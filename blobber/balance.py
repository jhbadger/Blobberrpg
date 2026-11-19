"""A balance check: a simple player plays the game's fights many times and
reports how quickly the party grows and how hard each fight is.

    ./yourgame --balance [runs]

The simulated player gives sensible orders (heal the hurt, cast its best
attack spell when the fight is worth it, otherwise hit what it can reach),
goes down into the level that suits the party's level, comes back to
town to rest, train and buy better armour and weapons when it is hurt or
out of spell points, and starts again from the last rest if it is wiped
out.  A game can tune the plan with BALANCE = {'levels': [(lid, min party
level), ...]}.
"""

import json
import random
import statistics

from .game import Game
from .combat import CombatMode, COMBAT_EFFECTS
from .rules import (Character, SPELLS, ITEMS, MONSTERS, SLOT_OF, can_use,
                    roll, dice_max, has_tag)


class _Silent:
    on = False
    available = False

    def play(self, name):
        pass


# ------------------------------------------------------------- the player

def orders(cm, g):
    """Orders for every able character, as a player might give them."""
    party = g.party
    live = cm.live_groups()
    foe_hp = sum(f.hp for _, grp in live for f in grp.alive)
    tough = sum(grp.m['level'] * len(grp.alive) for _, grp in live)
    out = {}
    for i, c in enumerate(party):
        if not c.able:
            continue
        spells = [s for s in c.spells() if SPELLS[s]['effect'] in
                  COMBAT_EFFECTS and SPELLS[s]['sp'] <= c.sp]
        by = {}
        for s in spells:
            by.setdefault(SPELLS[s]['effect'], []).append(s)
        hurt = [j for j, o in enumerate(party)
                if o.alive and o.hp < o.maxhp * 0.45]
        sick = [j for j, o in enumerate(party)
                if o.status in ('poisoned', 'paralyzed')]
        potions = [iid for iid in c.pack
                   if ITEMS[iid].get('use') == 'heal']
        if 'heal' in by and hurt:
            party_heal = [s for s in by['heal']
                          if SPELLS[s]['target'] == 'party']
            if party_heal and len(hurt) >= 2:
                out[i] = ('cast', party_heal[-1], None)
            else:
                one = [s for s in by['heal'] if SPELLS[s]['target'] == 'ally']
                low = min(hurt, key=lambda j: party[j].hp / party[j].maxhp)
                out[i] = ('cast', (one or by['heal'])[-1],
                          low if one else None)
            continue
        if 'cure' in by and sick:
            out[i] = ('cast', by['cure'][-1], sick[0])
            continue
        if c.hp < c.maxhp * 0.3 and potions:
            out[i] = ('use', potions[0], i)
            continue
        worth = foe_hp > 25 or tough >= 6
        if 'turn' in by and worth:
            und = [(gi, grp) for gi, grp in live
                   if has_tag(grp.m, SPELLS[by['turn'][-1]].get('tag',
                                                                 'undead'))
                   and grp.m['level'] < c.level and not grp.m.get('unique')]
            if und:
                out[i] = ('cast', by['turn'][-1], und[0][0])
                continue
        if cm.round_no == 1 and tough >= 12:
            if 'bless' in by and not cm.bless:
                out[i] = ('cast', by['bless'][-1], None)
                continue
            if 'ward' in by and not cm.ward:
                out[i] = ('cast', by['ward'][-1], None)
                continue
        attack_spells = by.get('damage', []) + by.get('smite', [])
        if attack_spells and worth and live:
            best = max(attack_spells, key=lambda s: (
                dice_max(SPELLS[s]['dice']) *
                (3 if SPELLS[s]['target'] in ('group', 'foes') else 1)))
            sp = SPELLS[best]
            target = max(live, key=lambda t: len(t[1].alive))[0] \
                if sp['target'] == 'group' else live[0][0]
            out[i] = ('cast', best, target)
            continue
        reach = cm.reach(g, c, i)
        weapon = c.item('weapon') or {}
        if reach and not (weapon.get('ammo') and not cm.has_ammo(g, weapon)):
            target = min(reach, key=lambda t: sum(f.hp for f in t[1].alive))
            out[i] = ('attack', target[0])
        else:
            out[i] = ('defend',)
    return out


def fight(g, groups, can_run=False):
    """Fight to the end; returns 'won' or 'lost' and the rounds taken."""
    cm = CombatMode(g, groups)
    cm.round_no = 0
    while True:
        cm.round_no += 1
        cm.orders = orders(cm, g)
        cm.simulate(g)
        if not any(grp.alive for grp in cm.groups):
            cm.shown = []
            cm.win(g)
            return 'won', cm.round_no
        if not any(c.able for c in g.party):
            return 'lost', cm.round_no
        if cm.round_no > 60:
            return 'lost', cm.round_no


# ---------------------------------------------------------------- the town

def town_prices(g):
    for L in g.levels.values():
        for sq in L.legend.values():
            if sq.get('shop') == 'inn':
                return sq.get('price', 4)
    return 4


def stock(g):
    for L in g.levels.values():
        for sq in L.legend.values():
            if sq.get('shop') == 'shop':
                return sq.get('stock') or [
                    k for k, it in ITEMS.items()
                    if it.get('price') and it['kind'] not in ('quest', 'key')]
    return []


def in_town(g, ledger):
    """Raise the dead, cure, rest, train and shop, as a player would."""
    st = g.st
    for c in g.party:
        if c.status == 'dead':
            cost = 100 * c.level
            if st.gold >= cost:
                st.gold -= cost
                c.status = 'ok'
                c.hp = c.maxhp
                ledger['raised'] += 1
            else:
                ledger['dead_left'] += 1
        if c.status in ('poisoned', 'paralyzed', 'stoned'):
            cost = 30 * c.level
            st.gold = max(0, st.gold - cost)
            c.status = 'ok'
    st.gold = max(0, st.gold - town_prices(g) * len(g.party))
    for c in g.party:
        if c.alive:
            c.hp, c.sp = c.maxhp, c.maxsp
        while c.alive and c.can_level():
            c.level_up(g.rng)
    shop(g)


def worth(it):
    if it['kind'] == 'weapon':
        return dice_max(it['dmg']) / 2 + it.get('hit', 0)
    return it.get('ac', 0)


def shop(g):
    """Spend on the biggest improvements first, keeping a little back."""
    st = g.st
    items = [i for i in stock(g) if ITEMS[i]['kind'] in SLOT_OF]
    while True:
        best = None
        for c in g.party:
            if not c.alive:
                continue
            for iid in items:
                it = ITEMS[iid]
                if it['price'] > st.gold - 20 or not can_use(c.cls, it):
                    continue
                slot = SLOT_OF[it['kind']]
                cur = c.item(slot)
                # back-rankers don't need melee weapons
                if slot == 'weapon' and not it.get('range') and \
                        g.party.index(c) >= 3:
                    continue
                if slot == 'weapon' and cur and cur.get('range') and \
                        not it.get('range'):
                    continue
                gain = worth(it) - (worth(cur) if cur else 0)
                if gain > 0.4:
                    value = gain / it['price']
                    if best is None or value > best[0]:
                        best = (value, c, iid, slot)
        if best is None:
            break
        _, c, iid, slot = best
        st.gold -= ITEMS[iid]['price']
        c.equip[slot] = iid
    for kind in {(c.item('weapon') or {}).get('ammo') for c in g.party} - {None}:
        packs = [i for i in stock(g) if ITEMS[i].get('ammo') == kind and
                 ITEMS[i]['kind'] == 'ammo']
        while packs and st.supplies.get(kind, 0) < 60 and \
                st.gold >= ITEMS[packs[0]]['price'] + 20:
            st.gold -= ITEMS[packs[0]]['price']
            st.supplies[kind] = st.supplies.get(kind, 0) + \
                ITEMS[packs[0]].get('amount', 1)
    potions = [i for i in stock(g) if ITEMS[i].get('use') == 'heal']
    if potions:
        for c in g.party[:3]:
            if not any(ITEMS[i].get('use') == 'heal' for i in c.pack) and \
                    st.gold >= ITEMS[potions[0]]['price'] + 60:
                st.gold -= ITEMS[potions[0]]['price']
                c.give(potions[0])


# ------------------------------------------------------------- campaign

def snapshot(g):
    return json.dumps(g.st.to_json())


def restore(g, snap):
    from .game import State
    g.st = State.from_json(json.loads(snap))


def plan(gdef, g):
    p = getattr(gdef, 'BALANCE', {}).get('levels')
    if p:
        return p
    out = []
    for lid, L in g.levels.items():
        if L.encounters and not L.outdoor:
            out.append((lid, 1 + 3 * (L.depth - 1 if L.depth else len(out))))
    return out


def encounter(g, L):
    total = sum(wt for wt, _ in L.encounters)
    r = g.rng.uniform(0, total)
    for wt, groups in L.encounters:
        r -= wt
        if r <= 0:
            break
    return [(k, g.rng.randint(lo, hi)) for (k, lo, hi) in groups]


def campaign(gdef, seed, max_fights=1500, target=None):
    g = Game(gdef, _Silent(), save_path='/dev/null')
    g.rng.seed(seed)
    g.new_game()
    stages = plan(gdef, g)
    ledger = dict(fights=0, wipes=0, raised=0, dead_left=0, expeditions=0)
    reached = {1: 0}
    snaps = {1: snapshot(g)}
    snap = snapshot(g)
    target = target or max(m for _, m in stages) + 3
    while ledger['fights'] < max_fights:
        avg = sum(c.level for c in g.party) / len(g.party)
        lid = stages[0][0]
        for l, need in stages:
            if avg >= need:
                lid = l
        L = g.levels[lid]
        g.st.level = lid
        g.st.x, g.st.y = next((x, y) for y in range(L.h) for x in range(L.w)
                              if not L.sq(x, y).get('solid') and
                              not L.sq(x, y).get('antimagic'))
        ledger['expeditions'] += 1
        while True:
            ledger['fights'] += 1
            res, _ = fight(g, encounter(g, L))
            if res == 'lost':
                ledger['wipes'] += 1
                restore(g, snap)
                break
            hp = sum(c.hp for c in g.party if c.alive) / \
                sum(c.maxhp for c in g.party)
            casters = [c for c in g.party if c.maxsp]
            sp = sum(c.sp for c in casters) / max(1, sum(c.maxsp
                                                          for c in casters))
            dead = any(not c.alive for c in g.party)
            if hp < 0.5 or (casters and sp < 0.25) or dead or \
                    any(c.can_level() for c in g.party):
                break
        in_town(g, ledger)
        snap = snapshot(g)
        lv = min(c.level for c in g.party)
        for k in range(2, lv + 1):
            reached.setdefault(k, ledger['fights'])
            snaps.setdefault(k, snap)
        if lv >= target:
            break
    return g, ledger, reached, snaps


def fixed_fights(gdef, g):
    out = []
    for lid, L in g.levels.items():
        for ch, sq in L.legend.items():
            if sq.get('fight'):
                out.append((lid, ch, sq.get('flag') or ch, sq['fight']))
    return out


def report(gdef, runs=20):
    print('Balance check for %s: %d campaigns\n' % (gdef.TITLE, runs))
    reached = {}
    ledgers = []
    parties = []
    for seed in range(runs):
        g, ledger, r, snaps = campaign(gdef, seed)
        ledgers.append(ledger)
        parties.append(snaps)
        for k, v in r.items():
            reached.setdefault(k, []).append(v)
    print('Random fights to reach each level (median, of runs that did):')
    for k in sorted(reached):
        if k > 1:
            print('  level %2d: %5d   (%d of %d runs)'
                  % (k, statistics.median(reached[k]), len(reached[k]), runs))
    for key in ('fights', 'wipes', 'raised', 'expeditions'):
        print('  %s per campaign: %.1f' % (
            key, statistics.mean(l[key] for l in ledgers)))
    print('\nFixed fights, fought by the campaigns\' parties as they reached '
          'each level\n(won %, median rounds, party hit points left %):')
    g0 = Game(gdef, _Silent(), save_path='/dev/null')
    g = g0
    for lid, ch, name, groups in fixed_fights(gdef, g0):
        row = []
        for level in (1, 2, 3, 4, 5, 6, 7, 8, 10):
            wins = 0
            rounds = []
            left = []
            for seed in range(runs):
                snap = parties[seed].get(level)
                if not snap:
                    continue
                restore(g, snap)
                g.rng.seed(seed * 31 + level)
                g.st.level = lid
                L = g.levels[lid]
                g.st.x, g.st.y = L.find(ch)
                res, n = fight(g, groups)
                if res == 'won':
                    wins += 1
                    rounds.append(n)
                    left.append(sum(c.hp for c in g.party) /
                                sum(c.maxhp for c in g.party))
            row.append((level, 100 * wins // runs,
                        statistics.median(rounds) if rounds else 0,
                        int(100 * statistics.mean(left)) if left else 0))
        desc = ', '.join('%d %s' % (n, MONSTERS[k]['name']) for k, n in groups)
        print('  %-8s %-10s %s' % (lid, name, desc))
        print('    ' + '  '.join('L%d:%3d%%/%g/%d%%' % r for r in row))

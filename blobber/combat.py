"""Fights.

Each round the party chooses to fight or run, then every character who
can act is given an order.  The round is worked out at once, everyone
acting in order of a dexterity roll, and then played back a line at a
time (the "beats"), with the roster's hit points following along.
"""

from .game import (Mode, Menu, VX, VY, VW, VH, TX, TY, TW, TH, INK, INK_DIM,
                   INK_HI, INK_TITLE)
from .gfx import rgb
from . import font
from . import art
from . import rules
from .rules import (Group, MONSTERS, SPELLS, ITEMS, roll, bonus, xp_for,
                    has_tag, death_text)
from .words import w

COMBAT_EFFECTS = ('damage', 'heal', 'cure', 'ward', 'bless', 'sleep', 'turn',
                  'smite')


def a_(name):
    return ('an ' if name[0].lower() in 'aeiou' else 'a ') + name


def called(m):
    """'a Skeleton', or 'the Ashen King' for a unique monster."""
    return 'the ' + m['name'] if m.get('unique') else a_(m['name'])


def cap(s):
    return s[0].upper() + s[1:]


class CombatMode(Mode):
    place = 'Combat!'

    def __init__(self, g, groups, on_win=None, can_run=True, fled_back=False):
        self.groups = []
        dist = 10
        for kind, n in groups:
            self.groups.append(Group(kind, n, dist, g.rng))
            if len(groups) > 1:
                dist = min(50, dist + 10 * g.rng.randint(0, 1) + 10)
        self.on_win = on_win
        self.can_run = can_run
        self.fled_back = fled_back
        self.ward = 0
        self.bless = 0
        self.orders = {}
        self.kills = []
        self.beats = []
        self.shown = []
        self.t = 0.0
        self.phase = 'menu'
        self.after = None
        self.gone = set()
        self.started = False

    # ------------------------------------------------------------- drawing

    def live_groups(self):
        return [(gi, grp) for gi, grp in enumerate(self.groups)
                if grp.alive and gi not in self.gone]

    def draw_view(self, g, s):
        g.draw_scene(s, dim=0.38)
        s.set_clip(VX, VY, VW, VH)
        live = self.live_groups()
        # the second and third groups stand smaller, behind the first
        for n, (gi, grp) in enumerate(live[1:3]):
            img = art.get(grp.m['art'])
            small = getattr(grp, '_small', None)
            if small is None:
                small = grp._small = img.scaled(img.w * 0.6, img.h * 0.6)\
                    .shaded(0.7)
            x = VX + (40 if n == 0 else VW - 40 - small.w)
            s.blit(small, x, VY + VH - small.h - 30)
        if live:
            gi, grp = live[0]
            img = art.get(grp.m['art'])
            s.blit(img, VX + VW // 2 - img.w // 2, VY + VH - img.h - 2)
        s.set_clip()
        y = VY + 24
        for gi, grp in live:
            s.text(VX + VW // 2, y, grp.label(), rgb('#ffe0a0'),
                   rgb('#000000'), align='center')
            y += font.LINE

    def groups_text(self):
        return '\n'.join('%s' % grp.label() for gi, grp in self.live_groups())

    def draw(self, g, s):
        self.draw_view(g, s)
        y = TY
        s.text(TX + TW // 2, y, 'Combat', INK_TITLE, align='center')
        y += font.LINE + 4
        lines = []
        for text in self.shown:
            lines.extend(font.wrap(text, TW))
        n = (TY + TH - y) // font.LINE
        show = lines[-n:]
        for i, line in enumerate(show):
            s.text(TX, y, line, INK if i >= len(show) - 4 else INK_DIM)
            y += font.LINE
        if self.phase in ('won', 'lost', 'fled', 'next'):
            s.text(TX + TW // 2, TY + TH - 10, '(press a key)', INK_DIM,
                   align='center')

    # ------------------------------------------------------------- flow

    def begin(self, g):
        names = ', '.join(grp.label() for grp in self.groups)
        g.say('You face %s!' % names, INK_HI)
        self.round_menu(g)

    def round_menu(self, g):
        self.phase = 'menu'
        self.orders = {}
        opts = [('Fight', 'fight'), ('Run', 'run', self.can_run)]
        g.push(Menu('Fight or run?', opts, lambda v: self.chose(g, v),
                    text='You face:\n' + self.groups_text(),
                    view=self.draw_view, place=self.place))

    def chose(self, g, v):
        if v == 'fight':
            self.order(g, 0)
        else:
            able = g.able()
            dx = sum(c.dx for c in able) / max(1, len(able))
            top = max(grp.m['level'] for gi, grp in self.live_groups())
            chance = max(10, min(90, 55 + (dx - 10) * 4 - top * 4))
            if g.rng.randint(1, 100) <= chance:
                self.start_play(g, [('The party flees!', None)], 'fled')
            else:
                beats = [('The party tries to flee, but the way is cut off!',
                          None)]
                beats += self.simulate(g, party_acts=False)
                self.start_play(g, beats, None)

    def next_able(self, g, i, step=1):
        while 0 <= i < len(g.party):
            if g.party[i].able:
                return i
            i += step
        return None

    def order(self, g, i):
        i = self.next_able(g, i)
        if i is None:
            self.start_play(g, self.simulate(g), None)
            return
        c = g.party[i]
        reach = self.reach(g, c, i)
        opts = []
        weapon = c.item('weapon') or {}
        if weapon.get('range') or i < 3:
            label = 'Attack'
            if weapon.get('ammo') and not self.has_ammo(g, weapon):
                label = 'Attack (no %s)' % weapon['ammo']
                reach = []
            opts.append((label, 'attack', bool(reach)))
        opts.append(('Defend', 'defend'))
        spells = [sid for sid in c.spells()
                  if SPELLS[sid]['effect'] in COMBAT_EFFECTS]
        if spells:
            opts.append((w('cast'), 'cast',
                         any(SPELLS[s]['sp'] <= c.sp for s in spells)))
        usable = [j for j, iid in enumerate(c.pack) if self.usable(iid)]
        if usable:
            opts.append(('Use an item', 'use'))

        def back():
            j = self.next_able(g, i - 1, -1)
            if j is None:
                self.round_menu(g)
            else:
                self.orders.pop(j, None)
                self.order(g, j)

        def pick(v):
            if v == 'attack':
                if len(reach) == 1:
                    self.orders[i] = ('attack', reach[0][0])
                    self.order(g, i + 1)
                else:
                    self.choose_group(g, i, reach, lambda gi: (
                        self.orders.__setitem__(i, ('attack', gi)),
                        self.order(g, i + 1)))
            elif v == 'defend':
                self.orders[i] = ('defend',)
                self.order(g, i + 1)
            elif v == 'cast':
                self.choose_spell(g, i, spells)
            elif v == 'use':
                self.choose_item(g, i, usable)

        g.push(Menu("%s's turn" % c.name, opts, pick,
                    text=self.groups_text(), on_cancel=back,
                    view=self.draw_view, place=self.place, roster_sel=i))

    def reach(self, g, c, i):
        """The groups character i could attack: within 10' for the front
        rank, or within the range of a ranged weapon from any rank."""
        weapon = c.item('weapon') or {}
        rng_ = weapon.get('range', 0)
        return [(gi, grp) for gi, grp in self.live_groups()
                if grp.dist <= max(rng_, 10 if i < 3 else 0)]

    def has_ammo(self, g, weapon):
        return g.st.supplies.get(weapon['ammo'], 0) > 0

    def usable(self, iid):
        it = ITEMS.get(iid, {})
        if it.get('use') in ('heal', 'cure'):
            return True
        if it.get('use') == 'spell':
            return SPELLS[it['spell']]['effect'] in COMBAT_EFFECTS
        return False

    def choose_group(self, g, i, groups, then, title='Which foes?'):
        g.push(Menu(title, [(grp.label(), gi) for gi, grp in groups], then,
                    on_cancel=lambda: self.order(g, i), view=self.draw_view,
                    place=self.place, roster_sel=i))

    def choose_ally(self, g, i, then, title='On whom?'):
        g.push(Menu(title, [(c.name, j, c.alive) for j, c in
                            enumerate(g.party)], then,
                    on_cancel=lambda: self.order(g, i), view=self.draw_view,
                    place=self.place, roster_sel=i))

    def choose_spell(self, g, i, spells):
        c = g.party[i]
        opts = [('%s\t%d %s' % (SPELLS[s]['name'], SPELLS[s]['sp'],
                                   w('sp')), s,
                 SPELLS[s]['sp'] <= c.sp) for s in spells]

        def pick(sid):
            self.target_for(g, i, SPELLS[sid]['target'],
                            lambda t: (self.orders.__setitem__(
                                i, ('cast', sid, t)), self.order(g, i + 1)))
        g.push(Menu('%s %s' % (c.name, w('casts')), opts, pick,
                    text='%d of %d %s.' % (c.sp, c.maxsp, w('points')),
                    on_cancel=lambda: self.order(g, i), view=self.draw_view,
                    place=self.place, roster_sel=i))

    def target_for(self, g, i, target, then):
        live = self.live_groups()
        if target in ('foe', 'group'):
            if len(live) == 1:
                then(live[0][0])
            else:
                self.choose_group(g, i, live, then)
        elif target == 'ally':
            self.choose_ally(g, i, then)
        else:
            then(None)

    def choose_item(self, g, i, usable):
        c = g.party[i]

        def pick(j):
            it = ITEMS[c.pack[j]]
            if it.get('use') == 'spell':
                self.target_for(g, i, SPELLS[it['spell']]['target'],
                                lambda t: (self.orders.__setitem__(
                                    i, ('use', c.pack[j], t)),
                                    self.order(g, i + 1)))
            else:
                self.orders[i] = ('use', c.pack[j], i)
                self.order(g, i + 1)
        g.push(Menu('%s uses' % c.name,
                    [(ITEMS[c.pack[j]]['name'], j) for j in usable], pick,
                    on_cancel=lambda: self.order(g, i), view=self.draw_view,
                    place=self.place, roster_sel=i))

    # ---------------------------------------------------------- the round

    def snap(self, g, i):
        c = g.party[i]
        return ('snap', i, c.hp, c.status, c.sp)

    def simulate(self, g, party_acts=True):
        rng = g.rng
        beats = []
        acts = []
        self.pre_round = {i: (c.hp, c.status, c.sp)
                          for i, c in enumerate(g.party)}
        if party_acts:
            for i, c in enumerate(g.party):
                if c.able and i in self.orders:
                    acts.append((c.dx + rng.randint(1, 10) + c.level // 2,
                                 0, i, None))
        for gi, grp in enumerate(self.groups):
            for f in grp.alive:
                for _ in range(grp.m.get('acts', 1)):
                    acts.append((grp.m['level'] + rng.randint(1, 10) + 2, 1,
                                 gi, f))
        acts.sort(key=lambda a: -a[0])
        defending = {i for i, o in self.orders.items() if o[0] == 'defend'}
        for _, who, a, b in acts:
            if who == 0:
                self.pc_act(g, a, beats, defending)
            else:
                self.foe_act(g, a, b, beats, defending)
            if not any(grp.alive for grp in self.groups):
                break
            if not any(c.able for c in g.party):
                break
        for grp in self.groups:
            if grp.alive:
                for f in grp.alive:
                    if f.asleep:
                        f.asleep -= 1
                if grp.dist > 10 and not grp.m.get('range'):
                    grp.dist -= 10
        return beats

    def pc_act(self, g, i, beats, defending):
        c = g.party[i]
        rng = g.rng
        if not c.able:
            return
        o = self.orders[i]
        if o[0] == 'defend':
            beats.append(('%s stands on guard.' % c.name, None))
        elif o[0] == 'attack':
            weapon = c.item('weapon') or {}
            ranged = bool(weapon.get('range'))
            reach = dict(self.reach(g, c, i))
            grp = self.groups[o[1]] if o[1] in reach else None
            if grp is None or not grp.alive:
                grp = next(iter(reach.values()), None)
            if grp is None:
                beats.append(('%s has no foe within reach.' % c.name, None))
                return
            gi = self.groups.index(grp)
            verb = weapon.get('verb', 'hits')
            if weapon.get('area'):
                self.area_attack(g, c, weapon, grp, gi, beats)
                return
            for n in range(c.attacks()):
                targets = grp.alive
                if not targets:
                    break
                if weapon.get('ammo'):
                    if not self.has_ammo(g, weapon):
                        beats.append((w('no_ammo', c.name, weapon['ammo']),
                                      None))
                        break
                    g.st.supplies[weapon['ammo']] -= 1
                f = rng.choice(targets)
                r = rng.randint(1, 20)
                th = c.to_hit() + self.bless + (4 if f.asleep else 0)
                if ranged:
                    th += bonus(c.dx) - bonus(c.st)
                if r == 20 or (r != 1 and r + th + grp.m['ac'] >= 20):
                    dmg = max(1, roll(c.damage_dice(), rng) +
                              (0 if ranged else bonus(c.st)))
                    if r == 20:
                        dmg *= 2
                    f.hp -= dmg
                    f.asleep = 0
                    text = '%s %s %s for %d damage%s' % (
                        c.name, verb, called(grp.m), dmg,
                        ', a critical hit!' if r == 20 else '.')
                    beats.append((text, ('foe', gi)))
                    if f.hp <= 0:
                        self.kill(grp, gi, f, beats)
                else:
                    beats.append((w('shot_miss' if ranged else 'melee_miss',
                                    c.name, called(grp.m)), ('miss',)))
        elif o[0] == 'cast':
            sp = SPELLS[o[1]]
            if c.sp < sp['sp']:
                beats.append((w('too_few', c.name), None))
                return
            c.sp -= sp['sp']
            beats.append(('%s %s %s!' % (c.name, w('casts'), sp['name']),
                          ('sound', 'spell')))
            beats.append(('', self.snap(g, i)))
            if g.antimagic():
                beats.append((w('fizzle_fight'), None))
                return
            self.apply_spell(g, c, sp, o[2], beats, c.level)
        elif o[0] == 'use':
            iid = o[1]
            if iid not in c.pack:
                beats.append(("%s can't find it." % c.name, None))
                return
            c.pack.remove(iid)
            it = ITEMS[iid]
            if it.get('use') == 'heal':
                n = roll(it.get('amount', '2d8'), rng)
                c.hp = min(c.maxhp, c.hp + n)
                beats.append(('%s %s the %s and is healed.' % (
                    c.name, it.get('verb', 'uses'), it['name']),
                    self.snap(g, i)))
            elif it.get('use') == 'cure':
                if c.status == 'poisoned':
                    c.status = 'ok'
                beats.append(('%s %s the %s.' % (
                    c.name, it.get('verb', 'uses'), it['name']),
                    self.snap(g, i)))
            elif it.get('use') == 'spell':
                sp = SPELLS[it['spell']]
                beats.append(('%s %s the %s!' % (
                    c.name, it.get('verb', 'uses'), it['name']),
                              ('sound', 'spell')))
                self.apply_spell(g, c, sp, o[2], beats, 5)

    def area_attack(self, g, c, weapon, grp, gi, beats):
        """A weapon with 'area' (a flamer, a blast) hits every foe in the
        group with one shot."""
        rng = g.rng
        if weapon.get('ammo'):
            if not self.has_ammo(g, weapon):
                beats.append((w('no_ammo', c.name, weapon['ammo']), None))
                return
            g.st.supplies[weapon['ammo']] -= 1
        beats.append(('%s %s the %s!' % (c.name, weapon.get('verb', 'hits'),
                                          grp.m['plural']), ('sound', 'trap')))
        for f in list(grp.alive):
            r = rng.randint(1, 20)
            th = c.to_hit() + self.bless + bonus(c.dx) - bonus(c.st)
            if r == 20 or (r != 1 and r + th + grp.m['ac'] >= 20):
                dmg = max(1, roll(c.damage_dice(), rng))
                f.hp -= dmg
                f.asleep = 0
                beats.append(('%s takes %d damage.' % (cap(called(grp.m)), dmg),
                              ('foe', gi)))
                if f.hp <= 0:
                    self.kill(grp, gi, f, beats)
            else:
                beats.append(('%s is missed.' % cap(called(grp.m)), ('miss',)))

    def kill(self, grp, gi, f, beats):
        self.kills.append(grp.kind)
        beats.append((death_text(grp.m), None))
        if not grp.alive:
            beats.append(('', ('gone', gi)))

    def apply_spell(self, g, c, sp, tgt, beats, level):
        rng = g.rng
        e = sp['effect']
        if e in ('damage', 'smite', 'sleep', 'turn'):
            if sp['target'] == 'foes':
                groups = [(gi, grp) for gi, grp in enumerate(self.groups)
                          if grp.alive and grp.dist <= 30]
            else:
                grp = self.groups[tgt] if tgt is not None else None
                if grp is None or not grp.alive:
                    live = self.live_groups()
                    if not live:
                        return
                    tgt, grp = live[0]
                groups = [(tgt, grp)]
            for gi, grp in groups:
                name = grp.m['name']
                if e == 'sleep':
                    n = 0
                    for f in grp.alive:
                        if not grp.m.get('unique') and \
                                not any(has_tag(grp.m, t)
                                        for t in sp.get('immune', ())) and \
                                grp.m['level'] <= level + 2 and \
                                rng.random() < 0.75:
                            f.asleep = rng.randint(2, 4)
                            n += 1
                    beats.append(('%d of the %s fall asleep.' % (
                        n, grp.m['plural']) if n else 'The %s shrug it off.'
                        % grp.m['plural'], None))
                    continue
                if e == 'turn':
                    if not has_tag(grp.m, sp.get('tag', 'undead')):
                        beats.append((w('turn_wrong', grp.m['plural']), None))
                        continue
                    n = 0
                    # it takes a caster above the monster's level, and
                    # never works on a unique monster
                    edge = level - grp.m['level']
                    chance = 0 if grp.m.get('unique') or edge < 1 else \
                        min(0.9, 0.4 + 0.1 * edge)
                    for f in grp.alive:
                        if rng.random() < chance:
                            f.hp = 0
                            self.kills.append(grp.kind)
                            n += 1
                    if n:
                        beats.append((w('turned',
                            n, grp.m['name'] if n == 1 else grp.m['plural']),
                            ('foe', gi)))
                        if not grp.alive:
                            beats.append(('', ('gone', gi)))
                    else:
                        beats.append((w('turn_fail', grp.m['plural']), None))
                    continue
                targets = grp.alive if sp['target'] in ('group', 'foes') \
                    else [rng.choice(grp.alive)]
                for f in targets:
                    dmg = roll(sp['dice'], rng) + level * sp.get('per', 0)
                    if sp.get('bane') and has_tag(grp.m, sp['bane']):
                        dmg *= 2
                    f.hp -= dmg
                    f.asleep = 0
                    beats.append(('%s takes %d damage.' % (
                        'The ' + name, dmg), ('foe', gi)))
                    if f.hp <= 0:
                        self.kill(grp, gi, f, beats)
        elif e == 'heal':
            whom = [tgt] if tgt is not None else range(len(g.party))
            for j in whom:
                t = g.party[j]
                if t.alive:
                    n = roll(sp['dice'], rng) + level * sp.get('per', 0)
                    t.hp = min(t.maxhp, t.hp + n)
                    beats.append(('%s is healed.' % t.name, self.snap(g, j)))
        elif e == 'cure':
            t = g.party[tgt]
            if t.status in ('poisoned', 'paralyzed', 'asleep'):
                t.status = 'ok'
            beats.append((w('is_cured', t.name), self.snap(g, tgt)))
        elif e == 'ward':
            self.ward = max(self.ward, sp.get('amount', 2))
            beats.append(('A shimmering ward surrounds the party.', None))
        elif e == 'bless':
            self.bless = max(self.bless, sp.get('amount', 2))
            beats.append(('The party feels blessed.', None))

    def hurt(self, g, i, dmg, beats, text):
        c = g.party[i]
        c.hp -= dmg
        if c.hp <= 0:
            c.hp = 0
            c.status = 'dead'
            beats.append((text, ('hurt', i, 0, 'dead', c.sp)))
            beats.append(('%s falls!' % c.name, ('sound', 'die')))
            return True
        beats.append((text, ('hurt', i, c.hp, c.status, c.sp)))
        return False

    def foe_act(self, g, gi, f, beats, defending):
        grp = self.groups[gi]
        m = grp.m
        rng = g.rng
        if f.hp <= 0 or f.asleep:
            return
        living = [i for i, c in enumerate(g.party) if c.alive]
        if not living:
            return
        name = m['name']
        for spc in m.get('special', []):
            parts = spc.split(':')
            if parts[0] == 'breath' and rng.randint(1, 100) <= int(parts[2]):
                beats.append(('The %s %s' % (name, m.get('breath_msg',
                                                         w('breath'))),
                              ('sound', 'trap')))
                for i in living:
                    c = g.party[i]
                    dmg = roll(parts[1], rng)
                    if rng.randint(1, 20) <= c.dx:
                        dmg //= 2
                    self.hurt(g, i, dmg, beats, '%s is burned for %d.'
                              % (c.name, dmg))
                return
            if parts[0] == 'cast' and rng.randint(1, 100) <= int(parts[2]):
                sp = SPELLS[parts[1]]
                i = rng.choice(living)
                c = g.party[i]
                dmg = roll(sp.get('dice', '2d6'), rng) + m['level']
                beats.append(('The %s %s %s!' % (name, w('casts'),
                                                  sp['name']),
                              ('sound', 'spell')))
                self.hurt(g, i, dmg, beats, '%s takes %d damage.'
                          % (c.name, dmg))
                return
        if grp.dist > 10 and not m.get('range'):
            return
        front = [i for i in living if i < 3]
        targets = front or living
        shooting = bool(m.get('range')) and grp.dist > 10
        if shooting:
            targets = living
        for h in range(m.get('hits', 1)):
            targets = [i for i in targets if g.party[i].alive]
            if not targets:
                return
            i = rng.choice(targets)
            c = g.party[i]
            ac = c.ac(self.ward + (2 if i in defending else 0))
            r = rng.randint(1, 20)
            if r == 20 or (r != 1 and r + m['level'] + 1 + ac >= 20):
                dmg = max(1, roll(m['dmg'], rng))
                verb = m.get('shoots', w('shoots')) if shooting else 'hits'
                died = self.hurt(g, i, dmg, beats, '%s %s %s for %d damage.'
                                 % (cap(called(m)), verb, c.name, dmg))
                if died:
                    continue
                for spc in m.get('special', []):
                    parts = spc.split(':')
                    if parts[0] in ('poison', 'paralyze', 'drain') and \
                            rng.randint(1, 100) <= int(parts[1]):
                        if parts[0] == 'poison' and c.status == 'ok':
                            c.status = 'poisoned'
                            beats.append((w('is_poisoned', c.name),
                                          self.snap(g, i)))
                        elif parts[0] == 'paralyze' and c.status in (
                                'ok', 'poisoned'):
                            if rng.randint(1, 20) > c.lk:
                                c.status = 'paralyzed'
                                beats.append((w('is_paralyzed', c.name),
                                              self.snap(g, i)))
                        elif parts[0] == 'drain' and c.level > 1:
                            c.level -= 1
                            loss = max(1, c.maxhp // (c.level + 1))
                            c.maxhp = max(1, c.maxhp - loss)
                            c.hp = min(c.hp, c.maxhp)
                            c.xp = xp_for(c.level)
                            c.maxsp = c.sp_for_level(c.level)
                            c.sp = min(c.sp, c.maxsp)
                            beats.append((w('drained', c.name),
                                          self.snap(g, i)))
            else:
                verb = m.get('shoots', w('shoots')) if shooting else 'attacks'
                beats.append(('%s %s %s but misses.' % (
                    cap(called(m)), verb, c.name), ('miss',)))

    # ---------------------------------------------------------- playback

    def start_play(self, g, beats, outcome):
        self.phase = 'play'
        self.beats = list(beats)
        self.t = 0.0
        self.outcome = outcome
        # the roster shows what it showed before the round until each
        # beat catches it up
        pre = getattr(self, 'pre_round', None) or {}
        g.roster_override = {i: pre.get(i, (c.hp, c.status, c.sp))
                             for i, c in enumerate(g.party)}
        self.pre_round = None
        self.next_beat(g)

    def next_beat(self, g):
        while self.beats:
            text, fx = self.beats.pop(0)
            if fx:
                kind = fx[0]
                if kind == 'foe':
                    g.view_flash = 0.12
                    g.sound.play('hit')
                elif kind == 'miss':
                    g.sound.play('miss')
                elif kind == 'hurt':
                    g.roster_override[fx[1]] = fx[2:]
                    g.hurt_flash(fx[1])
                    g.sound.play('hurt')
                elif kind == 'snap':
                    g.roster_override[fx[1]] = fx[2:]
                elif kind == 'gone':
                    self.gone.add(fx[1])
                elif kind == 'sound':
                    g.sound.play(fx[1])
            if text:
                self.shown.append(text)
                g.dirty = True
                return
        self.end_round(g)

    def update(self, g, dt):
        if self.phase != 'play':
            return
        self.t += dt
        if self.t >= 0.75 * g.speed:
            self.t = 0.0
            self.next_beat(g)

    def end_round(self, g):
        g.roster_override = None
        if self.outcome == 'fled':
            self.phase = 'fled'
            return
        if not any(grp.alive for grp in self.groups):
            self.win(g)
            return
        if not any(c.able for c in g.party):
            self.shown.append('Your party has been defeated...')
            self.phase = 'lost'
            g.sound.play('die')
            return
        self.phase = 'next'
        self.shown.append('')

    def win(self, g):
        rng = g.rng
        xp = sum(MONSTERS[k]['xp'] for k in self.kills)
        gold = sum(roll(MONSTERS[k].get('gold', '0'), rng)
                   for k in self.kills)
        alive = [c for c in g.party if c.alive]
        share = xp // max(1, len(alive))
        self.shown.append('Victory! The foes are vanquished.')
        before = {id(c): c.can_level() for c in alive}
        for c in alive:
            c.xp += share
            if c.status == 'asleep':
                c.status = 'ok'
        self.shown.append('Each survivor earns %d experience.' % share)
        if gold:
            g.st.gold += gold
            self.shown.append(w('found_money', gold))
        if rules.LOOT and rng.random() < 0.12 + 0.02 * len(self.kills):
            iid = rng.choice(rules.LOOT)
            who = g.give_party(iid)
            if who:
                self.shown.append('%s finds %s.' % (who.name,
                                                    a_(ITEMS[iid]['name'])))
        for c in alive:
            if c.can_level() and not before[id(c)]:
                self.shown.append(w('can_train', c.name))
        g.say('Victory: %d experience each, %d %s.' % (share, gold,
                                                       w('money')))
        g.sound.play('coin')
        self.phase = 'won'

    def key(self, g, k):
        if self.phase == 'play':
            self.t = 0.0
            self.next_beat(g)
        elif self.phase == 'next':
            self.round_menu(g)
        elif self.phase == 'won':
            g.pop(self)
            if self.on_win:
                self.on_win()
        elif self.phase == 'fled':
            g.pop(self)
            g.say('You escape.')
            if self.fled_back and g.st.prev:
                g.st.x, g.st.y = g.st.prev
                g.mark_seen()
        elif self.phase == 'lost':
            g.pop(self)
            g.check_wipe()

    def click(self, g, x, y):
        self.key(g, 'enter')

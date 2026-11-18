"""The places in town you walk into: the Guild (the party and new
adventurers), shops, the temple, the inn and the sage.

A shop square's legend entry says which kind it is ('shop': 'guild') and
may give 'name', 'art' (the keeper's picture), 'backdrop' (a texture for
the walls), 'greeting', 'stock' (item ids, for a shop) and 'prices' (for
the temple and inn).
"""

from .game import (INK_DIM, INK_HI, TextInput)
from .modes import picture_view
from . import rules
from .rules import (Character, ITEMS, RACES, CLASSES, STATS, STAT_NAMES,
                    can_use, xp_for, PACK, MAX_LEVEL)


def enter_shop(g, sq):
    kind = sq['shop']
    hook = g.hooks.get('shop:' + kind)
    if hook and hook(g, sq):
        return
    g.sound.play('door')
    {'guild': guild, 'shop': shop, 'temple': temple, 'inn': inn,
     'sage': sage}[kind](g, sq)


def view_for(sq, default_art, backdrop='cellar'):
    return picture_view(sq.get('art', default_art),
                        texture=sq.get('backdrop', backdrop))


# ------------------------------------------------------------------ guild

def guild(g, sq, sel=0):
    view = view_for(sq, 'guildmaster', 'cata')
    name = sq.get('name', "Adventurers' Guild")
    trainable = [c for c in g.party if c.alive and c.can_level()]
    opts = [('Train for new levels', 'train', bool(trainable)),
            ('Add a member to the party', 'add',
             bool(g.st.roster) and len(g.party) < 6),
            ('Leave a member at the Guild', 'remove', len(g.party) > 1),
            ('Create a new adventurer', 'create'),
            ('Change the marching order', 'order', len(g.party) > 1),
            ('Retire an adventurer', 'retire', bool(g.st.roster)),
            ('Leave', 'leave')]
    text = sq.get('greeting', 'The Guildmaster looks up from his ledgers. '
                              '"Well met. What do you need?"')

    def back():
        guild(g, sq)

    def pick(v):
        if v == 'leave':
            return
        if v == 'train':
            lines = []
            for c in g.party:
                while c.alive and c.can_level():
                    notes = c.level_up(g.rng)
                    lines.append('%s reaches level %d: %s.'
                                 % (c.name, c.level, ', '.join(notes)))
            g.sound.play('level')
            for l in lines:
                g.say(l)
            g.save()
            g.tell('\n\n'.join(lines), back, title='Training', view=view,
                   place=name)
        elif v == 'add':
            g.ask('Who joins?', [('%s, level %d %s' % (c.name, c.level, c.cls),
                                  i) for i, c in enumerate(g.st.roster)],
                  lambda i: (g.party.append(g.st.roster.pop(i)), back()),
                  on_cancel=back, view=view, place=name)
        elif v == 'remove':
            g.ask('Who stays behind?', [(c.name, i)
                                        for i, c in enumerate(g.party)],
                  lambda i: (g.st.roster.append(g.party.pop(i)), back()),
                  on_cancel=back, view=view, place=name)
        elif v == 'retire':
            def retire(i):
                c = g.st.roster[i]
                g.yesno('Retire %s for good? Everything %s carries goes too.'
                        % (c.name, c.name),
                        lambda: (g.st.roster.pop(i), back()), back)
            g.ask('Who retires?', [(c.name, i)
                                   for i, c in enumerate(g.st.roster)],
                  retire, on_cancel=back, view=view, place=name)
        elif v == 'order':
            reorder(g, back, view, name)
        elif v == 'create':
            create(g, back, view, name)
    g.ask(name, opts, pick, text, on_cancel=lambda: None, view=view,
          place=name)


def reorder(g, back, view, name):
    new = []
    left = list(range(len(g.party)))

    def step():
        if len(left) == 1:
            new.append(left.pop())
        if not left:
            g.st.party[:] = [g.party[i] for i in new]
            g.say('The party falls in: %s.' % ', '.join(c.name for c in g.party))
            back()
            return
        g.ask('Who goes %s?' % ['first', 'second', 'third', 'fourth', 'fifth',
                                'sixth'][len(new)],
              [(g.party[i].name, i) for i in left],
              lambda i: (new.append(i), left.remove(i), step()),
              'The first three fight hand to hand and take the blows.',
              on_cancel=back, view=view, place=name)
    step()


def create(g, back, view, name):
    def got_name(nm):
        races = list(RACES)
        g.ask('Choose a race', races, lambda r: got_race(nm, r),
              '\n'.join('%s: %s' % (r, RACES[r]['text']) for r in races),
              on_cancel=back, view=view, place=name)

    def got_race(nm, race):
        classes = list(CLASSES)
        g.ask('Choose a class', classes,
              lambda k: rolled(Character.roll_new(nm, race, k, g.rng)),
              '\n'.join('%s: %s' % (k, CLASSES[k]['text']) for k in classes),
              on_cancel=back, view=view, place=name)

    def rolled(c):
        stats = '   '.join('%s %d' % (s.upper(), getattr(c, s)) for s in STATS)
        text = ('%s the %s %s\n\n%s\n\nHit points %d   Spell points %d'
                % (c.name, c.race, c.cls, stats, c.maxhp, c.maxsp))

        def pick(v):
            if v == 'keep':
                for iid in g.kits.get(c.cls, []):
                    c.give(iid)
                    c.equip_item(len(c.pack) - 1)
                if len(g.party) < 6:
                    g.party.append(c)
                    where = 'joins the party'
                else:
                    g.st.roster.append(c)
                    where = 'waits at the Guild'
                g.sound.play('level')
                g.say('%s %s.' % (c.name, where))
                back()
            elif v == 'reroll':
                c.reroll(g.rng)
                rolled(c)
            else:
                back()
        g.ask('A new adventurer', [('Keep', 'keep'), ('Roll again', 'reroll'),
                                   ('Forget it', 'forget')], pick, text,
              on_cancel=back, view=view, place=name)

    g.push(TextInput('A new adventurer', 'What is the name of this new '
                     'adventurer?', got_name, maxlen=14, on_cancel=back,
                     view=view))


# ------------------------------------------------------------------- shop

def shop(g, sq):
    view = view_for(sq, 'smith', 'cellar')
    name = sq.get('name', 'The Armoury')
    stock = sq.get('stock', ['dagger', 'staff', 'club', 'mace', 'shortsword',
                             'longsword', 'warhammer', 'battleaxe', 'robes',
                             'leather', 'chain', 'plate', 'buckler', 'kite',
                             'cap', 'helm', 'gauntlets', 'potion', 'antidote',
                             'torch'])

    def back():
        shop(g, sq)

    def pick(v):
        if v == 'buy':
            buy(g, sq, stock, back, view, name)
        elif v == 'sell':
            sell(g, back, view, name)

    g.ask(name, [('Buy', 'buy'), ('Sell', 'sell'), ('Leave', 'leave')], pick,
          sq.get('greeting', 'The smith wipes soot from her hands. "Steel, '
                             'leather, a torch? I have it all."')
          + '\n\nYou have %d gold.' % g.st.gold,
          on_cancel=lambda: None, view=view, place=name)


def buy(g, sq, stock, back, view, name, sel=0):
    opts = [('%-18s %4d' % (ITEMS[i]['name'], ITEMS[i]['price']), i,
             ITEMS[i]['price'] <= g.st.gold) for i in stock]

    def pick(iid):
        it = ITEMS[iid]

        def who(j):
            c = g.party[j]
            if len(c.pack) >= PACK:
                g.tell("%s's pack is full." % c.name,
                       lambda: buy(g, sq, stock, back, view, name, sel))
                return
            g.st.gold -= it['price']
            c.give(iid)
            msg = '%s buys the %s.' % (c.name, it['name'])
            from .rules import SLOT_OF
            slot = SLOT_OF.get(it['kind'])
            if slot and can_use(c.cls, it) and not c.equip.get(slot):
                c.equip_item(len(c.pack) - 1)
                msg = '%s buys the %s and puts it on.' % (c.name, it['name']) \
                    if slot != 'weapon' else \
                    '%s buys the %s and takes it in hand.' % (c.name,
                                                             it['name'])
            g.sound.play('coin')
            g.say(msg)
            buy(g, sq, stock, back, view, name, stock.index(iid))

        mark = []
        for c in g.party:
            ok = can_use(c.cls, it) or it['kind'] not in (
                'weapon', 'armor', 'shield', 'helm', 'gloves', 'ring')
            mark.append(('%s%s' % (c.name, '' if ok else ' (can\'t use)'),
                         g.party.index(c), True))
        from .modes import describe
        g.ask('Who gets the %s?' % it['name'], mark, who,
              describe(it) + '\n\nYou have %d gold.' % g.st.gold,
              on_cancel=lambda: buy(g, sq, stock, back, view, name, sel),
              view=view, place=name)

    g.ask('Buy (you have %d gold)' % g.st.gold, opts, pick,
          on_cancel=back, view=view, place=name, sel=sel)


def sell(g, back, view, name):
    def pick_char(j):
        c = g.party[j]
        opts = []
        for k, iid in enumerate(c.pack):
            it = ITEMS[iid]
            price = it.get('price', 0) // 2
            opts.append(('%-18s %4d' % (it['name'], price), k,
                         price > 0 and it['kind'] not in ('quest', 'key')))
        if not opts:
            g.tell('%s has nothing in the pack to sell.' % c.name, back)
            return

        def sold(k):
            iid = c.pack.pop(k)
            price = ITEMS[iid].get('price', 0) // 2
            g.st.gold += price
            g.sound.play('coin')
            g.say('%s sells the %s for %d gold.' % (c.name, ITEMS[iid]['name'],
                                                    price))
            pick_char(j)
        g.ask('%s sells' % c.name, opts, sold, 'Equipment must be taken '
              'off before it can be sold (see the character sheet).',
              on_cancel=back, view=view, place=name)

    g.ask('Who sells?', [(c.name, j) for j, c in enumerate(g.party)],
          pick_char, on_cancel=back, view=view, place=name)


# ----------------------------------------------------------------- temple

def temple(g, sq):
    view = view_for(sq, 'priestess', 'cata')
    name = sq.get('name', 'The Temple')
    hurt = sum(c.maxhp - c.hp for c in g.party if c.alive)
    sick = [c for c in g.party if c.status in ('poisoned', 'paralyzed',
                                               'stoned')]
    dead = [c for c in g.party if c.status == 'dead']
    heal_cost = hurt
    opts = [('Heal wounds (%d gold)' % heal_cost, 'heal',
             hurt > 0 and g.st.gold >= heal_cost)]
    for c in sick:
        cost = 30 * c.level
        opts.append(('Cure %s (%d gold)' % (c.name, cost), ('cure', c),
                     g.st.gold >= cost))
    for c in dead:
        cost = 100 * c.level
        opts.append(('Raise %s (%d gold)' % (c.name, cost), ('raise', c),
                     g.st.gold >= cost))
    opts.append(('Leave', 'leave'))

    def back():
        temple(g, sq)

    def pick(v):
        if v == 'leave':
            return
        if v == 'heal':
            g.st.gold -= heal_cost
            for c in g.party:
                if c.alive:
                    c.hp = c.maxhp
            g.sound.play('heal')
            g.say('The priestess lays hands on your wounds.')
            back()
        elif v[0] == 'cure':
            c = v[1]
            g.st.gold -= 30 * c.level
            c.status = 'ok'
            c.hp = max(1, c.hp)
            g.sound.play('heal')
            g.say('%s is cured.' % c.name)
            back()
        elif v[0] == 'raise':
            c = v[1]
            g.st.gold -= 100 * c.level
            c.status = 'ok'
            c.hp = c.maxhp
            g.sound.play('magic')
            g.say('%s lives again!' % c.name, INK_HI)
            back()

    g.ask(name, opts, pick, sq.get('greeting', 'Candles gutter before the '
                                   'altar. "Peace be with you. How may the '
                                   'temple help?"') +
          '\n\nYou have %d gold.' % g.st.gold,
          on_cancel=lambda: None, view=view, place=name)


# -------------------------------------------------------------------- inn

def inn(g, sq):
    view = view_for(sq, 'innkeeper', 'cellar')
    name = sq.get('name', 'The Inn')
    cost = sq.get('price', 4) * len(g.party)

    def pick(v):
        if v == 'rest':
            g.st.gold -= cost
            for c in g.party:
                if c.alive:
                    c.hp = c.maxhp
                    c.sp = c.maxsp
                    if c.status == 'asleep':
                        c.status = 'ok'
            g.save()
            g.sound.play('heal')
            g.say('You sleep soundly. Hit points and spell points are '
                  'restored, and the game is saved.')
            ready = [c.name for c in g.party if c.alive and c.can_level()]
            text = 'Morning comes. You wake rested and whole.\n\n(The game ' \
                   'has been saved.)'
            if ready:
                text += '\n\n%s could train at the Guild.' % ', '.join(ready)
            g.tell(text, title=name, view=view, place=name)
        elif v == 'news':
            news = sq.get('news', ['"Nothing new under the sun."'])
            g.tell(g.rng.choice(news), lambda: inn(g, sq), view=view,
                   place=name)

    g.ask(name, [('Rest the night (%d gold)' % cost, 'rest',
                  g.st.gold >= cost),
                 ('Ask for news', 'news', bool(sq.get('news'))),
                 ('Leave', 'leave')], pick,
          sq.get('greeting', 'The innkeeper polishes a tankard. "Beds are '
                             'clean, the stew is hot."') +
          '\n\nYou have %d gold.' % g.st.gold,
          on_cancel=lambda: None, view=view, place=name)


# ------------------------------------------------------------------- sage

def sage(g, sq):
    view = view_for(sq, 'sage', 'cata')
    name = sq.get('name', "The Sage's Tower")
    price = sq.get('price', 20)
    hints = getattr(g.d, 'HINTS', [])

    def pick(v):
        if v == 'ask':
            g.st.gold -= price
            text = None
            for flag, hint in hints:
                if not flag or not g.flag(flag):
                    text = hint
                    break
            g.tell(text or '"You know all I could tell you."',
                   lambda: sage(g, sq), view=view, place=name)
        elif v == 'lore':
            g.tell(sq.get('lore', '"Knowledge is not free, friend."'),
                   lambda: sage(g, sq), view=view, place=name)

    g.ask(name, [('Ask for counsel (%d gold)' % price, 'ask',
                  g.st.gold >= price),
                 ('Ask about the crypt', 'lore', bool(sq.get('lore'))),
                 ('Leave', 'leave')], pick,
          sq.get('greeting', 'An old man peers at you over a pile of books.'),
          on_cancel=lambda: None, view=view, place=name)

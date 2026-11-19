"""Each game's own story, checked from start to finish: the endings and
the side quests.  for_game(name) gives the checks for a game; a game with
none here still gets every generic test in test_game.py."""

import util
from blobber.talk import answer


def npc(g, lid, ch):
    return g.levels[lid].legend[ch]['talk']


# ---------------------------------------------------------- The Ashen Crypt

def ashen_ending(t, gd):
    g = util.new_game(gd, strong=True)
    g.party[0].equip['weapon'] = 'embersword'
    g.change_level('crypt3', 12, 16, 2)
    g.modes = g.modes[:1]
    g.walk(0)                       # onto the throne
    util.fight_out(g)
    t.assertTrue(g.flag('kingdead'))
    t.assertTrue(g.has_item('crown'))
    g.move_to(12, 18)               # the portal home
    g.key('1')
    t.assertEqual(g.st.level, 'town')
    g.modes = g.modes[:1]
    g.st.x, g.st.y, g.st.facing = 14, 7, 0
    g.walk(0)                       # into the temple
    for _ in range(3):
        g.key('enter')
    t.assertTrue(g.st.won)


def ashen_mine(t, gd):
    g = util.new_game(gd, strong=True)
    brokk = npc(g, 'mine', 'b')
    t.assertIn('KING', answer(g, brokk, 'hammer'))
    g.change_level('mine', 17, 11, 2)
    g.modes = g.modes[:1]
    g.walk(0)
    util.fight_out(g)
    t.assertTrue(g.flag('koboldking'))
    t.assertTrue(g.has_item('brokkhammer'))
    gold = g.st.gold
    answer(g, brokk, 'hammer')
    answer(g, brokk, 'hammer')      # rewards come once
    t.assertTrue(g.has_item('runering'))
    t.assertEqual(g.st.gold, gold + 150)


def ashen_prisoner(t, gd):
    g = util.new_game(gd)
    nim = npc(g, 'crypt2', 'n')
    gold = g.st.gold
    t.assertIn('FOOTSTEPS', answer(g, nim, 'riddle'))
    t.assertEqual(g.st.gold, gold - 20)
    g.give_party('bonekey')
    answer(g, nim, 'out')
    t.assertTrue(g.flag('nimfree'))
    t.assertFalse(g.active(g.levels['crypt2'].sq(10, 3)).get('block'))


# -------------------------------------------------------------- Benediction

def bene_ending(t, gd):
    g = util.new_game(gd, strong=True)
    g.party[0].give('burninghand')
    g.party[0].equip_item(len(g.party[0].pack) - 1)
    g.party[1].give('litany')
    g.st.supplies['rounds'] = 999
    g.change_level('deck3', 12, 11, 2)
    g.modes = g.modes[:1]
    g.set_flag('guards')
    g.walk(0)                       # the Burning Hand opens the bone wall
    t.assertEqual((g.st.x, g.st.y), (12, 13))
    g.st.x, g.st.y, g.st.facing = 13, 16, 2
    g.walk(0)
    util.fight_out(g)
    t.assertTrue(g.flag('matriarch'))
    t.assertTrue(g.has_item('heart'))
    g.move_to(13, 18)
    g.key('1')
    t.assertEqual(g.st.level, 'ship')
    g.modes = g.modes[:1]
    g.st.x, g.st.y, g.st.facing = 3, 3, 0
    g.walk(0)                       # report to Command
    for _ in range(3):
        g.key('enter')
    t.assertTrue(g.st.won)


def bene_pilgrims(t, gd):
    g = util.new_game(gd, strong=True)
    g.change_level('mercy', 7, 8, 2)
    g.modes = g.modes[:1]
    g.walk(0)
    for _ in range(3):
        g.key('enter')
    g.modes = g.modes[:1]
    t.assertTrue(g.has_item('tomasicon'))
    g.st.x, g.st.y, g.st.facing = 14, 9, 2
    g.set_flag(g.sqkey(14, 10, ':open'))
    g.walk(0)
    util.fight_out(g)
    t.assertTrue(g.flag('captain'))
    t.assertTrue(g.has_item('mercyshield'))
    answer(g, npc(g, 'deck1', 'i'), 'tomas')
    t.assertTrue(g.flag('ilse_safe'))
    t.assertFalse(g.has_item('tomasicon'))


# ---------------------------------------------------------------- Dustwater

def dust_ending(t, gd):
    g = util.new_game(gd, strong=True)
    g.st.supplies.update(rounds=999, bolts=999)
    g.change_level('water', 17, 12, 0)
    g.modes = g.modes[:1]
    g.walk(0)                       # into the sump
    util.fight_out(g)
    t.assertTrue(g.flag('snapper'))
    t.assertTrue(g.has_item('filtercore'))
    g.change_level('bunk2', 3, 4, 0)
    g.modes = g.modes[:1]
    g.walk(0)                       # the seed bank
    for _ in range(4):
        g.key('1')
        g.key('enter')
    g.modes = g.modes[:1]
    t.assertTrue(g.has_item('seeds'))
    g.st.x, g.st.y, g.st.facing = 9, 10, 0
    g.walk(0)                       # the Guardian
    util.fight_out(g)
    t.assertTrue(g.flag('guardian'))
    t.assertTrue(g.has_item('fusioncell'))
    g.move_to(10, 11)               # the lift home
    g.key('1')
    t.assertEqual(g.st.level, 'village')
    g.modes = g.modes[:1]
    g.st.x, g.st.y, g.st.facing = 6, 4, 0
    g.walk(0)                       # into the purifier
    pages = g.mode.pages if hasattr(g.mode, 'pages') else []
    t.assertTrue(g.st.won)
    t.assertEqual(len(pages), 4)    # with the seeds' page
    t.assertFalse(g.has_item('filtercore'))


def dust_purifier_waits(t, gd):
    g = util.new_game(gd)
    g.give_party('filtercore')
    g.st.x, g.st.y, g.st.facing = 6, 4, 0
    g.walk(0)
    t.assertFalse(g.st.won)
    t.assertTrue(g.has_item('filtercore'))


def dust_bunker_way(t, gd):
    g = util.new_game(gd, strong=True)
    g.change_level('waste', 7, 5, 0)
    g.modes = g.modes[:1]
    g.walk(0)                       # Rusk's camp
    util.fight_out(g)
    t.assertTrue(g.flag('rusk'))
    t.assertTrue(g.has_item('keycard'))
    g.st.x, g.st.y, g.st.facing = 27, 19, 2
    g.walk(0)                       # the keycard opens the hatch
    g.modes = g.modes[:1]
    t.assertEqual((g.st.x, g.st.y), (27, 21))
    # the lower door wants the soldier's word
    g.change_level('bunk1', 17, 9, 2)
    g.modes = g.modes[:1]
    g.walk(0)
    for ch in 'sunrise':
        g.key(ch)
    g.key('enter')
    t.assertTrue(g.flag('bunkercode'))
    g.modes = g.modes[:1]
    g.walk(0)
    t.assertEqual((g.st.x, g.st.y), (17, 11))


def dust_mutation_rules(t, gd):
    import random
    from blobber import rules
    g = util.new_game(gd)
    rook, tusk, bolt, vesper = g.party[:4]
    t.assertEqual(bolt.maxhp, 50)               # androids are built so
    t.assertGreaterEqual(rook.maxhp, 60)
    t.assertEqual(rules.bonus(3), -3)
    t.assertEqual(rules.bonus(18), 3)
    t.assertEqual(tusk.ac(), 9 - 3 - 2)         # hide and leathers
    t.assertEqual(rook.maxsp, 0)                # no mutations, no focus
    t.assertGreater(vesper.maxsp, 0)
    t.assertIn('ERAY', vesper.spells())
    # radiation: five failed saves give a mutant something new
    before = len(vesper.traits) + len(vesper.powers)
    vesper.radfail = 4
    rng = random.Random(3)
    sq = dict(rad=1)
    real_save = rules.HOOKS['save']
    rules.HOOKS['save'] = lambda c, kind, r: False
    try:
        rook.hp = vesper.hp = 999
        g.ev_radiation(sq, lambda: None)
    finally:
        rules.HOOKS['save'] = real_save
    t.assertEqual(len(vesper.traits) + len(vesper.powers), before + 1)
    t.assertEqual(rook.traits, [])              # pure humans only burn
    t.assertEqual(bolt.hp, 50)                  # androids don't even burn
    # a new character of each stock
    for race in rules.RACES:
        c = rules.Character.roll_new('X', race, 'Scout', rng)
        t.assertGreater(c.maxhp, 0)
        if race.startswith('Mutant'):
            t.assertTrue(c.traits or c.powers)
        notes = c.level_up(rng)
        t.assertTrue(notes)


def dust_hermit(t, gd):
    g = util.new_game(gd)
    grue = npc(g, 'city', 'n')
    t.assertIn('ANTITOX', answer(g, grue, 'medicine'))
    g.give_party('antitox')
    gold = g.st.gold
    answer(g, grue, 'medicine')
    t.assertTrue(g.has_item('grenade'))
    t.assertFalse(g.has_item('antitox'))
    t.assertEqual(g.st.gold, gold + 25)


SCENARIOS = {
    'ashencrypt': [('the ending', ashen_ending), ('the Old Mine', ashen_mine),
                   ("Nim's cage", ashen_prisoner)],
    'benediction': [('the ending', bene_ending),
                    ('the Mercy of Kessa', bene_pilgrims)],
    'dustwater': [('the ending', dust_ending),
                  ('the purifier waits for both', dust_purifier_waits),
                  ('the way into the bunker', dust_bunker_way),
                  ('mutations and radiation', dust_mutation_rules),
                  ("Grue's medicine", dust_hermit)],
}


def for_game(name):
    return SCENARIOS.get(name, [])

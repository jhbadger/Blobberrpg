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


SCENARIOS = {
    'ashencrypt': [('the ending', ashen_ending), ('the Old Mine', ashen_mine),
                   ("Nim's cage", ashen_prisoner)],
    'benediction': [('the ending', bene_ending),
                    ('the Mercy of Kessa', bene_pilgrims)],
}


def for_game(name):
    return SCENARIOS.get(name, [])

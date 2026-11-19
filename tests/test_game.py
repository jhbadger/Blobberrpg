"""Tests of one game (named by the BLOBBER_GAME environment variable; see
run_tests.py, which runs these once for each game, each in its own
process).  Most are generic, so a new game gets them for nothing;
scenarios.py adds each game's own story checks.

BLOBBER_FUZZ sets how many random games to play (default 4)."""

import contextlib
import io
import os
import random
import unittest

import util
import scenarios

NAME = os.environ.get('BLOBBER_GAME') or util.games()[0]
GD = util.load(NAME)


class Game(unittest.TestCase):
    def test_selftest(self):
        import blobber
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = blobber.selftest(GD)
        self.assertEqual(status, 0, out.getvalue())

    def test_every_level_draws_both_ways(self):
        g = util.new_game(GD)
        for lid, L in g.levels.items():
            g.st.level = lid
            g.st.x, g.st.y = next((x, y) for y in range(L.h)
                                  for x in range(L.w)
                                  if not L.sq(x, y).get('solid'))
            for portrait in (False, True):
                g.portrait = portrait
                f = g.frame()
                self.assertEqual((f.w, f.h),
                                 (360, 676) if portrait else (640, 400))

    def test_save_load_and_slots(self):
        g = util.new_game(GD)
        g.st.gold = 1234
        self.assertTrue(g.save())
        self.assertTrue(g.save(path=g.slot_path(2)))
        g.st.gold = 1
        self.assertTrue(g.load())
        self.assertEqual(g.st.gold, 1234)
        self.assertTrue(g.slot_info(2))
        self.assertIsNone(g.slot_info(5))
        g.st.gold = 7
        self.assertTrue(g.load(g.slot_path(2)))
        self.assertEqual(g.st.gold, 1234)

    def test_fuzz(self):
        runs = int(os.environ.get('BLOBBER_FUZZ', '4'))
        for seed in range(runs):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                g = util.new_game(GD, seed, strong=bool(seed % 2))
                lid = rng.choice(list(g.levels))
                L = g.levels[lid]
                g.st.level = lid
                g.st.x, g.st.y = rng.choice(
                    [(x, y) for y in range(L.h) for x in range(L.w)
                     if not L.sq(x, y).get('solid') and
                     not L.sq(x, y).get('block')])
                util.fuzz(g, rng, 1500)

    def test_every_guardian_can_be_beaten(self):
        for lid, L in util.new_game(GD).levels.items():
            for ch, sq in L.legend.items():
                if not sq.get('fight'):
                    continue
                with self.subTest(level=lid, square=ch):
                    g = util.new_game(GD, strong=True)
                    g.st.level = lid
                    g.st.x, g.st.y = L.find(ch)
                    g.start_combat(list(sq['fight']))
                    util.fight_out(g)
                    self.assertFalse(util.in_combat(g))
                    self.assertTrue(any(c.alive for c in g.party))

    def test_every_conversation(self):
        from blobber.talk import answer, talk
        from blobber.rules import ITEMS
        for lid, L in util.new_game(GD).levels.items():
            for ch, sq in L.legend.items():
                npc = sq.get('talk')
                if not npc:
                    continue
                with self.subTest(person=npc['id']):
                    g = util.new_game(GD)
                    g.st.level = lid
                    talk(g, sq)                 # the scroll comes up
                    g.frame()
                    topics = list(npc.get('topics', {})) + ['xyzzy']
                    for k in topics:
                        self.assertIsInstance(answer(g, npc, k.lower()), str)
                    # and again with everything they might want
                    for t in npc.get('topics', {}).values():
                        if isinstance(t, dict):
                            need = t.get('needs') or t.get('takes')
                            if need in ITEMS:
                                g.give_party(need)
                            elif need:
                                g.set_flag(need)
                    g.st.gold += 1000
                    for k in topics:
                        self.assertIsInstance(answer(g, npc, k.lower()), str)


class Story(unittest.TestCase):
    def test_scenarios(self):
        for name, fn in scenarios.for_game(NAME):
            with self.subTest(scenario=name):
                fn(self, GD)


if __name__ == '__main__':
    unittest.main()

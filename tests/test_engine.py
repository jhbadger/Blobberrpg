"""Tests of the engine's parts that don't need a game."""

import unittest

import util  # noqa: F401  (puts the repository on the path)

from blobber import font, words, layout
from blobber.gfx import Surface, Image
from blobber.rules import roll, add_bonus, dice_max
from blobber.view import View, Look
from blobber import music


class Dice(unittest.TestCase):
    def test_roll_stays_in_range(self):
        import random
        rng = random.Random(1)
        for _ in range(500):
            v = roll('2d6+1', rng)
            self.assertTrue(3 <= v <= 13)
        self.assertEqual(roll(7), 7)
        self.assertEqual(dice_max('3d8+2'), 26)

    def test_add_bonus(self):
        self.assertEqual(add_bonus('1d6+1', 3), '1d6+4')
        self.assertEqual(add_bonus('2d6+2', -2), '2d6')
        self.assertEqual(add_bonus('1d4', -1), '1d4-1')


class Words(unittest.TestCase):
    def tearDown(self):
        words.setup({})

    def test_override_and_fill(self):
        words.setup({'money': 'credits'})
        self.assertEqual(words.w('money'), 'credits')
        self.assertEqual(words.w('found_money', 5),
                         'You find 5 gold pieces.')

    def test_word_without_slot(self):
        # a game's word may leave out the %s the engine fills in
        words.setup({'g_remove': 'Send a brother to the reserve'})
        self.assertEqual(words.w('g_remove', 'Command'),
                         'Send a brother to the reserve')


class Drawing(unittest.TestCase):
    def test_text_and_wrap(self):
        s = Surface(100, 20)
        w = s.text(0, 0, 'Hello', (255, 255, 255))
        self.assertEqual(w, font.width('Hello'))
        lines = font.wrap('one two three four five six', 40)
        self.assertTrue(all(font.width(l) <= 40 or ' ' not in l
                            for l in lines))

    def test_blit_clips(self):
        s = Surface(10, 10)
        img = Image.from_pixels(4, 4, [(255, 0, 0)] * 16)
        s.blit(img, -2, -2)
        s.blit(img, 8, 8)
        self.assertEqual(bytes(s.buf[0:3]), b'\xff\x00\x00')

    def test_view_renders_and_caches(self):
        v = View()
        s = Surface(320, 224)

        def look(k, x):
            if abs(x) > 0:
                return Look(True, 'plain')
            return Look(False, None, 'plain', 'plain')
        v.render(s, 0, 0, look, 3.0)
        before = bytes(s.buf)
        v.render(s, 0, 0, look, 3.0)
        self.assertEqual(before, bytes(s.buf))
        self.assertNotEqual(set(before), {0})


class Layout(unittest.TestCase):
    def test_taps_map_back(self):
        # the view keeps its place; the scroll moves under it
        self.assertEqual(layout.to_wide(100, 100), (100, 100))
        ax, ay = layout.PAPER_AT
        px, py, pw, ph = layout.PAPER_SRC
        self.assertEqual(layout.to_wide(ax + 5, ay + 7), (px + 5, py + 7))
        self.assertIsNone(layout.to_wide(2, layout.H - 2))


class Music(unittest.TestCase):
    def test_stock_tunes_fit(self):
        for name, tune in music.TUNES.items():
            with self.subTest(tune=name):
                music.check(tune)


if __name__ == '__main__':
    unittest.main()

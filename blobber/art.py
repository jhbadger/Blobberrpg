"""Pictures painted in code: monsters, townsfolk, things standing in the
dungeon, and the carved frame round the screen.

Each picture is a function registered by name that paints on a Painter
and returns it; pictures are made on first use.  A game can register
its own with @picture('name', w, h).
"""

import math
import random

from .paint import Painter
from .gfx import Image, rgb, mix, scale
from . import textures

_GEN = {}
_CACHE = {}


def picture(name, w=160, h=160, height=None):
    """Register a painting.  height is how tall it stands in the dungeon
    (a wall is 0.84) when shown as an object in a square."""
    def deco(fn):
        _GEN[name] = (fn, w, h, height)
        return fn
    return deco


def get(name):
    img = _CACHE.get(name)
    if img is None:
        if name not in _GEN:
            name2 = 'unknown'
            fn, w, h, _ = _GEN[name2]
        else:
            fn, w, h, _ = _GEN[name]
        p = Painter(w, h, seed=hash(name) & 0xffff)
        p.glow.update({'eyered', 'eyegold', 'eyecyan', 'eyegreen', 'flame',
                       'ember', 'violetglow', 'greenflame'})
        fn(p)
        img = _CACHE[name] = p.image()
    return img


def world_height(name):
    return _GEN.get(name, (None, 0, 0, 0.5))[3] or 0.5


def sprite_source(name):
    return get(name), world_height(name)


def names():
    return sorted(_GEN)


GREENFLAME = ('#003a10', '#109a20', '#50f040', '#c0ff90', '#ffffff')


def eye(p, x, y, r, m='eyered'):
    p.circle(x, y, r, m, lum=0.55)
    p.circle(x - r * 0.3, y - r * 0.3, max(0.8, r * 0.35), m, lum=1.0)


def skull(p, cx, cy, r, bias=0.0, eyes='shadow', eye_lum=0.08, jaw=True):
    textures.skull(p, cx, cy, r, bias, eyes, eye_lum)


# ------------------------------------------------------------- monsters

@picture('unknown')
def _p(p):
    p.ellipse(80, 100, 40, 50, 'black')
    eye(p, 66, 90, 6)
    eye(p, 94, 90, 6)


@picture('rat')
def _p(p):
    p.chain([(120, 132), (140, 128), (152, 112), (154, 92), (148, 80)],
            4.5, 1.2, 'pink')
    p.limb(112, 128, 116, 150, 9, 5, 'fur', tex=0.2)
    p.ellipse(118, 152, 9, 4, 'pink')
    p.ellipse(90, 118, 46, 30, 'fur', tex=0.3, angle=-0.08)
    p.speckle('fur', 0.15, 0.15)
    p.ellipse(52, 114, 27, 23, 'fur', tex=0.25, angle=-0.2)
    p.ellipse(28, 124, 17, 11, 'fur', tex=0.2, angle=0.35)
    p.circle(13, 129, 4.5, 'pink')
    p.limb(60, 134, 54, 150, 7, 4, 'fur')
    p.ellipse(50, 152, 9, 4, 'pink')
    p.limb(84, 140, 82, 151, 6, 4, 'fur')
    p.ellipse(80, 153, 8, 3.5, 'pink')
    p.ellipse(60, 90, 11, 14, 'fur', angle=0.3)
    p.ellipse(60, 91, 6.5, 9.5, 'pink', angle=0.3, bias=-0.1)
    eye(p, 36, 110, 4.5)
    p.poly([(19, 133), (24, 133), (22, 141)], 'teeth', lum=0.85)
    p.poly([(25, 133), (29, 133), (27, 140)], 'teeth', lum=0.75)
    for k in range(3):
        p.line(18, 124 + k * 3, 2, 116 + k * 7, 'greyhair', 0.8, 0.8)


@picture('bat')
def _p(p):
    for s in (-1, 1):
        def X(x):
            return 80 + s * (x - 80)
        p.poly([(X(76), 74), (X(30), 34), (X(6), 60), (X(22), 70),
                (X(18), 92), (X(36), 84), (X(44), 108), (X(58), 92),
                (X(72), 100)], 'black', lum=0.42, gradx=-0.25 * s, tex=0.05)
        for (tx, ty) in ((30, 34), (6, 60), (18, 92), (44, 108)):
            p.limb(X(76), 72, X(tx), ty, 2.2, 1.2, 'fur', bias=-0.1)
    p.ellipse(80, 86, 15, 22, 'fur', tex=0.25)
    p.ellipse(80, 62, 13, 12, 'fur', tex=0.2)
    p.poly([(68, 58), (64, 34), (76, 52)], 'fur', lum=0.45)
    p.poly([(92, 58), (96, 34), (84, 52)], 'fur', lum=0.45)
    p.poly([(68, 54), (66, 40), (73, 52)], 'pink', lum=0.5)
    p.poly([(92, 54), (94, 40), (87, 52)], 'pink', lum=0.5)
    eye(p, 74, 60, 3)
    eye(p, 86, 60, 3)
    p.ellipse(80, 69, 5, 3, 'mouth', lum=0.3)
    p.poly([(76, 69), (78, 69), (77, 75)], 'teeth', lum=0.9)
    p.poly([(82, 69), (84, 69), (83, 75)], 'teeth', lum=0.9)
    p.limb(74, 106, 70, 118, 2, 1.5, 'fur')
    p.limb(86, 106, 90, 118, 2, 1.5, 'fur')


@picture('kobold')
def _p(p):
    p.line(112, 22, 106, 156, 'wood', 0.55, 4)
    p.poly([(112, 2), (117, 22), (107, 22)], 'steel', lum=0.75, gradx=-0.4)
    p.chain([(84, 118), (108, 134), (124, 128), (132, 116)], 6, 2, 'rust')
    for s in (-1, 1):
        p.limb(80 + s * 10, 112, 80 + s * 14, 134, 8, 6, 'rust', tex=0.15)
        p.limb(80 + s * 14, 134, 80 + s * 12, 152, 6, 4, 'rust', tex=0.15)
        p.ellipse(80 + s * 15, 154, 9, 4, 'rust')
    p.ellipse(80, 98, 19, 24, 'rust', tex=0.2)
    p.ellipse(80, 102, 11, 16, 'bone', bias=-0.15)
    p.poly([(62, 112), (98, 112), (94, 130), (80, 124), (66, 130)],
           'leather', lum=0.5, grad=-0.2)
    p.limb(62, 84, 54, 106, 6, 5, 'rust')
    p.limb(54, 106, 62, 118, 5, 4, 'rust')
    p.limb(98, 84, 106, 98, 6, 5, 'rust')
    p.limb(106, 98, 108, 82, 5, 4, 'rust')
    p.circle(108, 80, 5, 'rust')
    p.ellipse(80, 60, 18, 16, 'rust', tex=0.2)
    p.ellipse(66, 68, 13, 8, 'rust', angle=0.25, tex=0.2)
    p.limb(70, 48, 58, 30, 3.5, 1.2, 'bone')
    p.limb(90, 48, 100, 30, 3.5, 1.2, 'bone')
    eye(p, 72, 56, 3.5, 'eyegold')
    eye(p, 88, 56, 3.5, 'eyegold')
    p.line(56, 72, 72, 74, 'mouth', 0.2, 1.5)
    p.poly([(60, 72), (63, 72), (61, 77)], 'teeth', lum=0.9)


@picture('slime')
def _p(p):
    p.ellipse(80, 122, 66, 36, 'slime', tex=0.08)
    p.ellipse(78, 100, 42, 34, 'slime', tex=0.08)
    for (x, w) in ((30, 7), (58, 6), (104, 8), (128, 6)):
        p.limb(x, 140, x + 2, 156, w, w * 0.6, 'slime')
    p.ellipse(80, 156, 66, 4, 'slime', bias=-0.2)
    skull(p, 92, 112, 13, bias=-0.35)
    p.limb(48, 130, 70, 136, 3, 3, 'bone', bias=-0.4)
    for (x, y, r) in ((54, 96, 5), (110, 128, 4), (70, 132, 3),
                      (40, 116, 3.5), (100, 88, 3)):
        p.circle(x, y, r, 'slime', bias=0.3)
    p.ellipse(60, 84, 12, 6, 'slime', lum=0.95, angle=-0.5)
    p.circle(50, 108, 3, 'slime', lum=0.98)


@picture('skeleton')
def _p(p):
    p.circle(42, 98, 21, 'wood', tex=0.25)
    p.circle(42, 98, 21, 'wood', tex=0.25)
    p.ellipse(42, 98, 21, 21, 'wood', tex=0.3)
    p.circle(42, 98, 5, 'iron')
    for s in (-1, 1):
        p.limb(80 + s * 9, 108, 80 + s * 12, 130, 3.5, 3, 'bone')
        p.limb(80 + s * 12, 130, 80 + s * 11, 150, 3, 2.5, 'bone')
        p.circle(80 + s * 12, 130, 4, 'bone')
        p.ellipse(80 + s * 13, 153, 8, 3.5, 'bone')
    p.ellipse(80, 104, 17, 8, 'bone')
    p.limb(80, 46, 80, 102, 3.5, 3.5, 'bone')
    for i in range(5):
        y = 56 + i * 8
        w = 18 - abs(i - 1.5) * 2
        for s in (-1, 1):
            p.chain([(80, y), (80 + s * w * 0.7, y + 1),
                     (80 + s * w, y + 7)], 2.4, 1.8, 'bone')
    p.limb(58, 50, 102, 50, 3.5, 3.5, 'bone')
    p.limb(60, 52, 50, 78, 3.5, 3, 'bone')
    p.limb(50, 78, 46, 96, 3, 2.5, 'bone')
    p.limb(100, 52, 112, 78, 3.5, 3, 'bone')
    p.limb(112, 78, 120, 100, 3, 2.5, 'bone')
    p.line(120, 104, 150, 30, 'rust', 0.6, 6)
    p.line(122, 102, 151, 28, 'steel', 0.75, 2)
    p.line(112, 96, 130, 106, 'iron', 0.55, 3)
    p.circle(120, 101, 4.5, 'bone')
    p.circle(117, 108, 3, 'iron')
    p.ellipse(42, 98, 21, 21, 'wood', tex=0.3)
    p.circle(42, 98, 6, 'iron')
    for a in range(8):
        ang = a * math.pi / 4
        p.circle(42 + 16 * math.cos(ang), 98 + 16 * math.sin(ang), 1.6, 'iron',
                 lum=0.8)
    p.circle(48, 96, 4, 'bone')
    skull(p, 80, 28, 15, eyes='shadow')
    eye(p, 74, 30, 2.6)
    eye(p, 86, 30, 2.6)


@picture('zombie')
def _p(p):
    for s in (-1, 1):
        p.limb(80 + s * 12, 108, 80 + s * 15, 132, 9, 8, 'cloth', tex=0.2)
        p.limb(80 + s * 15, 132, 80 + s * 13, 150, 8, 6, 'cloth', tex=0.2)
        p.ellipse(80 + s * 14, 153, 10, 4.5, 'leather')
    p.poly([(56, 50), (104, 50), (110, 110), (100, 104), (92, 114),
            (84, 104), (74, 116), (66, 104), (52, 112)], 'cloth', lum=0.55,
           gradx=-0.3, tex=0.18)
    p.ellipse(88, 78, 9, 13, 'rotgreen')
    for i in range(3):
        p.line(80, 70 + i * 6, 96, 72 + i * 6, 'bone', 0.75, 2)
    p.chain([(58, 54), (46, 70), (38, 84)], 7, 6, 'rotgreen', tex=0.15)
    p.chain([(102, 54), (114, 70), (124, 82)], 7, 6, 'rotgreen', tex=0.15)
    for (hx, hy, s) in ((36, 90, -1), (126, 88, 1)):
        p.ellipse(hx, hy, 9, 8, 'rotgreen')
        for k in range(4):
            p.limb(hx + s * (k - 1.5) * 3, hy + 4, hx + s * (k - 1.5) * 4,
                   hy + 14, 1.8, 1.4, 'rotgreen')
    p.limb(80, 46, 80, 54, 6, 6, 'rotgreen')
    p.ellipse(80, 34, 17, 19, 'rotgreen', tex=0.15)
    p.ellipse(70, 30, 6, 5, 'shadow', lum=0.08)
    p.ellipse(90, 31, 6, 5, 'shadow', lum=0.08)
    eye(p, 70, 30, 2, 'eyegold')
    eye(p, 90, 31, 2, 'eyegold')
    p.ellipse(80, 44, 7, 6, 'mouth', lum=0.4)
    for k in (-1, 1):
        p.rect(80 + k * 3 - 1, 39, 2, 3, 'teeth', lum=0.85)
    p.ellipse(72, 18, 12, 6, 'hair', tex=0.3)
    p.limb(64, 20, 58, 44, 2.5, 1, 'hair')
    p.limb(94, 20, 100, 40, 2.5, 1, 'hair')


@picture('spider')
def _p(p):
    p.ellipse(80, 66, 46, 38, 'black', tex=0.12)
    p.poly([(74, 48), (86, 48), (80, 60)], 'red', lum=0.65)
    p.poly([(74, 72), (86, 72), (80, 60)], 'red', lum=0.65)
    for s in (-1, 1):
        for i in range(4):
            bx = 80 + s * (16 + i * 2)
            by = 98 + i * 3
            kx = 80 + s * (44 + i * 14)
            ky = 58 + i * 12
            fx = 80 + s * (54 + i * 7)
            fy = 152
            p.limb(bx, by, kx, ky, 5, 4, 'black', tex=0.12)
            p.limb(kx, ky, fx, fy, 4, 1.5, 'black', tex=0.12)
            p.circle(kx, ky, 4.5, 'black')
    p.ellipse(80, 106, 26, 21, 'black', tex=0.15)
    p.ellipse(80, 98, 18, 12, 'greyfur', tex=0.25, bias=-0.1)
    for (x, y, r) in ((73, 98, 3.5), (87, 98, 3.5), (66, 94, 2.4),
                      (94, 94, 2.4), (76, 91, 2), (84, 91, 2), (70, 104, 1.8),
                      (90, 104, 1.8)):
        eye(p, x, y, r)
    p.chain([(72, 118), (68, 128), (72, 136)], 4.5, 1.5, 'bone')
    p.chain([(88, 118), (92, 128), (88, 136)], 4.5, 1.5, 'bone')


@picture('ghoul')
def _p(p):
    for s in (-1, 1):
        p.limb(80 + s * 14, 112, 80 + s * 30, 128, 9, 7, 'paleskin', tex=0.15)
        p.limb(80 + s * 30, 128, 80 + s * 24, 150, 7, 5, 'paleskin', tex=0.15)
        p.ellipse(80 + s * 26, 153, 10, 4, 'paleskin')
    p.ellipse(82, 92, 26, 30, 'paleskin', tex=0.2, angle=0.25)
    for i in range(4):
        p.line(70, 80 + i * 6, 92, 84 + i * 6, 'paleskin', 0.35, 1)
    p.poly([(60, 108), (104, 108), (100, 126), (84, 120), (70, 128)],
           'cloth', lum=0.4, tex=0.2)
    p.chain([(62, 76), (44, 98), (36, 124)], 7, 5, 'paleskin', tex=0.15)
    p.chain([(104, 74), (118, 98), (126, 126)], 7, 5, 'paleskin', tex=0.15)
    for (hx, hy) in ((36, 128), (126, 130)):
        p.ellipse(hx, hy, 7, 6, 'paleskin')
        for k in range(4):
            p.limb(hx + (k - 1.5) * 3.5, hy + 3, hx + (k - 1.5) * 5,
                   hy + 20, 1.6, 0.6, 'bone')
    p.ellipse(74, 60, 17, 16, 'paleskin', tex=0.15)
    p.poly([(58, 54), (40, 40), (60, 62)], 'paleskin', lum=0.55)
    p.poly([(90, 54), (106, 38), (88, 62)], 'paleskin', lum=0.55)
    p.ellipse(66, 57, 5, 4, 'shadow', lum=0.1)
    p.ellipse(82, 57, 5, 4, 'shadow', lum=0.1)
    eye(p, 66, 57, 2.6, 'eyegold')
    eye(p, 82, 57, 2.6, 'eyegold')
    p.ellipse(74, 70, 10, 5, 'mouth', lum=0.35)
    for k in range(-3, 4):
        p.poly([(74 + k * 2.6 - 1, 67), (74 + k * 2.6 + 1, 67),
                (74 + k * 2.6, 71)], 'teeth', lum=0.9)


@picture('cultist')
def _p(p):
    p.poly([(80, 40), (54, 62), (40, 156), (120, 156), (106, 62)],
           'crimson', lum=0.55, gradx=-0.35, tex=0.06)
    for x in (56, 66, 80, 94, 104):
        p.line(80 + (x - 80) * 0.3, 70, x, 154, 'crimson', 0.3, 1.2)
    p.rect(58, 92, 44, 4, 'gold', lum=0.6)
    p.line(68, 96, 64, 120, 'gold', 0.5, 2)
    p.chain([(60, 66), (44, 86), (50, 102)], 9, 7, 'crimson')
    p.chain([(100, 66), (116, 80), (120, 62)], 9, 7, 'crimson')
    p.circle(50, 104, 5, 'skin')
    p.line(50, 106, 48, 128, 'steel', 0.8, 3)
    p.line(44, 104, 56, 104, 'gold', 0.7, 2)
    p.circle(120, 56, 5, 'skin')
    p.circle(122, 42, 11, 'violetglow', lum=0.5)
    p.circle(122, 42, 7, 'violetglow', lum=0.8)
    p.circle(119, 39, 3, 'violetglow', lum=1.0)
    p.ellipse(80, 40, 21, 24, 'crimson', bias=0.05)
    p.ellipse(80, 46, 12, 14, 'shadow', lum=0.04)
    eye(p, 75, 46, 2.2, 'eyegold')
    eye(p, 85, 46, 2.2, 'eyegold')
    p.circle(80, 72, 4, 'gold')


@picture('wraith')
def _p(p):
    pts = [(80, 22), (48, 46), (34, 96), (26, 154), (40, 136), (50, 156),
           (62, 138), (74, 156), (86, 138), (98, 156), (110, 136), (122, 154),
           (130, 132), (124, 92), (112, 46)]
    p.poly(pts, 'ghost', lum=0.45, gradx=-0.3, grad=-0.3, tex=0.1)
    for x in (52, 66, 80, 96, 110):
        p.line(80 + (x - 80) * 0.25, 54, x, 140, 'ghost', 0.3, 1.5)
    p.chain([(56, 62), (40, 84), (30, 96)], 8, 6, 'ghost')
    p.chain([(104, 62), (120, 84), (130, 96)], 8, 6, 'ghost')
    for (hx, hy, s) in ((28, 100, -1), (132, 100, 1)):
        p.circle(hx, hy, 5, 'bone')
        for k in range(4):
            p.limb(hx + s * (k - 1.5) * 2, hy + 2, hx + s * (k * 3 - 2),
                   hy + 18, 1.4, 0.8, 'bone')
    p.ellipse(80, 40, 20, 24, 'ghost', bias=0.05)
    p.ellipse(80, 46, 12, 15, 'shadow', lum=0.0)
    eye(p, 74, 44, 3, 'eyecyan')
    eye(p, 86, 44, 3, 'eyecyan')
    p.speckle('ghost', 0.1, 0.2)


@picture('orc')
def _p(p):
    p.line(124, 24, 116, 150, 'wood', 0.5, 5)
    p.poly([(124, 20), (150, 8), (156, 32), (150, 56), (122, 44)],
           'steel', lum=0.7, gradx=0.3, grad=-0.2)
    p.poly([(124, 26), (110, 18), (110, 46), (122, 40)], 'steel', lum=0.5)
    for s in (-1, 1):
        p.limb(80 + s * 14, 110, 80 + s * 18, 134, 11, 9, 'leather', tex=0.15)
        p.limb(80 + s * 18, 134, 80 + s * 17, 150, 9, 8, 'iron')
        p.ellipse(80 + s * 18, 153, 12, 5, 'iron')
    p.ellipse(80, 84, 32, 34, 'green', tex=0.15)
    p.line(54, 60, 104, 112, 'leather', 0.45, 6)
    p.rect(52, 102, 56, 10, 'leather', lum=0.45)
    p.circle(80, 107, 5, 'iron')
    for s in (-1, 1):
        p.ellipse(80 + s * 34, 60, 15, 12, 'iron', tex=0.15)
        for k in range(3):
            p.circle(80 + s * (28 + k * 6), 54, 1.6, 'steel', lum=0.9)
    p.chain([(48, 66), (40, 92), (46, 112)], 11, 9, 'green', tex=0.15)
    p.circle(46, 116, 9, 'green')
    p.chain([(112, 66), (120, 84), (120, 98)], 11, 9, 'green', tex=0.15)
    p.circle(120, 100, 9, 'green')
    p.ellipse(80, 38, 20, 19, 'green', tex=0.15)
    p.rect(62, 28, 36, 6, 'green', lum=0.35)
    eye(p, 71, 34, 3, 'eyered')
    eye(p, 89, 34, 3, 'eyered')
    p.ellipse(80, 44, 6, 3, 'green', lum=0.35)
    p.ellipse(80, 50, 10, 4, 'mouth', lum=0.3)
    p.chain([(72, 52), (70, 44)], 2.5, 1.2, 'bone')
    p.chain([(88, 52), (90, 44)], 2.5, 1.2, 'bone')
    p.chain([(80, 20), (80, 10), (88, 2)], 4, 2, 'hair')


@picture('imp')
def _p(p):
    for s in (-1, 1):
        def X(x):
            return 80 + s * (x - 80)
        p.poly([(X(74), 70), (X(36), 40), (X(22), 62), (X(34), 66),
                (X(32), 84), (X(50), 78), (X(66), 90)], 'crimson', lum=0.45,
               tex=0.05)
        p.limb(X(74), 70, X(36), 40, 2, 1, 'red')
    p.chain([(88, 112), (110, 126), (126, 116), (132, 100)], 3, 1.5, 'red')
    p.poly([(132, 92), (138, 102), (128, 104)], 'red', lum=0.6)
    for s in (-1, 1):
        p.chain([(80 + s * 8, 110), (80 + s * 14, 124), (80 + s * 10, 140)],
                5, 3, 'red')
        p.ellipse(80 + s * 11, 142, 6, 3, 'black')
    p.ellipse(80, 96, 16, 20, 'red', tex=0.15)
    p.chain([(66, 86), (52, 96), (44, 84)], 5, 3.5, 'red')
    p.chain([(94, 86), (104, 100), (110, 110)], 5, 3.5, 'red')
    p.circle(42, 74, 12, 'flame', lum=0.6)
    p.circle(42, 74, 7, 'flame', lum=0.85)
    p.circle(40, 72, 3, 'flame', lum=1.0)
    p.ellipse(80, 64, 15, 14, 'red', tex=0.15)
    p.chain([(70, 54), (62, 42), (66, 30)], 3.5, 1, 'bone')
    p.chain([(90, 54), (98, 42), (94, 30)], 3.5, 1, 'bone')
    p.poly([(64, 60), (52, 52), (66, 66)], 'red', lum=0.5)
    p.poly([(96, 60), (108, 52), (94, 66)], 'red', lum=0.5)
    eye(p, 73, 62, 3, 'eyegold')
    eye(p, 87, 62, 3, 'eyegold')
    p.poly([(70, 70), (90, 70), (80, 77)], 'mouth', lum=0.3)
    for k in range(-2, 3):
        p.poly([(80 + k * 3.5 - 1, 70), (80 + k * 3.5 + 1, 70),
                (80 + k * 3.5, 73)], 'teeth', lum=0.9)


@picture('deathknight')
def _p(p):
    p.poly([(56, 46), (104, 46), (124, 156), (36, 156)], 'crimson',
           lum=0.35, gradx=0.3, tex=0.08)
    for s in (-1, 1):
        p.limb(80 + s * 13, 108, 80 + s * 16, 132, 10, 9, 'darksteel')
        p.limb(80 + s * 16, 132, 80 + s * 15, 150, 9, 8, 'darksteel')
        p.ellipse(80 + s * 16, 153, 11, 5, 'darksteel')
        p.circle(80 + s * 16, 132, 7, 'darksteel', bias=0.1)
    p.poly([(58, 50), (102, 50), (98, 104), (80, 112), (62, 104)],
           'darksteel', lum=0.5, gradx=-0.4, grad=-0.2)
    p.ellipse(80, 72, 18, 20, 'darksteel', bias=0.05)
    p.line(80, 56, 80, 96, 'darksteel', 0.25, 1.5)
    p.rect(60, 100, 40, 8, 'leather', lum=0.4)
    p.circle(80, 104, 4, 'gold')
    for s in (-1, 1):
        p.ellipse(80 + s * 26, 56, 16, 12, 'darksteel', tex=0.1)
        p.ellipse(80 + s * 26, 60, 15, 7, 'darksteel', bias=-0.1)
        p.chain([(80 + s * 30, 62), (80 + s * 28, 86), (80 + s * 12, 96)],
                8, 7, 'darksteel')
    p.circle(80, 96, 9, 'darksteel')
    p.line(80, 100, 80, 156, 'steel', 0.75, 7)
    p.line(78, 100, 78, 154, 'steel', 1.0, 1)
    p.line(64, 96, 96, 96, 'gold', 0.6, 4)
    p.line(80, 70, 80, 92, 'leather', 0.4, 4)
    p.circle(80, 68, 5, 'gold')
    p.ellipse(80, 32, 16, 19, 'darksteel', tex=0.1)
    p.chain([(66, 22), (54, 14), (50, 0)], 4.5, 1.5, 'bone')
    p.chain([(94, 22), (106, 14), (110, 0)], 4.5, 1.5, 'bone')
    p.rect(68, 30, 24, 4, 'shadow', lum=0.0)
    p.rect(79, 34, 2, 12, 'shadow', lum=0.0)
    eye(p, 73, 32, 2.2)
    eye(p, 87, 32, 2.2)


@picture('ashenking', 200, 180, height=0.84)
def _p(p):
    p.material('greenflame', *GREENFLAME, glow=True)
    # the throne
    p.rect(30, 20, 140, 160, 'stone', lum=0.35, gradx=-0.3)
    p.rect(30, 20, 140, 6, 'stone', lum=0.6)
    for x in (30, 160):
        p.rect(x, 0, 10, 180, 'stone', lum=0.45, gradx=-0.4)
        p.circle(x + 5, 4, 8, 'gold')
    p.poly([(56, 60), (144, 60), (156, 178), (44, 178)], 'black', lum=0.4,
           tex=0.08)
    for s in (-1, 1):
        p.limb(100 + s * 16, 130, 100 + s * 22, 156, 9, 8, 'ash')
        p.limb(100 + s * 22, 156, 100 + s * 22, 174, 4, 3, 'bone')
        p.ellipse(100 + s * 23, 176, 8, 3.5, 'bone')
    p.poly([(70, 58), (130, 58), (134, 140), (66, 140)], 'ash', lum=0.5,
           gradx=-0.35, tex=0.12)
    p.rect(96, 58, 8, 82, 'gold', lum=0.6, gradx=-0.3)
    for i in range(4):
        p.circle(100, 70 + i * 18, 2.5, 'red', lum=0.7)
    for s in (-1, 1):
        p.ellipse(100 + s * 32, 62, 17, 11, 'ash', tex=0.1)
        p.rect(100 + s * 32 - 17, 62, 34, 3, 'gold', lum=0.65)
    # left arm resting, right arm holding the staff
    p.chain([(68, 66), (58, 96), (68, 120)], 9, 7, 'ash')
    p.circle(70, 122, 5, 'bone')
    for k in range(4):
        p.limb(70 + k * 2, 124, 72 + k * 3, 134, 1.3, 0.8, 'bone')
    p.line(150, 30, 146, 178, 'wood', 0.5, 5)
    skull(p, 150, 26, 8)
    p.ellipse(150, 10, 9, 14, 'greenflame', lum=0.55)
    p.ellipse(150, 13, 5, 9, 'greenflame', lum=0.85)
    p.chain([(132, 66), (146, 88), (148, 100)], 9, 7, 'ash')
    p.circle(148, 102, 5, 'bone')
    p.limb(100, 48, 100, 60, 5, 5, 'bone')
    skull(p, 100, 38, 17)
    eye(p, 93, 40, 2.8, 'greenflame')
    eye(p, 107, 40, 2.8, 'greenflame')
    p.poly([(80, 24), (84, 6), (90, 18), (100, 2), (110, 18), (116, 6),
            (120, 24)], 'gold', lum=0.65, grad=-0.3)
    p.rect(80, 22, 40, 6, 'gold', lum=0.55)
    for x in (88, 100, 112):
        p.circle(x, 25, 2.2, 'red', lum=0.8)
    p.speckle('ash', 0.08, 0.2)


@picture('rogue')
def _p(p):
    p.poly([(80, 46), (54, 64), (50, 150), (110, 150), (106, 64)], 'black',
           lum=0.5, gradx=-0.3, tex=0.08)
    for s in (-1, 1):
        p.limb(80 + s * 10, 128, 80 + s * 12, 152, 7, 6, 'leather')
        p.ellipse(80 + s * 12, 154, 8, 4, 'leather')
    p.rect(60, 96, 40, 5, 'leather', lum=0.5)
    p.chain([(60, 66), (48, 90), (58, 104)], 8, 6, 'black')
    p.chain([(100, 66), (114, 86), (124, 80)], 8, 6, 'black')
    p.circle(58, 106, 4, 'skin')
    p.line(58, 108, 70, 124, 'steel', 0.85, 2.5)
    p.circle(124, 78, 4, 'skin')
    p.line(124, 76, 136, 58, 'steel', 0.85, 2.5)
    p.ellipse(80, 40, 18, 21, 'black')
    p.ellipse(80, 44, 11, 13, 'skin', bias=-0.25)
    p.rect(68, 46, 24, 10, 'black', lum=0.35)
    eye(p, 75, 41, 1.6, 'eyegold')
    eye(p, 85, 41, 1.6, 'eyegold')


# --------------------------------------------------------------- people

def person(p, skin='skin', hair='hair', robe='blue', trim='gold', beard=None,
           hood=False, bald=False, apron=None, hat=None, eyes='blue',
           long_hair=False, mustache=False, seed=0):
    """A townsperson from the waist up, seen across a counter."""
    p.poly([(30, 160), (40, 112), (60, 100), (100, 100), (120, 112),
            (130, 160)], robe, lum=0.55, gradx=-0.3, tex=0.06)
    p.ellipse(80, 106, 30, 10, robe, bias=0.05)
    if apron:
        p.poly([(56, 112), (104, 112), (108, 160), (52, 160)], apron,
               lum=0.6, gradx=-0.3)
        p.line(60, 112, 70, 100, apron, 0.5, 2)
        p.line(100, 112, 90, 100, apron, 0.5, 2)
    if trim:
        p.line(80, 100, 80, 160, trim, 0.6, 2)
    if long_hair:
        p.ellipse(80, 72, 30, 40, hair, tex=0.2)
    if hood:
        p.ellipse(80, 64, 32, 36, robe, bias=-0.05)
    p.limb(80, 84, 80, 102, 9, 10, skin)
    p.ellipse(80, 64, 21, 26, skin, tex=0.05)
    p.ellipse(59, 66, 4, 7, skin)
    p.ellipse(101, 66, 4, 7, skin)
    if hood:
        p.poly([(56, 44), (80, 30), (104, 44), (102, 52), (80, 42),
                (58, 52)], robe, lum=0.55)
    elif not bald:
        p.ellipse(80, 46, 22, 12, hair, tex=0.25)
        p.ellipse(60, 56, 5, 12, hair, tex=0.2)
        p.ellipse(100, 56, 5, 12, hair, tex=0.2)
    for s in (-1, 1):
        p.ellipse(80 + s * 8, 62, 4, 2.5, 'white', lum=0.9)
        p.circle(80 + s * 8, 62, 1.8, eyes, lum=0.45)
        p.line(80 + s * 4, 57, 80 + s * 12, 56, hair if not bald else skin,
               0.3, 1.5)
    p.limb(80, 62, 78, 72, 2.4, 3.2, skin, bias=-0.05)
    p.line(73, 79, 87, 79, 'mouth', 0.4, 1.5)
    if mustache:
        p.poly([(70, 78), (80, 74), (90, 78), (88, 80), (80, 77), (72, 80)],
               beard or hair, lum=0.5)
    if beard:
        p.poly([(62, 72), (98, 72), (94, 92), (80, 104), (66, 92)], beard,
               lum=0.55, gradx=-0.3, tex=0.15)
        p.line(73, 80, 87, 80, 'mouth', 0.3, 1.5)
    if hat == 'mitre':
        p.poly([(64, 46), (80, 14), (96, 46)], 'white', lum=0.75, gradx=-0.3)
        p.line(80, 20, 80, 44, 'gold', 0.7, 2)
    elif hat == 'wizard':
        p.poly([(52, 46), (108, 46), (90, 8), (70, -4)], robe, lum=0.55,
               gradx=-0.3)
        p.ellipse(80, 46, 30, 6, robe, bias=0.05)


@picture('innkeeper')
def _p(p):
    person(p, robe='wood', trim=None, apron='white', bald=True,
           mustache=True, beard=None, hair='hair')
    p.rect(104, 120, 16, 22, 'wood', lum=0.6, gradx=-0.4)
    p.ellipse(112, 120, 8, 3, 'white', lum=0.9)


@picture('priestess')
def _p(p):
    person(p, robe='white', trim='gold', hood=True, eyes='leaf')
    p.circle(80, 122, 7, 'gold')
    p.rect(79, 112, 2, 20, 'gold', lum=0.8)


@picture('smith')
def _p(p):
    person(p, skin='darkskin', robe='cloth', trim=None, apron='leather',
           hair='hair', beard='hair', bald=True)
    p.line(118, 160, 126, 110, 'wood', 0.55, 4)
    p.rect(116, 100, 22, 12, 'iron', lum=0.6, grad=-0.3)


@picture('guildmaster')
def _p(p):
    person(p, robe='blue', trim='gold', hair='greyhair', beard='greyhair',
           eyes='blue')
    p.rect(52, 116, 56, 6, 'gold', lum=0.6)


@picture('sage')
def _p(p):
    person(p, robe='purple', trim='gold', hair='greyhair', beard='white',
           hat='wizard', eyes='blue')
    p.circle(122, 120, 9, 'glass', lum=0.75)
    p.circle(119, 117, 3, 'white', lum=1.0)


def standing(p, cx, robe, skin='skin', hair='hair', hood=False, beard=None,
             staff=False, apron=None):
    """A whole person, standing, for the view (as a sprite)."""
    p.poly([(cx - 10, 40), (cx + 10, 40), (cx + 16, 118), (cx - 16, 118)],
           robe, lum=0.55, gradx=-0.35, tex=0.06)
    if apron:
        p.poly([(cx - 8, 56), (cx + 8, 56), (cx + 11, 104), (cx - 11, 104)],
               apron, lum=0.6)
    for s in (-1, 1):
        p.ellipse(cx + s * 7, 120, 7, 3, 'leather', lum=0.4)
        p.limb(cx + s * 12, 44, cx + s * 16, 76, 4.5, 4, robe)
        p.circle(cx + s * 16, 79, 3.5, skin)
    if staff:
        p.line(cx + 19, 30, cx + 19, 122, 'wood', 0.55, 2.5)
    p.ellipse(cx, 28, 9, 11, skin, tex=0.05)
    if hood:
        p.ellipse(cx, 25, 11, 12, robe, bias=0.05)
        p.ellipse(cx, 30, 7, 8, skin, bias=-0.15)
    else:
        p.ellipse(cx, 19, 9, 5, hair, tex=0.2)
    if beard:
        p.poly([(cx - 7, 31), (cx + 7, 31), (cx + 4, 44), (cx - 4, 44)],
               beard, lum=0.6)
    for s in (-1, 1):
        p.circle(cx + s * 3.5, 27, 1.1, 'black', lum=0.1)


# ----------------------------------------------------- things in squares

@picture('chest', 64, 48, height=0.26)
def _p(p):
    p.rect(6, 20, 52, 26, 'wood', lum=0.55, gradx=-0.3, tex=0.1)
    p.ellipse(32, 20, 26, 12, 'wood', bias=0.05)
    p.rect(6, 19, 52, 3, 'wood', lum=0.3)
    for x in (10, 52):
        p.rect(x - 2, 10, 5, 36, 'iron', lum=0.55, gradx=-0.4)
    p.rect(27, 22, 10, 10, 'gold', lum=0.65, grad=-0.3)
    p.rect(31, 26, 2, 4, 'shadow', lum=0.0)


@picture('chest_open', 64, 48, height=0.26)
def _p(p):
    p.poly([(8, 6), (56, 6), (58, 20), (6, 20)], 'wood', lum=0.35)
    p.rect(6, 20, 52, 26, 'wood', lum=0.55, gradx=-0.3, tex=0.1)
    p.rect(9, 18, 46, 6, 'shadow', lum=0.05)
    for x in (10, 52):
        p.rect(x - 2, 18, 5, 28, 'iron', lum=0.55, gradx=-0.4)


@picture('fountain', 96, 96, height=0.62)
def _p(p):
    p.ellipse(48, 80, 44, 12, 'stone', bias=-0.05)
    p.rect(4, 66, 88, 16, 'stone', lum=0.55, gradx=-0.4)
    p.ellipse(48, 66, 44, 11, 'stone', bias=0.1)
    p.ellipse(48, 66, 38, 8, 'water', lum=0.55, tex=0.1)
    p.rect(42, 26, 12, 40, 'stone', lum=0.6, gradx=-0.4)
    p.ellipse(48, 28, 16, 6, 'stone', bias=0.1)
    p.ellipse(48, 27, 12, 4, 'water', lum=0.6)
    for s in (-1, 1):
        p.chain([(48, 20), (48 + s * 14, 18), (48 + s * 26, 40),
                 (48 + s * 30, 64)], 2.5, 1.5, 'water', lum=0.85)
    p.ellipse(48, 14, 4, 8, 'water', lum=0.9)


@picture('stairs_up', 96, 96, height=0.84)
def _p(p):
    p.rect(8, 0, 80, 96, 'shadow', lum=0.1)
    for i in range(8):
        y = 92 - i * 11
        w = 80 - i * 6
        p.rect(48 - w / 2, y - 6, w, 6, 'stone', lum=0.75 - i * 0.07)
        p.rect(48 - w / 2, y, w, 5, 'stone', lum=0.45 - i * 0.05)
    p.rect(4, 0, 6, 96, 'stone', lum=0.55, gradx=-0.4)
    p.rect(86, 0, 6, 96, 'stone', lum=0.4, gradx=-0.4)


@picture('statue', 80, 128, height=0.8)
def _p(p):
    p.rect(14, 104, 52, 24, 'stone', lum=0.5, gradx=-0.4)
    p.rect(10, 100, 60, 6, 'stone', lum=0.7)
    for s in (-1, 1):
        p.limb(40 + s * 7, 76, 40 + s * 8, 100, 6, 5, 'stone')
    p.poly([(28, 36), (52, 36), (54, 80), (26, 80)], 'stone', lum=0.6,
           gradx=-0.4)
    for s in (-1, 1):
        p.ellipse(40 + s * 14, 38, 8, 6, 'stone')
    p.limb(26, 40, 22, 64, 5, 4, 'stone')
    p.limb(54, 40, 58, 60, 5, 4, 'stone')
    p.line(58, 62, 60, 102, 'stone', 0.75, 4)
    p.line(50, 62, 66, 62, 'stone', 0.7, 3)
    p.ellipse(40, 24, 9, 11, 'stone', bias=0.05)
    p.rect(32, 24, 16, 2, 'stone', lum=0.2)
    p.speckle('stone', 0.15, 0.12)


@picture('brazier', 64, 80, height=0.5)
def _p(p):
    for s in (-1, 0, 1):
        p.line(32 + s * 4, 46, 32 + s * 18, 80, 'iron', 0.5, 3)
    p.ellipse(32, 44, 22, 9, 'iron', bias=0.05)
    p.ellipse(32, 40, 20, 5, 'ember', lum=0.6, tex=0.3)
    p.ellipse(32, 26, 14, 18, 'flame', lum=0.55)
    p.ellipse(32, 30, 9, 12, 'flame', lum=0.8)
    p.ellipse(32, 34, 4, 6, 'flame', lum=1.0)


@picture('altar', 96, 64, height=0.36)
def _p(p):
    p.rect(8, 22, 80, 42, 'stone', lum=0.55, gradx=-0.4, tex=0.08)
    p.rect(4, 16, 88, 8, 'stone', lum=0.75)
    p.poly([(30, 16), (66, 16), (70, 48), (26, 48)], 'crimson', lum=0.5)
    p.circle(48, 34, 6, 'gold')
    for x in (14, 82):
        p.rect(x - 3, 2, 6, 14, 'white', lum=0.8)
        p.ellipse(x, 0, 2, 3, 'flame', lum=0.9)


@picture('bones', 80, 40, height=0.2)
def _p(p):
    p.limb(8, 34, 50, 30, 3, 3, 'bone')
    p.limb(30, 38, 72, 32, 3, 3, 'bone', bias=-0.1)
    for (x, y) in ((8, 34), (50, 30), (30, 38), (72, 32)):
        p.circle(x, y, 4, 'bone')
    p.chain([(40, 26), (52, 22), (60, 26)], 2.2, 2, 'bone')
    skull(p, 26, 20, 10)


@picture('tree', 128, 160, height=1.4)
def _p(p):
    p.limb(64, 160, 64, 90, 9, 6, 'wood', tex=0.2)
    p.limb(64, 110, 40, 80, 4, 2, 'wood')
    p.limb(64, 100, 92, 74, 4, 2, 'wood')
    blobs = [(64, 50, 40, 36), (36, 70, 28, 24), (92, 66, 30, 26),
             (64, 80, 34, 20), (50, 34, 24, 20), (80, 30, 24, 22)]
    for (x, y, rx, ry) in blobs:
        p.ellipse(x, y, rx, ry, 'leaf', tex=0.3)
    p.speckle('leaf', 0.25, 0.18)


@picture('lamppost', 48, 160, height=1.1)
def _p(p):
    p.rect(21, 40, 6, 116, 'iron', lum=0.5, gradx=-0.4)
    p.rect(15, 152, 18, 8, 'iron', lum=0.5)
    p.rect(12, 14, 24, 28, 'glass', lum=0.85)
    p.ellipse(24, 28, 7, 10, 'flame', lum=0.85)
    p.poly([(8, 14), (24, 2), (40, 14)], 'iron', lum=0.55)
    p.rect(10, 40, 28, 4, 'iron', lum=0.5)


@picture('portal', 96, 128, height=0.84)
def _p(p):
    for i in range(10):
        r = 44 - i * 4
        p.ellipse(48, 64, r, r * 1.3, 'violetglow', lum=0.25 + i * 0.08,
                  tex=0.15)
    p.ellipse(48, 64, 6, 8, 'white', lum=1.0)


@picture('throne', 120, 140, height=0.84)
def _p(p):
    p.rect(10, 10, 100, 130, 'stone', lum=0.35, gradx=-0.3)
    for x in (10, 100):
        p.rect(x, 0, 10, 140, 'stone', lum=0.45, gradx=-0.4)
        p.circle(x + 5, 4, 7, 'gold')
    p.rect(26, 80, 68, 16, 'black', lum=0.45)
    p.poly([(30, 30), (90, 30), (94, 80), (26, 80)], 'black', lum=0.4)
    p.rect(20, 96, 80, 44, 'stone', lum=0.45, gradx=-0.3)


# --------------------------------------------------------------- the frame

@picture('ornament', 40, 36)
def _p(p):
    skull(p, 20, 15, 13)


@picture('icon', 64, 64)
def _p(p):
    p.rect(2, 2, 60, 60, 'black', lum=0.4)
    p.ellipse(32, 30, 22, 24, 'shadow', lum=0.15)
    skull(p, 32, 26, 16)
    eye(p, 26, 28, 3, 'eyegreen')
    eye(p, 38, 28, 3, 'eyegreen')
    p.material('greenflame', *GREENFLAME, glow=True)
    p.line(8, 60, 56, 60, 'gold', 0.6, 3)


def stone_panel(w, h, seed, base='#8e8c88', mortar='#4a4844', bands=None):
    """Bytes of a w x h panel of stone, tiled from a texture."""
    rng = random.Random(seed)
    tex = textures.stone_wall(seed, base, mortar, bands or [18, 22, 24],
                              18, 36, jitter=0.08, noise=0.3)
    T = textures.T
    out = bytearray()
    for y in range(h):
        for x in range(w):
            out += bytes(tex[(y % T) * T + (x % T)])
    return bytes(out)


def texture_panel(w, h, name, shade=1.0):
    """Bytes of a w x h panel tiled from a texture."""
    tex = textures.get(name)
    T = textures.T
    out = bytearray()
    for y in range(h):
        for x in range(w):
            out += bytes(scale(tex[(y % T) * T + (x % T)], shade))
    return bytes(out)


def parchment(w, h, seed=5, base='#e2c894', edge='#9a6a30'):
    rng = random.Random(seed)
    n = textures.fbm(rng)
    T = textures.T
    base = rgb(base)
    edge = rgb(edge)
    px = []
    for y in range(h):
        for x in range(w):
            v = n[(y % T) * T + (x % T)]
            d = min(x, w - 1 - x, y, h - 1 - y)
            e = max(0.0, 1 - d / 14.0)
            c = scale(base, 0.88 + 0.2 * v)
            c = mix(c, edge, e * e * 0.85)
            px.append(c)
    return px


def scroll_roll(w, h, lo='#6a3e14', hi='#e8b858'):
    """Pixels of the wooden roller at the top or bottom of a scroll."""
    px = []
    lo, hi = rgb(lo), rgb(hi)
    for y in range(h):
        t = 1 - abs((y + 0.5) / h * 2 - 1)
        for x in range(w):
            k = t ** 0.7
            c = mix(lo, hi, k * 0.85)
            if x < 6 or x >= w - 6:
                c = scale(c, 0.7)
            px.append(c)
    return px

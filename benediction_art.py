"""The pictures and textures of Benediction: the strike ship Unbending
Vow, the wreck's cargo decks, its cathedral, the Brood's hive, the Brood
itself, and the crew of the Vow.  Importing this module registers them
with the engine."""

import math
import random

from blobber import textures as tx
from blobber.textures import (texture, T, fbm, overlay, glow_at,
                              plates, stripes, light_strip)
from blobber.art import picture, eye, skull, person, standing
from blobber.paint import Painter
from blobber.gfx import rgb, mix, scale

IRON = ('#14161a', '#2c3038', '#474c56', '#686e7a', '#9298a4', '#c8ccd4')
REDTRIM = ('#2a0606', '#5a0c0c', '#8c1a14', '#c02c20', '#e8603c')
BRASS = ('#2a1a08', '#5a3c10', '#8c6420', '#c09838', '#ecd070', '#fff4c0')
CHITIN = ('#0e0a14', '#241830', '#3e2a50', '#5c4074', '#86629c', '#b896c8')
FLESH = ('#1a0c10', '#3c1a22', '#6a3038', '#9a4e50', '#c87a70', '#ecb0a0')
ACID = ('#0a2a06', '#1e5a0c', '#3c9a18', '#78d830', '#c8ff70', '#f8ffd0')
TEAL = ('#04201e', '#0a4a44', '#14807a', '#30c0b4', '#90f0e4', '#e8fffa')
BONEPLATE = ('#2a2418', '#5a4e38', '#8e8064', '#c0b494', '#e8e0c8')


def mats(p):
    p.material('iron', *IRON)
    p.material('redtrim', *REDTRIM)
    p.material('brass', *BRASS)
    p.material('chitin', *CHITIN)
    p.material('flesh', *FLESH)
    p.material('acid', *ACID, glow=True)
    p.material('teal', *TEAL, glow=True)
    p.material('boneplate', *BONEPLATE)


def P(seed=1):
    p = Painter(T, T, seed)
    mats(p)
    return p


# ------------------------------------------------------------ metal walls

# -------------------------------------------------------- the Unbending Vow

def _vow():
    px = plates(101, '#4a5260', '#14181e', cols=(32, 32), rows=(40, 24))
    for x in range(T):
        for y in (40, 41, 42):
            px[y * T + x] = rgb('#b08a30') if y == 41 else rgb('#5a4418')
    light_strip(px, 52, '#ffb860', 10, 54)
    return px


@texture('vow_wall')
def _t():
    return _vow()


@texture('vow_port')
def _t():
    px = _vow()
    rng = random.Random(4)
    for y in range(6, 36):
        for x in range(10, 54):
            dx = min(x - 10, 53 - x)
            dy = min(y - 6, 35 - y)
            if dx < 4 and dy < 4 and (4 - dx) ** 2 + (4 - dy) ** 2 > 16:
                continue
            if dx < 2 or dy < 2:
                px[y * T + x] = rgb('#202630')
                continue
            c = rgb('#02030a')
            d = math.hypot(x - 60, y - 40)
            if d < 22:
                c = mix(rgb('#3a6a9a'), rgb('#0a1428'), max(0, (d - 12) / 10))
            elif rng.random() < 0.05:
                c = rgb(rng.choice(['#ffffff', '#c8d8ff', '#ffe8c0']))
            px[y * T + x] = c
    return px


@texture('vow_banner')
def _t():
    return tx.banner(_vow(), 'crimson', 'gold')


def emblem(p, cx, cy, r, m='brass'):
    """The Order of the Iron Vigil: a sword before a rayed sun."""
    for a in range(12):
        ang = a * math.pi / 6
        p.line(cx + r * 0.7 * math.cos(ang), cy + r * 0.7 * math.sin(ang),
               cx + r * math.cos(ang), cy + r * math.sin(ang), m, 0.8, 1.5)
    p.circle(cx, cy, r * 0.62, m)
    p.circle(cx, cy, r * 0.45, 'redtrim', lum=0.45)
    p.line(cx, cy - r * 0.95, cx, cy + r * 0.95, 'steel', 0.85, 2)
    p.line(cx - r * 0.35, cy + r * 0.35, cx + r * 0.35, cy + r * 0.35,
           m, 0.7, 2)


@texture('vow_icon')
def _t():
    px = _vow()
    p = P(5)
    emblem(p, 32, 20, 14)
    return overlay(px, p)


@texture('vow_floor')
def _t():
    px = plates(102, '#3a3e46', '#101216', cols=(32, 32), rows=(32, 32),
                rivets=False)
    for y in range(T):
        for x in range(T):
            if (x % 8 == 3 and y % 8 in (2, 3, 4)) or \
                    (y % 8 == 3 and x % 8 in (2, 3, 4)):
                px[y * T + x] = scale(px[y * T + x], 1.25)
    return px


@texture('vow_ceil')
def _t():
    px = plates(103, '#30343c', '#0c0e12', cols=(64,), rows=(32, 32))
    for y in range(26, 38):
        for x in range(20, 44):
            px[y * T + x] = rgb('#fff0d0') if 28 <= y < 36 and 22 <= x < 42 \
                else rgb('#5a5a50')
    return px


def bulkhead_door(px, colour='#606a78', light='#40ff60', hazard=True,
                  locked=False, seed=6):
    p = P(seed)
    p.rect(8, 6, 48, 58, 'iron', lum=0.25)
    p.rect(12, 10, 19, 54, 'iron', lum=0.6, gradx=-0.3, tex=0.08)
    p.rect(33, 10, 19, 54, 'iron', lum=0.55, gradx=-0.3, tex=0.08)
    p.rect(31, 10, 2, 54, 'shadow', lum=0.0)
    if hazard:
        for k in range(6):
            y = 40 + k * 4
            p.poly([(12, y), (31, y - 8), (31, y - 5), (12, y + 3)],
                   'gold', lum=0.65)
            p.poly([(33, y - 8), (52, y), (52, y + 3), (33, y - 5)],
                   'gold', lum=0.65)
    p.rect(26, 16, 12, 8, 'iron', lum=0.35)
    p.circle(32, 20, 2.5, 'eyegreen' if not locked else 'eyered', lum=0.9)
    if locked:
        p.rect(14, 30, 36, 5, 'iron', lum=0.75, grad=0.4)
        p.rect(28, 28, 8, 9, 'redtrim', lum=0.6)
    out = overlay(px, p)
    glow_at(out, 32, 20, 10, '#ff3020' if locked else light, 0.35)
    return out


@texture('vow_door')
def _t():
    return bulkhead_door(_vow(), hazard=False)


def plaque(px, icon, colour='black', seed=7):
    p = P(seed)
    p.rect(40, 6, 20, 16, colour, lum=0.5, grad=-0.3)
    p.rect(40, 6, 20, 1, 'brass', lum=0.75)
    p.rect(40, 21, 20, 1, 'brass', lum=0.45)
    icon(p, 50, 14)
    return overlay(px, p)


def _icon_command(p, x, y):
    emblem(p, x, y, 6)


def _icon_rifles(p, x, y):
    p.line(x - 7, y + 5, x + 7, y - 5, 'steel', 0.8, 2)
    p.line(x + 7, y + 5, x - 7, y - 5, 'steel', 0.8, 2)
    p.rect(x - 2, y - 2, 4, 4, 'brass', lum=0.7)


def _icon_vial(p, x, y):
    p.rect(x - 2, y - 7, 4, 3, 'white', lum=0.9)
    p.ellipse(x, y + 2, 5, 6, 'glass', lum=0.7)
    p.ellipse(x, y + 4, 4, 3, 'eyegreen', lum=0.7)


def _icon_cup(p, x, y):
    p.poly([(x - 6, y - 5), (x + 6, y - 5), (x + 3, y + 3), (x - 3, y + 3)],
           'brass', lum=0.7, gradx=-0.4)
    p.rect(x - 1, y + 3, 2, 3, 'brass', lum=0.6)
    p.rect(x - 4, y + 6, 8, 2, 'brass', lum=0.6)


def _icon_book(p, x, y):
    p.poly([(x - 8, y - 5), (x, y - 3), (x, y + 6), (x - 8, y + 4)], 'white',
           lum=0.85)
    p.poly([(x + 8, y - 5), (x, y - 3), (x, y + 6), (x + 8, y + 4)], 'white',
           lum=0.7)
    for k in range(3):
        p.line(x - 6, y - 2 + k * 2, x - 2, y - 1 + k * 2, 'black', 0.3, 0.7)


def _facade(icon, colour, seed):
    return plaque(bulkhead_door(_vow(), hazard=False, seed=seed), icon,
                  colour, seed)


@texture('vow_command')
def _t():
    return _facade(_icon_command, 'redtrim', 11)


@texture('vow_armoury')
def _t():
    return _facade(_icon_rifles, 'black', 12)


@texture('vow_infirmary')
def _t():
    return _facade(_icon_vial, 'white', 13)


@texture('vow_barracks')
def _t():
    return _facade(_icon_cup, 'crimson', 14)


@texture('vow_archive')
def _t():
    return _facade(_icon_book, 'purple', 15)


@texture('vow_airlock')
def _t():
    px = _vow()
    stripes(px, 0, 6)
    stripes(px, 58, 64)
    p = P(16)
    p.circle(32, 32, 24, 'iron', bias=0.05)
    p.circle(32, 32, 19, 'iron', lum=0.4)
    for a in range(8):
        ang = a * math.pi / 4 + 0.3
        p.poly([(32, 32), (32 + 19 * math.cos(ang), 32 + 19 * math.sin(ang)),
                (32 + 19 * math.cos(ang + 0.6), 32 + 19 * math.sin(ang + 0.6))],
               'iron', lum=0.45 + 0.05 * (a % 2))
    p.circle(32, 32, 4, 'iron', lum=0.7)
    p.circle(32, 6, 2.5, 'eyered', lum=0.9)
    out = overlay(px, p)
    glow_at(out, 32, 6, 8, '#ff3020', 0.4)
    return out


# ----------------------------------------------------- the wreck: cargo decks

def _wreck(seed=201):
    return plates(seed, '#5a5248', '#16120e', cols=(20, 24, 20),
                  rows=(24, 22, 18), grime=0.45, rust='#7a3a18', jitter=0.14)


@texture('wreck_wall')
def _t():
    return _wreck()


@texture('wreck_pipes')
def _t():
    px = _wreck(202)
    p = P(17)
    for x, r in ((14, 4), (24, 3), (46, 5)):
        p.rect(x - r, 0, 2 * r, 64, 'iron', lum=0.55, gradx=-0.7)
        for y in (12, 40):
            p.rect(x - r - 1, y, 2 * r + 2, 4, 'rust', lum=0.5, gradx=-0.6)
    return overlay(px, p)


@texture('wreck_hazard')
def _t():
    return stripes(_wreck(203), 46, 54)


@texture('wreck_console')
def _t():
    px = _wreck(204)
    p = P(18)
    p.rect(12, 14, 40, 30, 'iron', lum=0.35)
    p.rect(15, 17, 34, 20, 'shadow', lum=0.05)
    rng = random.Random(3)
    for k in range(5):
        w = rng.randint(10, 30)
        p.rect(17, 19 + k * 3, w, 1, 'eyegreen', lum=0.7)
    for k in range(4):
        p.circle(19 + k * 8, 41, 1.5, ['eyered', 'eyegold', 'eyegreen',
                                       'eyegold'][k], lum=0.9)
    out = overlay(px, p)
    glow_at(out, 32, 27, 22, '#40ff60', 0.12)
    return out


@texture('wreck_breach')
def _t():
    px = _wreck(205)
    rng = random.Random(5)
    pts = []
    for k in range(18):
        a = k / 18 * math.tau
        r = rng.uniform(12, 22)
        pts.append((32 + r * math.cos(a), 30 + r * 1.1 * math.sin(a)))
    p = P(19)
    p.poly(pts, 'shadow', lum=0.02)
    for (x, y) in pts:
        p.circle(x, y, 1.5, 'iron', lum=0.85)
    out = overlay(px, p)
    for _ in range(12):
        x, y = rng.randint(16, 48), rng.randint(14, 46)
        out[y * T + x] = rgb('#ffd060')
    return out


@texture('wreck_door')
def _t():
    return bulkhead_door(_wreck(206), seed=20)


@texture('wreck_locked')
def _t():
    return bulkhead_door(_wreck(207), locked=True, seed=21)


@texture('grating')
def _t():
    px = []
    rng = random.Random(8)
    for y in range(T):
        for x in range(T):
            bar = (x % 8 in (0, 1)) or (y % 16 in (0, 1, 2))
            if bar:
                f = 0.9 + 0.2 * rng.random()
                c = scale('#5a5650', f * (1.15 if x % 8 == 0 or y % 16 == 0
                                          else 0.85))
            else:
                c = scale('#141210', 0.6 + 0.5 * rng.random())
            px.append(c)
    return px


@texture('wreck_ceil')
def _t():
    px = plates(208, '#3a3630', '#0e0c0a', cols=(64,), rows=(32, 32),
                rust='#5a2a10')
    p = P(22)
    for y, r in ((18, 4), (44, 5)):
        p.rect(0, y - r, 64, 2 * r, 'iron', lum=0.5, grad=-0.7)
    return overlay(px, p)


@texture('lift_floor')
def _t():
    px = list(tx.get('grating'))
    for y in range(8, 56):
        for x in range(8, 56):
            edge = min(x - 8, 55 - x, y - 8, 55 - y)
            if edge < 4:
                px[y * T + x] = rgb('#d8b020') if ((x + y) // 4) % 2 else \
                    rgb('#141414')
            else:
                px[y * T + x] = scale('#4a4e56', 0.8 + 0.1 * ((x // 6 + y // 6) % 2))
    return px


# ---------------------------------------------------- the wreck: the nave

def _nave(seed=301):
    px = tx.stone_wall(seed, '#3e3634', '#120e0c', [16, 16, 16, 16], 16, 28,
                       hue='#4a3a30', noise=0.4)
    p = P(seed)
    # a gilded pointed arch in relief
    for side in (-1, 1):
        pts = [(32 + side * 22, 64), (32 + side * 22, 26)]
        for k in range(9):
            a = k / 8 * (math.pi / 2)
            pts.append((32 + side * 22 * math.cos(a) - side * 0,
                        26 - 22 * math.sin(a) * 0.9))
        for i in range(len(pts) - 1):
            p.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                   'brass', 0.55, 1.6)
    return overlay(px, p)


@texture('nave_wall')
def _t():
    return _nave()


@texture('nave_glass')
def _t():
    px = _nave(302)
    rng = random.Random(9)
    pal = ['#a01818', '#1838a0', '#c89020', '#186030', '#5a1a80']
    for y in range(8, 60):
        for x in range(14, 50):
            dx = abs(x + 0.5 - 32) / 18
            top = 24 - 18 * math.sqrt(max(0, 1 - dx * dx))
            if y < top:
                continue
            cell = (x // 6, y // 7)
            c = pal[(cell[0] * 7 + cell[1] * 3) % len(pal)]
            if x % 6 == 0 or y % 7 == 0:
                c = '#1a1612'
            px[y * T + x] = scale(c, 0.85 + 0.3 * rng.random())
    p = P(23)
    p.circle(32, 22, 6, 'gold', lum=0.9)
    p.ellipse(32, 24, 3.5, 4, 'paleskin', lum=0.75)
    p.poly([(26, 30), (38, 30), (41, 56), (23, 56)], 'white', lum=0.75,
           gradx=-0.3)
    p.ellipse(38, 32, 3, 3, 'flame', lum=0.95)
    out = overlay(px, p)
    glow_at(out, 32, 36, 30, '#ffd090', 0.18)
    return out


@texture('nave_candles')
def _t():
    px = _nave(303)
    p = P(24)
    p.rect(10, 44, 44, 4, 'brass', lum=0.6)
    p.rect(14, 48, 36, 12, 'brass', lum=0.4, gradx=-0.4)
    rng = random.Random(10)
    for k in range(9):
        x = 13 + k * 4.6
        h = rng.randint(6, 14)
        p.rect(x, 44 - h, 2.5, h, 'white', lum=0.85)
        p.ellipse(x + 1.2, 44 - h - 3, 1.4, 2.5, 'flame', lum=0.95)
    out = overlay(px, p)
    glow_at(out, 32, 34, 28, '#ffb050', 0.35)
    return out


@texture('nave_banner')
def _t():
    return tx.banner(_nave(304), 'crimson', 'gold')


@texture('nave_skull')
def _t():
    return tx.skull_niche(_nave(305))


@texture('nave_door')
def _t():
    return tx.door_overlay(_nave(306), 'gold', 'rust')


@texture('nave_locked')
def _t():
    px = tx.door_overlay(_nave(307), 'gold', 'rust')
    p = P(25)
    p.circle(32, 38, 7, 'redtrim', lum=0.6)
    p.circle(32, 38, 4, 'redtrim', lum=0.45)
    p.line(32, 45, 30, 56, 'white', 0.8, 2)
    p.line(34, 45, 36, 55, 'white', 0.75, 2)
    return overlay(px, p)


@texture('nave_floor')
def _t():
    rng = random.Random(11)
    n = fbm(rng)
    px = []
    for y in range(T):
        for x in range(T):
            dark = ((x // 16) + (y // 16)) % 2
            c = '#1e1a1a' if dark else '#8e8478'
            v = n[y * T + x]
            px.append(scale(c, 0.8 + 0.35 * v))
    return tx.cracks(px, 12, 3, '#0a0808')


@texture('nave_ceil')
def _t():
    px = tx.stone_wall(308, '#2a2422', '#0a0808', [32, 32], 24, 40)
    p = P(26)
    p.line(0, 0, 64, 64, 'brass', 0.4, 2)
    p.line(64, 0, 0, 64, 'brass', 0.4, 2)
    return overlay(px, p)


@texture('nave_lift')
def _t():
    px = list(tx.get('nave_floor'))
    lf = tx.get('lift_floor')
    for y in range(8, 56):
        for x in range(8, 56):
            px[y * T + x] = lf[y * T + x]
    return px


# ------------------------------------------------------- the wreck: the hive

def _hive(seed=401):
    rng = random.Random(seed)
    n = fbm(rng, ((4, 0.4), (16, 0.4), (32, 0.2)))
    px = []
    base = rgb('#4a3048')
    for y in range(T):
        for x in range(T):
            rib = math.sin((x + 6 * math.sin(y / 9 + seed)) / 64 * math.tau * 4)
            f = 0.55 + 0.45 * rib + 0.3 * (n[y * T + x] - 0.5)
            c = scale(base, max(0.15, f))
            if rib > 0.85:
                c = mix(c, '#c8a0c0', 0.35)
            px.append(c)
    return px


@texture('hive_wall')
def _t():
    return _hive()


@texture('hive_pods')
def _t():
    px = _hive(402)
    p = P(27)
    rng = random.Random(13)
    for _ in range(7):
        x, y = rng.uniform(10, 54), rng.uniform(10, 54)
        r = rng.uniform(4, 8)
        p.ellipse(x, y, r, r * 1.3, 'teal', lum=0.45)
        p.ellipse(x - r * 0.3, y - r * 0.4, r * 0.35, r * 0.4, 'teal', lum=0.9)
    out = overlay(px, p)
    glow_at(out, 32, 32, 34, '#30c0b4', 0.15)
    return out


@texture('hive_eaten')
def _t():
    px = _wreck(403)
    hv = _hive(404)
    for y in range(T):
        for x in range(T):
            edge = 26 + 10 * math.sin(x / 7.0) + 5 * math.sin(x / 2.3)
            if y > edge:
                px[y * T + x] = hv[y * T + x]
            elif y > edge - 2:
                px[y * T + x] = rgb('#20101e')
    return px


@texture('hive_veins')
def _t():
    return tx.cracks(_hive(405), 14, 5, glow='#40e0d0')


@texture('hive_door')
def _t():
    px = _hive(406)
    p = P(28)
    p.ellipse(32, 34, 24, 28, 'flesh', bias=0.05)
    for a in range(10):
        ang = a * math.tau / 10
        p.line(32, 34, 32 + 22 * math.cos(ang), 34 + 26 * math.sin(ang),
               'flesh', 0.3, 1.5)
    p.ellipse(32, 34, 5, 6, 'shadow', lum=0.0)
    return overlay(px, p)


@texture('hive_locked')
def _t():
    px = _hive(407)
    p = P(29)
    for k in range(5):
        y = 6 + k * 12
        p.ellipse(32, y + 6, 26, 7, 'boneplate', bias=0.1, tex=0.1)
    p.line(32, 4, 32, 62, 'boneplate', 0.3, 2)
    return overlay(px, p)


@texture('hive_floor')
def _t():
    rng = random.Random(14)
    n = fbm(rng, ((8, 0.5), (16, 0.3), (32, 0.2)))
    px = []
    for i in range(T * T):
        v = n[i]
        c = mix('#2a1420', '#7a3a48', v)
        if v > 0.62:
            c = mix(c, '#e8b0c0', (v - 0.62) * 2)
        px.append(c)
    return px


@texture('hive_ceil')
def _t():
    return [scale(c, 0.6) for c in _hive(408)]


# ----------------------------------------------------------------- things

@picture('crate', 80, 64, height=0.36)
def _p(p):
    mats(p)
    p.rect(4, 10, 72, 54, 'leaf', lum=0.45, gradx=-0.4,
           tex=0.08)
    for x in (4, 38, 72):
        p.rect(x, 10, 4, 54, 'iron', lum=0.5)
    p.rect(4, 10, 72, 4, 'iron', lum=0.7)
    p.rect(4, 60, 72, 4, 'iron', lum=0.35)
    p.rect(14, 28, 18, 8, 'gold', lum=0.55)


@picture('console', 64, 96, height=0.62)
def _p(p):
    mats(p)
    p.rect(14, 40, 36, 56, 'iron', lum=0.45, gradx=-0.4)
    p.poly([(6, 10), (58, 10), (52, 44), (12, 44)], 'iron', lum=0.55,
           gradx=-0.4)
    p.rect(14, 16, 36, 22, 'shadow', lum=0.05)
    for k in range(5):
        p.rect(16, 19 + k * 3.5, 8 + (k * 7) % 22, 1.5, 'eyegreen', lum=0.75)
    for k in range(4):
        p.circle(20 + k * 8, 50, 2, ['eyered', 'eyegold', 'eyegreen',
                                     'eyecyan'][k], lum=0.9)


@picture('saint', 80, 140, height=0.84)
def _p(p):
    mats(p)
    p.rect(16, 116, 48, 24, 'stone', lum=0.5, gradx=-0.4)
    p.rect(12, 112, 56, 6, 'brass', lum=0.65)
    p.poly([(40, 30), (24, 44), (18, 112), (62, 112), (56, 44)], 'stone',
           lum=0.62, gradx=-0.4, tex=0.06)
    for x in (28, 40, 52):
        p.line(40 + (x - 40) * 0.3, 50, x, 110, 'stone', 0.4, 1)
    p.ellipse(40, 28, 9, 11, 'stone', bias=0.05)
    p.ellipse(40, 22, 11, 12, 'stone', lum=0.5)
    p.chain([(54, 46), (64, 34), (66, 20)], 4, 3.5, 'stone')
    p.ellipse(66, 14, 5, 9, 'flame', lum=0.6)
    p.ellipse(66, 16, 3, 5, 'flame', lum=0.9)
    for a in range(9):
        ang = math.pi + a * math.pi / 8
        p.line(40 + 14 * math.cos(ang), 26 + 14 * math.sin(ang),
               40 + 18 * math.cos(ang), 26 + 18 * math.sin(ang), 'gold', 0.85,
               1.5)


@picture('pods', 96, 72, height=0.42)
def _p(p):
    mats(p)
    for (x, y, r) in ((24, 46, 16), (52, 40, 20), (76, 50, 14), (40, 58, 12)):
        p.ellipse(x, y, r * 0.85, r, 'flesh', tex=0.1)
        p.ellipse(x - r * 0.25, y - r * 0.3, r * 0.3, r * 0.4, 'teal',
                  lum=0.8)
    p.ellipse(48, 68, 46, 6, 'flesh', lum=0.3)


@picture('fallen', 96, 56, height=0.3)
def _p(p):
    mats(p)
    p.ellipse(48, 40, 34, 13, 'iron', tex=0.1)
    p.ellipse(22, 34, 13, 10, 'iron', bias=0.1)
    p.ellipse(72, 30, 12, 10, 'redtrim')
    p.circle(70, 30, 4, 'brass', lum=0.65)
    p.ellipse(16, 30, 9, 8, 'iron', bias=0.05)
    p.rect(10, 28, 12, 3, 'eyered', lum=0.3)
    p.line(50, 30, 92, 18, 'iron', 0.45, 4)
    p.ellipse(56, 50, 28, 4, 'crimson', lum=0.35)


@picture('lift', 96, 112, height=0.84)
def _p(p):
    mats(p)
    p.rect(6, 0, 84, 112, 'shadow', lum=0.08)
    p.rect(6, 0, 8, 112, 'iron', lum=0.55, gradx=-0.5)
    p.rect(82, 0, 8, 112, 'iron', lum=0.4, gradx=-0.5)
    for y in range(4, 108, 10):
        p.rect(14, y, 68, 2, 'iron', lum=0.25)
    p.rect(14, 96, 68, 10, 'gold', lum=0.6)
    for k in range(9):
        p.poly([(14 + k * 8, 96), (18 + k * 8, 96), (14 + k * 8, 106)],
               'black', lum=0.2)
    p.circle(48, 12, 3, 'eyegreen', lum=0.9)


@picture('reliquary', 96, 72, height=0.4)
def _p(p):
    mats(p)
    p.rect(8, 34, 80, 38, 'stone', lum=0.5, gradx=-0.4)
    p.rect(4, 30, 88, 6, 'brass', lum=0.7)
    p.rect(30, 8, 36, 24, 'brass', lum=0.65, gradx=-0.4, tex=0.05)
    p.poly([(28, 8), (48, 0), (68, 8)], 'brass', lum=0.75)
    p.rect(44, 12, 8, 14, 'redtrim', lum=0.6)
    for x in (16, 80):
        p.rect(x - 2, 14, 4, 16, 'white', lum=0.85)
        p.ellipse(x, 11, 1.6, 3, 'flame', lum=0.95)


@picture('medstation', 64, 96, height=0.62)
def _p(p):
    mats(p)
    p.rect(8, 8, 48, 80, 'white', lum=0.65, gradx=-0.4)
    p.rect(14, 16, 36, 28, 'glass', lum=0.55)
    p.rect(28, 50, 8, 22, 'eyegreen', lum=0.7)
    p.rect(21, 57, 22, 8, 'eyegreen', lum=0.7)
    p.rect(8, 88, 48, 8, 'iron', lum=0.4)


@picture('conduit', 64, 112, height=0.8)
def _p(p):
    mats(p)
    p.rect(20, 0, 24, 112, 'iron', lum=0.45, gradx=-0.6)
    for y in range(10, 104, 18):
        p.ellipse(32, y, 14, 6, 'brass', bias=0.05)
    p.rect(26, 20, 12, 70, 'violetglow', lum=0.6)
    p.rect(30, 24, 4, 62, 'violetglow', lum=0.95)


# -------------------------------------------------------------- the Brood

@picture('broodling', 140, 100)
def _p(p):
    mats(p)
    for s in (-1, 1):
        for i in range(3):
            bx, by = 70 + s * 14, 62 + i * 6
            kx, ky = 70 + s * (34 + i * 10), 46 + i * 8
            p.limb(bx, by, kx, ky, 3.5, 3, 'chitin')
            p.limb(kx, ky, 70 + s * (44 + i * 12), 96, 3, 1, 'chitin')
    p.ellipse(70, 64, 26, 18, 'chitin', tex=0.12)
    for k in range(4):
        p.line(48 + k * 12, 52, 52 + k * 12, 76, 'chitin', 0.35, 1.5)
    p.ellipse(70, 50, 15, 12, 'flesh', tex=0.1)
    for (x, y) in ((62, 46), (70, 44), (78, 46)):
        eye(p, x, y, 2.4, 'eyegold')
    p.chain([(62, 58), (56, 68), (60, 74)], 3, 1, 'bone')
    p.chain([(78, 58), (84, 68), (80, 74)], 3, 1, 'bone')


@picture('thrall', 160, 160)
def _p(p):
    mats(p)
    for s in (-1, 1):
        p.limb(80 + s * 12, 108, 80 + s * 14, 132, 9, 8, 'cloth', tex=0.15)
        p.limb(80 + s * 14, 132, 80 + s * 13, 150, 8, 7, 'iron')
        p.ellipse(80 + s * 14, 153, 10, 4.5, 'iron')
    p.poly([(56, 50), (104, 50), (108, 112), (52, 112)], 'cloth', lum=0.5,
           gradx=-0.3, tex=0.12)
    p.rect(56, 60, 48, 6, 'gold', lum=0.4)
    p.ellipse(92, 76, 14, 18, 'chitin', tex=0.1)
    for k in range(3):
        p.circle(88 + k * 5, 70 + k * 6, 3, 'teal', lum=0.7)
    p.chain([(58, 54), (48, 76), (52, 98)], 7, 6, 'paleskin')
    p.chain([(102, 54), (120, 66), (132, 60)], 8, 6, 'chitin')
    p.chain([(132, 60), (146, 46), (150, 30)], 5, 1.5, 'bone')
    p.circle(52, 100, 6, 'paleskin')
    p.limb(80, 46, 80, 54, 6, 6, 'paleskin')
    p.ellipse(80, 34, 16, 18, 'paleskin', tex=0.12)
    p.ellipse(88, 26, 9, 10, 'chitin', tex=0.1)
    eye(p, 73, 34, 2.6, 'teal')
    eye(p, 86, 36, 2, 'teal')
    p.ellipse(78, 45, 6, 3, 'mouth', lum=0.3)
    p.ellipse(70, 22, 10, 5, 'hair', tex=0.3)


@picture('sentinel', 160, 160)
def _p(p):
    mats(p)
    p.rect(40, 128, 80, 26, 'iron', lum=0.4, gradx=-0.4)
    for x in range(44, 120, 10):
        p.circle(x, 141, 5, 'iron', lum=0.6)
    p.rect(66, 96, 28, 34, 'iron', lum=0.5, gradx=-0.4)
    p.ellipse(80, 70, 36, 32, 'iron', tex=0.06)
    p.rect(44, 66, 72, 8, 'gold', lum=0.5)
    for s in (-1, 1):
        p.rect(80 + s * 48 - 12, 54, 24, 28, 'iron', lum=0.55, gradx=-0.4)
        for k in range(3):
            p.line(80 + s * 48 - 6 + k * 6, 82, 80 + s * 48 - 6 + k * 6, 104,
                   'steel', 0.7, 3)
    p.ellipse(80, 54, 18, 12, 'iron', bias=0.1)
    p.rect(66, 50, 28, 6, 'shadow', lum=0.0)
    eye(p, 80, 53, 3.5, 'eyered')
    p.line(80, 40, 80, 26, 'iron', 0.5, 2)
    p.circle(80, 25, 3, 'eyered', lum=0.9)


@picture('choir', 160, 160)
def _p(p):
    mats(p)
    p.poly([(80, 40), (54, 62), (42, 156), (118, 156), (106, 62)], 'purple',
           lum=0.45, gradx=-0.35, tex=0.06)
    for x in (58, 70, 80, 92, 104):
        p.line(80 + (x - 80) * 0.3, 70, x, 154, 'purple', 0.25, 1.2)
    p.chain([(60, 66), (64, 92), (80, 100)], 9, 7, 'purple')
    p.chain([(100, 66), (104, 88), (96, 100)], 9, 7, 'purple')
    p.rect(60, 94, 64, 8, 'iron', lum=0.55, gradx=0.3)
    p.rect(118, 92, 20, 5, 'iron', lum=0.7)
    p.rect(74, 100, 8, 14, 'iron', lum=0.45)
    p.circle(80, 100, 5, 'paleskin')
    p.ellipse(80, 40, 20, 23, 'purple', bias=0.05)
    p.ellipse(80, 46, 12, 14, 'paleskin', bias=-0.2)
    p.ellipse(80, 38, 12, 7, 'chitin', tex=0.1)
    eye(p, 74, 46, 2.2, 'teal')
    eye(p, 86, 46, 2.2, 'teal')
    p.line(74, 54, 86, 54, 'mouth', 0.3, 1.5)


@picture('stalker', 160, 160)
def _p(p):
    mats(p)
    p.chain([(96, 120), (124, 132), (146, 116), (152, 92)], 6, 2, 'chitin')
    p.poly([(150, 92), (158, 80), (156, 98)], 'bone', lum=0.7)
    for s in (-1, 1):
        p.chain([(80 + s * 10, 112), (80 + s * 26, 128), (80 + s * 18, 154)],
                7, 4, 'chitin', tex=0.1)
        p.chain([(80 + s * 18, 154), (80 + s * 28, 156)], 3, 2, 'bone')
    p.ellipse(82, 96, 22, 26, 'chitin', tex=0.12, angle=0.2)
    for k in range(4):
        p.ellipse(80, 82 + k * 9, 14 - k, 4, 'chitin', bias=0.15)
    for s in (-1, 1):
        p.chain([(80 + s * 16, 76), (80 + s * 44, 62), (80 + s * 52, 90)],
                6, 4, 'chitin')
        p.chain([(80 + s * 52, 90), (80 + s * 46, 120)], 3.5, 0.8, 'bone')
        p.chain([(80 + s * 14, 90), (80 + s * 30, 100), (80 + s * 26, 112)],
                4, 2.5, 'chitin')
    p.ellipse(80, 52, 20, 18, 'chitin', tex=0.1)
    p.poly([(64, 46), (80, 14), (96, 46)], 'chitin', lum=0.5, gradx=-0.3)
    p.poly([(68, 40), (80, 22), (92, 40)], 'flesh', lum=0.45)
    p.ellipse(80, 64, 12, 7, 'mouth', lum=0.35)
    for k in range(-3, 4):
        p.poly([(80 + k * 3 - 1, 60), (80 + k * 3 + 1, 60), (80 + k * 3, 66)],
               'teeth', lum=0.9)
    eye(p, 70, 52, 2.5, 'eyegold')
    eye(p, 90, 52, 2.5, 'eyegold')


@picture('spitter', 160, 160)
def _p(p):
    mats(p)
    for s in (-1, 1):
        for i in range(2):
            p.chain([(80 + s * 20, 120 + i * 6), (80 + s * (40 + i * 10), 128),
                     (80 + s * (44 + i * 12), 154)], 5, 2, 'chitin')
    p.ellipse(80, 108, 40, 32, 'flesh', tex=0.1)
    for (x, y, r) in ((60, 100, 10), (96, 96, 12), (78, 120, 9)):
        p.ellipse(x, y, r, r * 0.9, 'acid', lum=0.55)
        p.ellipse(x - r * 0.3, y - r * 0.3, r * 0.3, r * 0.3, 'acid', lum=0.9)
    p.ellipse(80, 68, 20, 18, 'chitin', tex=0.1)
    p.chain([(80, 56), (80, 36), (88, 22)], 9, 6, 'chitin')
    p.ellipse(90, 20, 10, 8, 'mouth', lum=0.3)
    p.ellipse(94, 18, 5, 4, 'acid', lum=0.85)
    eye(p, 72, 60, 2.2, 'eyegold')
    eye(p, 86, 58, 2.2, 'eyegold')


@picture('broodguard', 160, 160)
def _p(p):
    mats(p)
    for s in (-1, 1):
        p.limb(80 + s * 20, 116, 80 + s * 30, 140, 12, 9, 'chitin')
        p.limb(80 + s * 30, 140, 80 + s * 28, 154, 9, 6, 'boneplate')
    p.ellipse(80, 98, 36, 34, 'chitin', tex=0.1)
    for k in range(4):
        p.ellipse(80, 76 + k * 13, 32 - k * 3, 7, 'boneplate', bias=0.1)
    for s in (-1, 1):
        p.ellipse(80 + s * 36, 66, 18, 14, 'boneplate', tex=0.1)
        p.chain([(80 + s * 40, 76), (80 + s * 50, 100), (80 + s * 42, 122)],
                10, 8, 'chitin')
        p.chain([(80 + s * 42, 122), (80 + s * 36, 142)], 6, 1, 'bone')
    p.ellipse(80, 50, 20, 16, 'boneplate', tex=0.1)
    p.ellipse(80, 60, 14, 8, 'chitin')
    eye(p, 72, 52, 2.5, 'eyered')
    eye(p, 88, 52, 2.5, 'eyered')
    p.chain([(70, 62), (64, 72), (68, 78)], 3, 1, 'bone')
    p.chain([(90, 62), (96, 72), (92, 78)], 3, 1, 'bone')


@picture('whisperer', 160, 160)
def _p(p):
    mats(p)
    p.poly([(80, 60), (50, 80), (40, 156), (120, 156), (110, 80)], 'chitin',
           lum=0.4, gradx=-0.3, tex=0.08)
    for s in (-1, 1):
        p.chain([(80 + s * 22, 80), (80 + s * 40, 100), (80 + s * 34, 124)],
                5, 4, 'paleskin')
        for k in range(4):
            p.limb(80 + s * 34, 124, 80 + s * (30 + k * 3), 140, 1.2, 0.6,
                   'paleskin')
    p.ellipse(80, 40, 30, 32, 'paleskin', tex=0.08)
    for k in range(5):
        p.chain([(58 + k * 11, 22), (54 + k * 12, 34), (58 + k * 11, 44)],
                1.5, 1, 'teal')
    eye(p, 70, 52, 3.5, 'violetglow')
    eye(p, 90, 52, 3.5, 'violetglow')
    p.ellipse(80, 66, 6, 3, 'mouth', lum=0.3)
    p.shade_where(lambda x, y: (x - 80) ** 2 + (y - 40) ** 2 < 900, 0.08,
                  {'paleskin'})


@picture('ravager', 160, 160)
def _p(p):
    mats(p)
    p.chain([(60, 120), (30, 130), (12, 112), (8, 86)], 7, 2, 'chitin')
    for s in (-1, 1):
        p.chain([(80 + s * 14, 110), (80 + s * 34, 124), (80 + s * 26, 154)],
                10, 6, 'chitin', tex=0.1)
    p.ellipse(80, 92, 30, 30, 'chitin', tex=0.12)
    p.ellipse(80, 98, 16, 20, 'flesh', tex=0.1)
    for s in (-1, 1):
        for i in range(2):
            y0 = 70 + i * 18
            p.chain([(80 + s * 24, y0), (80 + s * 54, y0 - 14 + i * 8),
                     (80 + s * 66, y0 + 14)], 6, 4, 'chitin')
            p.chain([(80 + s * 66, y0 + 14), (80 + s * 56, y0 + 44)], 4, 0.8,
                    'bone')
    p.ellipse(80, 50, 22, 20, 'chitin', tex=0.1)
    p.chain([(70, 38), (60, 18), (64, 4)], 4, 1, 'boneplate')
    p.chain([(90, 38), (100, 18), (96, 4)], 4, 1, 'boneplate')
    p.ellipse(80, 62, 14, 8, 'mouth', lum=0.35)
    for k in range(-4, 5):
        p.poly([(80 + k * 3 - 1, 58), (80 + k * 3 + 1, 58), (80 + k * 3, 65)],
               'teeth', lum=0.9)
    for (x, y) in ((70, 46), (90, 46), (76, 40), (84, 40)):
        eye(p, x, y, 2, 'eyered')


@picture('warden', 180, 170)
def _p(p):
    mats(p)
    for s in (-1, 1):
        p.limb(90 + s * 24, 120, 90 + s * 32, 150, 14, 12, 'iron')
        p.rect(90 + s * 32 - 16, 148, 32, 20, 'iron', lum=0.45, gradx=-0.3)
    p.poly([(52, 50), (128, 50), (122, 124), (58, 124)], 'iron', lum=0.55,
           gradx=-0.4, tex=0.06)
    p.rect(52, 84, 76, 8, 'brass', lum=0.6)
    emblem(p, 90, 70, 13)
    for s in (-1, 1):
        p.ellipse(90 + s * 50, 54, 24, 18, 'iron', tex=0.06)
        p.ellipse(90 + s * 50, 54, 24, 6, 'brass', lum=0.55)
        p.limb(90 + s * 54, 64, 90 + s * 62, 104, 12, 11, 'iron')
    p.rect(138, 100, 30, 18, 'iron', lum=0.5)
    for k in range(3):
        p.line(144 + k * 8, 118, 144 + k * 8, 140, 'steel', 0.8, 4)
    p.ellipse(28, 112, 14, 18, 'iron', bias=0.05)
    p.ellipse(28, 112, 8, 10, 'flame', lum=0.6)
    p.ellipse(90, 36, 22, 18, 'iron', bias=0.1)
    p.rect(74, 34, 32, 5, 'shadow', lum=0.0)
    eye(p, 90, 36, 3, 'eyered')
    p.rect(60, 12, 60, 8, 'brass', lum=0.5)


@picture('matriarch', 220, 180, height=0.84)
def _p(p):
    mats(p)
    # the swollen body, half fused into the hive
    p.ellipse(150, 130, 72, 46, 'flesh', tex=0.1)
    for (x, y, r) in ((180, 120, 12), (150, 146, 10), (200, 146, 9),
                      (126, 120, 8)):
        p.ellipse(x, y, r, r, 'teal', lum=0.55)
        p.ellipse(x - r * 0.3, y - r * 0.3, r * 0.3, r * 0.3, 'teal', lum=0.95)
    for s in (-1, 1):
        for i in range(3):
            p.chain([(100 + s * 16, 100 + i * 10),
                     (100 + s * (52 + i * 8), 80 + i * 16),
                     (100 + s * (64 + i * 10), 176)], 7 - i, 2, 'chitin')
    p.ellipse(100, 96, 34, 36, 'chitin', tex=0.12)
    for k in range(5):
        p.ellipse(100, 76 + k * 10, 28 - k * 2, 5, 'chitin', bias=0.15)
    for s in (-1, 1):
        p.chain([(100 + s * 28, 70), (100 + s * 66, 40), (100 + s * 86, 70)],
                9, 6, 'chitin')
        p.chain([(100 + s * 86, 70), (100 + s * 78, 112)], 6, 1, 'bone')
        p.chain([(100 + s * 24, 90), (100 + s * 44, 110), (100 + s * 36, 132)],
                5, 3, 'chitin')
    p.ellipse(100, 44, 26, 24, 'chitin', tex=0.1)
    p.poly([(76, 36), (64, 2), (88, 26)], 'boneplate', lum=0.55)
    p.poly([(124, 36), (136, 2), (112, 26)], 'boneplate', lum=0.55)
    p.poly([(88, 30), (100, 0), (112, 30)], 'boneplate', lum=0.65)
    p.ellipse(100, 60, 16, 9, 'mouth', lum=0.35)
    for k in range(-5, 6):
        p.poly([(100 + k * 3 - 1, 55), (100 + k * 3 + 1, 55),
                (100 + k * 3, 63)], 'teeth', lum=0.9)
    for (x, y, r) in ((88, 44, 3.5), (112, 44, 3.5), (94, 36, 2.5),
                      (106, 36, 2.5)):
        eye(p, x, y, r, 'violetglow')
    # the Heart of Orsolya, held in her claws
    p.circle(100, 124, 9, 'brass')
    p.circle(100, 124, 5, 'flame', lum=0.85)


@texture('hull_plate')
def _t():
    return plates(501, '#3c4048', '#101216', cols=(32, 32), rows=(32, 32),
                  grime=0.35)


@texture('hull_frame')
def _t():
    return plates(502, '#565c66', '#16181c', cols=(16, 24, 24),
                  rows=(20, 22, 22), grime=0.3, jitter=0.05)


@picture('vigil_icon', 64, 64)
def _p(p):
    mats(p)
    p.rect(2, 2, 60, 60, 'iron', lum=0.3)
    p.rect(2, 2, 60, 3, 'redtrim', lum=0.6)
    emblem(p, 32, 32, 26)


@picture('vigil_ornament', 44, 40)
def _p(p):
    mats(p)
    emblem(p, 22, 20, 17)


# ----------------------------------------------------------- the marines

def marine(p, cx=80, armour='iron', trim='redtrim', helm=True, weapon='rifle'):
    for s in (-1, 1):
        p.limb(cx + s * 16, 112, cx + s * 20, 136, 13, 12, armour)
        p.limb(cx + s * 20, 136, cx + s * 20, 152, 12, 11, armour)
        p.rect(cx + s * 20 - 13, 148, 26, 10, armour, lum=0.4)
    p.poly([(cx - 30, 54), (cx + 30, 54), (cx + 26, 116), (cx - 26, 116)],
           armour, lum=0.55, gradx=-0.4, tex=0.05)
    p.rect(cx - 26, 104, 52, 8, trim, lum=0.5)
    emblem(p, cx, 76, 12)
    for s in (-1, 1):
        p.ellipse(cx + s * 38, 58, 22, 18, armour, tex=0.05)
        p.ellipse(cx + s * 38, 50, 20, 8, trim, lum=0.55)
        p.limb(cx + s * 42, 70, cx + s * 40, 102, 12, 11, armour)
    if weapon == 'rifle':
        p.rect(cx - 30, 92, 70, 12, 'iron', lum=0.45, gradx=0.3)
        p.rect(cx + 40, 95, 26, 6, 'iron', lum=0.65)
        p.rect(cx - 6, 104, 10, 14, 'iron', lum=0.35)
        p.circle(cx - 40, 102, 9, armour)
        p.circle(cx + 40, 100, 9, armour)
    p.limb(cx, 46, cx, 56, 9, 9, armour)
    if helm:
        p.ellipse(cx, 34, 18, 20, armour, bias=0.1, tex=0.04)
        p.rect(cx - 13, 30, 26, 6, 'shadow', lum=0.0)
        p.rect(cx - 12, 31, 24, 3, 'eyecyan', lum=0.75)
        p.rect(cx - 2, 14, 4, 18, trim, lum=0.6)


@picture('marine', 160, 160)
def _p(p):
    mats(p)
    marine(p)


@picture('title', 200, 180)
def _p(p):
    mats(p)
    p.rect(0, 0, 200, 180, 'shadow', lum=0.05)
    for k in range(20):
        p.circle((k * 53) % 200, (k * 37) % 120, 0.8, 'white', lum=0.9)
    p.circle(160, 40, 28, 'blue', lum=0.3)
    marine(p, cx=100)
    p.limb(160, 160, 160, 10, 2.5, 2.5, 'iron')
    p.poly([(162, 12), (196, 16), (194, 60), (180, 52), (162, 58)],
           'redtrim', lum=0.55, gradx=-0.3)
    emblem(p, 178, 34, 10)


# ------------------------------------------------------------ the crew

@picture('castellan')
def _p(p):
    mats(p)
    person(p, skin='paleskin', robe='iron', trim='brass', hair='greyhair',
           beard=None, bald=False, eyes='eyecyan', mustache=True)
    for s in (-1, 1):
        p.ellipse(80 + s * 44, 112, 20, 14, 'iron', tex=0.05)
        p.ellipse(80 + s * 44, 106, 18, 6, 'redtrim', lum=0.55)
    emblem(p, 80, 134, 10)
    p.ellipse(72, 62, 5, 4, 'eyered', lum=0.85)


@picture('quartermaster')
def _p(p):
    mats(p)
    person(p, skin='darkskin', robe='iron', trim=None, apron='leather',
           bald=True, beard='greyhair', eyes='blue')
    p.rect(110, 104, 34, 10, 'iron', lum=0.5, gradx=0.3)
    p.rect(140, 106, 16, 5, 'iron', lum=0.7)


@picture('sister')
def _p(p):
    mats(p)
    person(p, skin='skin', robe='white', trim='crimson', hood=True,
           eyes='leaf')
    p.rect(68, 112, 24, 8, 'crimson', lum=0.6)
    p.rect(76, 104, 8, 24, 'crimson', lum=0.6)


@picture('steward')
def _p(p):
    mats(p)
    person(p, skin='skin', robe='cloth', trim=None, hair='hair', bald=False,
           eyes='blue', mustache=False)
    p.rect(60, 100, 40, 6, 'redtrim', lum=0.5)


@picture('archivist')
def _p(p):
    mats(p)
    person(p, skin='paleskin', robe='purple', trim='brass', hood=True,
           eyes='eyegreen')
    p.circle(72, 62, 7, 'brass')
    p.circle(72, 62, 5, 'eyegreen', lum=0.8)
    p.limb(62, 70, 46, 90, 1.5, 1.5, 'brass')
    p.rect(112, 112, 30, 22, 'white', lum=0.7)


# ------------------------------------------- the pilgrim ship Mercy of Kessa

def _pilgrim(seed=701):
    px = plates(seed, '#9a8e78', '#2a241c', cols=(32, 32), rows=(36, 28),
                grime=0.4, rust='#6a3a18')
    rng = random.Random(seed)
    # prayer strips pasted on the bulkheads
    for k in range(3):
        x0 = rng.randint(4, 50)
        y0 = rng.randint(4, 20)
        for y in range(y0, y0 + rng.randint(16, 30)):
            for x in range(x0, x0 + 6):
                if y < T:
                    px[y * T + x] = mix('#e8dcb8', '#a89870', rng.random() * 0.4)
        for y in range(y0 + 2, min(T, y0 + 26), 3):
            for x in range(x0 + 1, x0 + 5):
                if rng.random() < 0.6 and y < T:
                    px[y * T + x] = rgb('#3a2a1a')
    for x in range(T):
        for y in (58, 59):
            px[y * T + x] = rgb('#8a1a14')
    return px


@texture('pilgrim_wall')
def _t():
    return _pilgrim()


@texture('pilgrim_shrine')
def _t():
    px = _pilgrim(702)
    p = P(41)
    p.rect(18, 10, 28, 36, 'shadow', lum=0.1)
    p.ellipse(32, 26, 8, 10, 'gold', bias=0.1)
    p.rect(28, 30, 8, 14, 'white', lum=0.75)
    for x in (20, 26, 38, 44):
        p.rect(x - 1, 40, 2.5, 6, 'white', lum=0.85)
        p.ellipse(x, 38, 1.2, 2, 'flame', lum=0.95)
    p.glow.add('flame')
    out = overlay(px, p)
    glow_at(out, 32, 36, 22, '#ffb050', 0.3)
    return out


@texture('pilgrim_door')
def _t():
    return bulkhead_door(_pilgrim(703), hazard=False, seed=42)


@texture('pilgrim_locked')
def _t():
    return bulkhead_door(_pilgrim(704), hazard=False, locked=True, seed=43)


@texture('pilgrim_floor')
def _t():
    px = list(tx.get('vow_floor'))
    rng = random.Random(44)
    for y in range(T):
        for x in range(14, 50):
            edge = x in (14, 15, 48, 49)
            c = '#c8a040' if edge else '#7a1a18'
            px[y * T + x] = scale(c, 0.75 + 0.35 * rng.random())
    return px


@texture('mercy_airlock')
def _t():
    px = _wreck(705)
    stripes(px, 0, 6)
    p = P(45)
    p.circle(32, 34, 22, 'iron', bias=0.05)
    p.circle(32, 34, 17, 'shadow', lum=0.1)
    p.rect(20, 30, 24, 8, 'gold', lum=0.6)
    p.circle(32, 10, 2.5, 'eyegold', lum=0.9)
    return overlay(px, p)


# ------------------------------------------------------------ the people

@picture('novice', 48, 124, height=0.6)
def _p(p):
    mats(p)
    standing(p, 24, 'white', hair='blond', hood=False)
    p.rect(20, 50, 8, 3, 'crimson', lum=0.6)
    p.rect(22.5, 46, 3, 12, 'crimson', lum=0.6)


@picture('shipwright', 48, 124, height=0.62)
def _p(p):
    mats(p)
    standing(p, 24, 'iron', skin='darkskin', hair='black', apron='leather')
    p.rect(30, 62, 12, 6, 'brass', lum=0.6)


@picture('pilgrim', 48, 124, height=0.6)
def _p(p):
    mats(p)
    standing(p, 24, 'cloth', hood=True)
    p.circle(24, 60, 3, 'brass')


@picture('edda_face')
def _p(p):
    mats(p)
    person(p, robe='white', trim='crimson', hair='blond', eyes='blue')


@picture('corra_face')
def _p(p):
    mats(p)
    person(p, skin='darkskin', robe='iron', trim=None, apron='leather',
           hair='black', eyes='leaf')
    p.circle(70, 62, 6, 'brass')
    p.circle(70, 62, 4, 'eyegold', lum=0.8)


@picture('ilse_face')
def _p(p):
    mats(p)
    person(p, robe='cloth', trim=None, hood=True, eyes='leaf')
    p.circle(80, 124, 6, 'brass')


@picture('captain', 160, 160)
def _p(p):
    mats(p)
    for s in (-1, 1):
        p.limb(80 + s * 12, 108, 80 + s * 14, 134, 9, 8, 'black')
        p.limb(80 + s * 14, 134, 80 + s * 13, 152, 8, 7, 'leather')
        p.ellipse(80 + s * 14, 154, 10, 4, 'leather')
    p.poly([(52, 50), (108, 50), (114, 130), (46, 130)], 'crimson', lum=0.45,
           gradx=-0.3, tex=0.06)
    for k in range(4):
        p.circle(72, 62 + k * 10, 2, 'brass', lum=0.8)
        p.circle(88, 62 + k * 10, 2, 'brass', lum=0.8)
    for s in (-1, 1):
        p.ellipse(80 + s * 30, 54, 14, 8, 'brass', tex=0.05)
    p.ellipse(100, 84, 18, 26, 'chitin', tex=0.12)
    for k in range(3):
        p.circle(96 + k * 5, 78 + k * 7, 3, 'teal', lum=0.7)
    p.chain([(56, 56), (44, 82), (48, 104)], 8, 6, 'crimson')
    p.circle(48, 108, 6, 'paleskin')
    p.line(46, 108, 30, 140, 'steel', 0.8, 3)
    p.chain([(106, 56), (126, 74), (140, 66)], 9, 7, 'chitin')
    p.chain([(140, 66), (152, 44), (154, 22)], 6, 1.5, 'bone')
    p.limb(80, 44, 80, 52, 7, 7, 'paleskin')
    p.ellipse(80, 32, 16, 18, 'paleskin', tex=0.1)
    p.ellipse(90, 26, 10, 12, 'chitin', tex=0.1)
    p.rect(62, 12, 36, 8, 'black', lum=0.4)
    p.rect(58, 18, 44, 4, 'black', lum=0.3)
    p.circle(80, 15, 3, 'brass')
    eye(p, 73, 32, 2.6, 'teal')
    eye(p, 87, 34, 2.2, 'teal')
    p.ellipse(78, 44, 6, 3, 'mouth', lum=0.3)

"""Dustwater's pictures and textures: the scrap village, the wasteland,
the ruins of Carvel and its waterworks, Bunker Nine, and the things that
live among them.  Importing this module registers them with the engine."""

import math
import random

from blobber import textures as tx
from blobber.textures import (texture, T, fbm, overlay, glow_at, plates,
                              stripes, light_strip)
from blobber.art import picture, eye, skull, person, standing
from blobber.paint import Painter
from blobber.gfx import rgb, mix, scale

RAMPS = {
    'scrap':   ('#1a1612', '#3a322a', '#5a4e42', '#7e705e', '#a49480'),
    'toxic':   ('#0a2a06', '#1e6a0c', '#3cb018', '#8cf040', '#e0ffb0'),
    'sand':    ('#3a2a18', '#6a5030', '#9a7a4c', '#c4a470', '#e8d0a0'),
    'olive':   ('#14180c', '#2a321a', '#46522c', '#64723e', '#8a9a5a'),
    'antred':  ('#1a0806', '#3a120c', '#601e14', '#8a3020', '#b44a30',
                '#d87050'),
    'shell':   ('#10140a', '#283018', '#424e28', '#5e6c3a', '#7e8c54'),
    'robot':   ('#2a2c30', '#5a5e66', '#8c929c', '#bcc2ca', '#e8ecf0'),
    'scorch':  ('#1a0e08', '#3e2414', '#6a3e22', '#94603a', '#c08a5c'),
    'denim':   ('#0c1018', '#1c2638', '#2e3c58', '#465a7e', '#6a82a6'),
}
GLOWS = {'toxic'}


def mats(p):
    for name, ramp in RAMPS.items():
        p.material(name, *ramp, glow=name in GLOWS)


def P(seed=1, w=T, h=T):
    p = Painter(w, h, seed)
    mats(p)
    return p


def trefoil(p, cx, cy, r, m='black', back='gold'):
    """The radiation warning sign."""
    p.circle(cx, cy, r, back, lum=0.75)
    for k in range(3):
        a0 = -math.pi / 2 + k * 2 * math.pi / 3 - 0.5
        pts = [(cx, cy)]
        for j in range(7):
            a = a0 + j / 6
            pts.append((cx + r * 0.85 * math.cos(a), cy + r * 0.85 * math.sin(a)))
        p.poly(pts, m, lum=0.15)
    p.circle(cx, cy, r * 0.22, back, lum=0.75)
    p.circle(cx, cy, r * 0.14, m, lum=0.15)


# ----------------------------------------------------------- the village

def corrugated(seed, base, rust=0.45):
    rng = random.Random(seed)
    n = fbm(rng, ((4, 0.5), (16, 0.5)))
    px = []
    for y in range(T):
        for x in range(T):
            ridge = math.sin(x / 3.0 * math.pi)
            c = scale(base, 0.8 + 0.25 * ridge)
            v = n[y * T + x]
            if v > 1 - rust:
                c = mix(c, '#7a3a14', min(0.85, (v - 1 + rust) * 3))
            px.append(c)
    for y in (2, 61):
        for x in range(T):
            px[y * T + x] = scale(base, 0.5)
    return px


@texture('shack_a')
def _t():
    px = corrugated(801, '#8a8a84')
    p = P(1)
    p.rect(18, 14, 26, 18, 'wood', lum=0.35)
    p.rect(20, 16, 22, 14, 'shadow', lum=0.08)
    p.line(20, 16, 42, 30, 'wood', 0.5, 2)
    p.rect(0, 40, 64, 3, 'wood', lum=0.55)
    return overlay(px, p)


@texture('shack_b')
def _t():
    rng = random.Random(802)
    px = []
    for y in range(T):
        for x in range(T):
            plank = (x // 9 + (y // 32)) % 3
            base = ['#8a6a44', '#7a5a38', '#9a7a52'][plank]
            c = scale(base, 0.75 + 0.35 * rng.random())
            if x % 9 == 0:
                c = scale(base, 0.45)
            px.append(c)
    p = P(2)
    p.rect(8, 34, 22, 22, 'scrap', lum=0.6, gradx=-0.3)
    for x in (12, 22):
        p.circle(x, 38, 1.3, 'iron', lum=0.8)
    return overlay(px, p)


@texture('scrapwall')
def _t():
    px = corrugated(803, '#6a645a', 0.6)
    p = P(3)
    rng = random.Random(4)
    for _ in range(6):
        x, y = rng.randint(0, 50), rng.randint(0, 50)
        w, h = rng.randint(10, 22), rng.randint(8, 18)
        p.rect(x, y, w, h, rng.choice(['scrap', 'rust', 'denim', 'iron']),
               lum=0.4 + 0.3 * rng.random(), gradx=-0.3)
    for k in range(4):
        p.circle(10 + k * 15, 56, 6, 'black', bias=-0.1)
        p.circle(10 + k * 15, 56, 3, 'shadow', lum=0.1)
    return overlay(px, p)


def _shopfront(seed, base_px, icon, board):
    p = P(seed)
    # a door of planks, and a painted sign board over it
    p.rect(22, 30, 20, 34, 'wood', lum=0.45, gradx=-0.3)
    for x in range(22, 42, 5):
        p.rect(x, 30, 1, 34, 'shadow', lum=0.2)
    p.circle(38, 48, 1.5, 'iron', lum=0.8)
    p.rect(10, 6, 44, 18, board, lum=0.55, grad=-0.3)
    p.rect(10, 6, 44, 1, 'wood', lum=0.8)
    icon(p, 32, 15)
    return overlay(base_px, p)


def _i_cow_skull(p, x, y):
    p.ellipse(x, y, 5, 6, 'bone')
    p.limb(x - 4, y - 4, x - 12, y - 8, 1.5, 0.8, 'bone')
    p.limb(x + 4, y - 4, x + 12, y - 8, 1.5, 0.8, 'bone')
    p.circle(x - 2, y - 1, 1.2, 'shadow', lum=0.0)
    p.circle(x + 2, y - 1, 1.2, 'shadow', lum=0.0)


def _i_crate(p, x, y):
    p.rect(x - 7, y - 5, 14, 10, 'wood', lum=0.6, gradx=-0.3)
    p.line(x - 7, y - 5, x + 7, y + 5, 'wood', 0.35, 1)
    p.line(x + 7, y - 5, x - 7, y + 5, 'wood', 0.35, 1)


def _i_leaf(p, x, y):
    p.ellipse(x, y, 4, 7, 'leaf', bias=0.1, angle=0.6)
    p.line(x - 3, y + 4, x + 3, y - 4, 'leaf', 0.3, 1)


def _i_bed(p, x, y):
    p.rect(x - 8, y - 1, 16, 4, 'white', lum=0.8)
    p.rect(x - 8, y + 3, 2, 3, 'wood', lum=0.5)
    p.rect(x + 6, y + 3, 2, 3, 'wood', lum=0.5)
    p.ellipse(x - 5, y - 3, 3, 2, 'white', lum=0.9)


def _i_gear(p, x, y):
    for k in range(8):
        a = k * math.pi / 4
        p.circle(x + 6 * math.cos(a), y + 6 * math.sin(a), 1.8, 'iron',
                 lum=0.7)
    p.circle(x, y, 5.5, 'iron', lum=0.6)
    p.circle(x, y, 2, 'black', lum=0.2)


@texture('dw_elder')
def _t():
    return _shopfront(811, tx.get('shack_b'), _i_cow_skull, 'crimson')


@texture('dw_trader')
def _t():
    return _shopfront(812, tx.get('shack_a'), _i_crate, 'blue')


@texture('dw_healer')
def _t():
    return _shopfront(813, tx.get('shack_b'), _i_leaf, 'white')


@texture('dw_bunk')
def _t():
    return _shopfront(814, tx.get('shack_a'), _i_bed, 'leaf')


@texture('dw_mags')
def _t():
    return _shopfront(815, corrugated(816, '#6a7a7a'), _i_gear, 'black')


@texture('dw_purifier')
def _t():
    px = plates(817, '#6a7078', '#202428', cols=(32, 32), rows=(32, 32),
                rust='#7a3a14', grime=0.5)
    p = P(5)
    for x in (14, 50):
        p.rect(x - 9, 8, 18, 46, 'scrap', lum=0.55, gradx=-0.6)
        p.ellipse(x, 8, 9, 3, 'scrap', bias=0.1)
    p.rect(0, 30, 64, 5, 'iron', lum=0.5, grad=-0.5)
    p.circle(32, 22, 7, 'gold', lum=0.5)
    p.circle(32, 22, 4, 'water', lum=0.6)
    p.rect(28, 40, 8, 10, 'shadow', lum=0.05)
    p.circle(32, 46, 2, 'eyered', lum=0.9)
    out = overlay(px, p)
    glow_at(out, 32, 46, 8, '#ff3020', 0.3)
    return out


@texture('dw_gate')
def _t():
    px = tx.get('scrapwall')
    px = list(px)
    for y in range(8, 64):
        for x in range(12, 52):
            if (x - 12) % 6 == 0 or (y - 8 + (x - 12)) % 6 == 0 or \
                    (y - 8 - (x - 12)) % 6 == 0:
                px[y * T + x] = rgb('#a0a4a8')
            else:
                px[y * T + x] = rgb('#3a3226')
    for y in range(8, 64):
        for x in (10, 11, 52, 53):
            px[y * T + x] = rgb('#5a5a5a')
    return px


@texture('dust')
def _t():
    rng = random.Random(820)
    n = fbm(rng, ((8, 0.5), (32, 0.5)))
    px = [scale('#9a7a54', 0.75 + 0.35 * v) for v in n]
    # cracks in the dried earth
    for _ in range(9):
        x, y = rng.uniform(0, T), rng.uniform(0, T)
        a = rng.uniform(0, math.tau)
        for _ in range(rng.randint(8, 20)):
            px[int(y) % T * T + int(x) % T] = rgb('#4a3820')
            a += rng.uniform(-0.8, 0.8)
            x += math.cos(a)
            y += math.sin(a)
    return px


# --------------------------------------------------------- the wasteland

@texture('rockface')
def _t():
    rng = random.Random(830)
    n = fbm(rng, ((4, 0.4), (16, 0.4), (32, 0.2)))
    px = []
    for y in range(T):
        band = math.sin(y / 5.0 + 3 * n[y * T]) * 0.5 + 0.5
        for x in range(T):
            c = mix('#7a3e22', '#c07a48', band * 0.6 + n[y * T + x] * 0.4)
            px.append(scale(c, 0.8 + 0.3 * n[(y * 7 + x) % (T * T)]))
    return tx.cracks(px, 831, 4, '#3a1e10')


@texture('ruinwall')
def _t():
    px = tx.stone_wall(832, '#8a8a84', '#3a3a36', [16, 16, 16, 16], 20, 32,
                       noise=0.45, jitter=0.1)
    rng = random.Random(833)
    # broken top, and rebar sticking out
    for x in range(T):
        top = int(10 + 8 * math.sin(x / 6.0) + rng.randint(0, 4))
        for y in range(0, top):
            px[y * T + x] = None
    p = P(6)
    for x in (12, 30, 48):
        p.line(x, 4, x + 3, 22, 'rust', 0.5, 1.5)
    out = overlay([c if c else (0, 0, 0) for c in px], p)
    # what isn't wall shows the sky's haze colour (it is drawn as wall)
    for i, c in enumerate(px):
        if c is None and out[i] == (0, 0, 0):
            out[i] = rgb('#c8905a')
    return tx.moss(out, 834, '#5a6a2a', 0.3, 'bottom')


@texture('city_gate')
def _t():
    px = tx.get('ruinwall')
    px = list(px)
    p = P(7)
    p.rect(10, 20, 44, 44, 'shadow', lum=0.06)
    p.rect(8, 16, 48, 6, 'scrap', lum=0.6)
    p.rect(14, 4, 36, 12, 'leaf', lum=0.5, grad=-0.3)
    for k in range(5):
        p.rect(18 + k * 6, 8, 4, 4, 'white', lum=0.85)
    return overlay(px, p)


@texture('bunker_hatch')
def _t():
    px = tx.stone_wall(835, '#7a7a70', '#2a2a26', [32, 32], 30, 40,
                       noise=0.4, round_=1)
    p = P(8)
    p.rect(12, 18, 40, 46, 'olive', lum=0.45, gradx=-0.4)
    p.rect(31, 18, 2, 46, 'shadow', lum=0.0)
    for y in (26, 54):
        p.rect(12, y, 40, 3, 'iron', lum=0.6)
    trefoil(p, 32, 9, 7)
    p.rect(42, 36, 6, 8, 'iron', lum=0.4)
    p.circle(45, 38, 1.5, 'eyered', lum=0.9)
    out = overlay(px, p)
    return stripes(out, 60, 64)


@texture('sand')
def _t():
    rng = random.Random(840)
    n = fbm(rng, ((4, 0.5), (8, 0.3), (32, 0.2)))
    px = []
    for y in range(T):
        for x in range(T):
            ripple = math.sin((x + y * 0.4 + 6 * n[y * T + x]) / 3.0)
            px.append(scale('#c49a62', 0.82 + 0.12 * ripple + 0.15 * n[y * T + x]))
    return px


@texture('road')
def _t():
    rng = random.Random(841)
    n = fbm(rng, ((8, 0.5), (32, 0.5)))
    px = [scale('#4a4844', 0.7 + 0.4 * v) for v in n]
    for y in range(T):
        if (y // 8) % 2 == 0:
            for x in (31, 32):
                px[y * T + x] = rgb('#c8b450')
    tx.cracks(px, 842, 5, '#1a1816')
    for _ in range(30):
        x, y = rng.randrange(T), rng.randrange(T)
        px[y * T + x] = rgb('#9a7a54')
    return px


@texture('rad_ground')
def _t():
    px = list(tx.get('sand'))
    rng = random.Random(843)
    for i in range(T * T):
        px[i] = mix(px[i], '#6a8a20', 0.45)
    for _ in range(60):
        x, y = rng.randrange(T), rng.randrange(T)
        px[y * T + x] = rgb('#b0ff60')
    return px


# --------------------------------------------------------- Carvel's ruins

def _tower(seed, base, lit_chance=0.0):
    rng = random.Random(seed)
    px = tx.stone_wall(seed, base, '#2a2a28', [16, 16, 16, 16], 32, 32,
                       noise=0.35, jitter=0.06, round_=0)
    p = P(seed)
    for wy in (6, 38):
        for wx in (6, 38):
            broken = rng.random() < 0.6
            p.rect(wx, wy, 20, 18, 'shadow', lum=0.08)
            if not broken:
                p.rect(wx + 1, wy + 1, 18, 16, 'glass', lum=0.45)
                p.line(wx + 2, wy + 15, wx + 16, wy + 3, 'glass', 0.8, 1)
            else:
                p.poly([(wx + 1, wy + 1), (wx + 9, wy + 1), (wx + 1, wy + 9)],
                       'glass', lum=0.5)
    return tx.cracks(overlay(px, p), seed + 1, 4, '#1a1a18')


@texture('tower_a')
def _t():
    return _tower(850, '#8a8478')


@texture('tower_b')
def _t():
    px = tx.brick_wall(851, '#7a4434', '#2a1e1a', bw=12, bh=6)
    p = P(852)
    for wx in (8, 36):
        p.rect(wx, 10, 20, 22, 'shadow', lum=0.08)
        p.rect(wx, 40, 20, 18, 'shadow', lum=0.08)
    return overlay(px, p)


@texture('rubble')
def _t():
    rng = random.Random(853)
    px = [None] * (T * T)
    p = P(854)
    for _ in range(40):
        x, y = rng.uniform(0, 64), rng.uniform(16, 64)
        r = rng.uniform(4, 11)
        p.ellipse(x, y, r, r * 0.7, rng.choice(['stone', 'scrap', 'stone']),
                  tex=0.2, angle=rng.uniform(0, 3))
    for _ in range(4):
        x = rng.uniform(4, 60)
        p.line(x, 64, x + rng.uniform(-10, 10), rng.uniform(10, 30), 'rust',
               0.5, 1.5)
    sky = [mix('#b07a50', '#d8a070', y / T) for y in range(T)]
    base = [sky[i // T] for i in range(T * T)]
    return overlay(base, p)


@texture('shopfront')
def _t():
    px = _tower(855, '#7a8070')
    p = P(856)
    p.rect(4, 30, 56, 34, 'shadow', lum=0.06)
    p.rect(4, 22, 56, 8, 'crimson', lum=0.45)
    for k in range(6):
        p.rect(8 + k * 8, 24, 5, 4, 'white', lum=0.6)
    p.rect(26, 36, 12, 28, 'scrap', lum=0.4)
    return overlay(px, p)


@texture('waterworks_gate')
def _t():
    px = tx.stone_wall(857, '#7a7a72', '#2a2a28', [16, 16, 16, 16], 24, 32,
                       noise=0.4)
    p = P(858)
    p.rect(10, 4, 44, 12, 'blue', lum=0.45, grad=-0.3)
    for k in range(6):
        p.rect(14 + k * 6, 8, 4, 4, 'white', lum=0.8)
    p.rect(14, 22, 36, 42, 'iron', lum=0.4, gradx=-0.4)
    p.circle(32, 42, 10, 'iron', lum=0.6)
    for k in range(6):
        a = k * math.pi / 3
        p.line(32, 42, 32 + 9 * math.cos(a), 42 + 9 * math.sin(a), 'iron',
               0.75, 1.5)
    return overlay(px, p)


@texture('asphalt')
def _t():
    px = list(tx.get('road'))
    rng = random.Random(859)
    for _ in range(12):
        x, y, r = rng.randint(0, 63), rng.randint(0, 63), rng.randint(1, 3)
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r, x + r + 1):
                px[(yy % T) * T + xx % T] = scale('#7a7a76', 0.8 +
                                                  0.3 * rng.random())
    return px


# ------------------------------------------------------- the waterworks

def _concrete(seed):
    return tx.stone_wall(seed, '#7a7c78', '#3a3c3a', [16, 16, 16, 16], 32, 32,
                         noise=0.4, jitter=0.05, round_=0)


@texture('ww_wall')
def _t():
    px = _concrete(860)
    rng = random.Random(861)
    for x in range(T):
        if rng.random() < 0.3:
            for y in range(rng.randint(10, 50)):
                i = y * T + x
                px[i] = mix(px[i], '#2a3a2a', 0.4 * (1 - y / 60))
    return px


@texture('ww_pipes')
def _t():
    px = _concrete(862)
    p = P(9)
    for y, r in ((18, 7), (44, 5)):
        p.rect(0, y - r, 64, 2 * r, 'iron', lum=0.5, grad=-0.7)
        for x in (12, 44):
            p.rect(x, y - r - 1, 4, 2 * r + 2, 'rust', lum=0.5, gradx=-0.5)
    return overlay(px, p)


@texture('ww_valve')
def _t():
    px = _concrete(863)
    p = P(10)
    p.rect(28, 0, 8, 64, 'iron', lum=0.45, gradx=-0.6)
    p.circle(32, 32, 14, 'crimson', lum=0.5)
    p.circle(32, 32, 11, 'shadow', lum=0.1)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        p.line(32, 32, 32 + 12 * math.cos(a), 32 + 12 * math.sin(a),
               'crimson', 0.6, 2)
    p.circle(32, 32, 3, 'crimson', lum=0.7)
    return overlay(px, p)


def _hatch(seed, px, locked=False):
    p = P(seed)
    p.rect(12, 8, 40, 56, 'iron', lum=0.45, gradx=-0.4)
    p.rect(14, 10, 36, 52, 'iron', lum=0.55, gradx=-0.4)
    for y in (14, 56):
        for x in (16, 46):
            p.circle(x, y, 1.5, 'iron', lum=0.85)
    p.rect(40, 30, 6, 10, 'iron', lum=0.75)
    if locked:
        p.rect(20, 28, 24, 6, 'iron', lum=0.8, grad=0.4)
        p.circle(32, 31, 3, 'eyered', lum=0.9)
    return overlay(px, p)


@texture('ww_door')
def _t():
    return _hatch(864, _concrete(865))


@texture('ww_locked')
def _t():
    return _hatch(866, _concrete(867), locked=True)


@texture('ww_floor')
def _t():
    px = _concrete(868)
    rng = random.Random(869)
    n = fbm(rng, ((8, 1.0),))
    for i in range(T * T):
        if n[i] > 0.62:
            px[i] = mix(px[i], '#2a3a44', 0.6)
    return px


@texture('ww_water')
def _t():
    rng = random.Random(870)
    px = []
    for y in range(T):
        for x in range(T):
            wave = math.sin((x + 2 * math.sin(y / 5.0)) / 4.0)
            c = scale('#1e3a3a', 0.8 + 0.25 * wave + 0.1 * rng.random())
            if (x % 16 in (0, 1)) or (y % 16 in (0, 1)):
                c = scale('#5a5a56', 0.9)
            px.append(c)
    return px


@texture('ww_ceil')
def _t():
    return [scale(c, 0.65) for c in _concrete(871)]


# ----------------------------------------------------------- Bunker Nine

def _olive(seed):
    px = plates(seed, '#5a6448', '#1a2014', cols=(32, 32), rows=(40, 24),
                grime=0.3)
    return px


def _stencil(px, text_rows, x0, y0, colour='#d8d0b0'):
    """Blocky stencilled numbers from rows of '#.'."""
    for j, row in enumerate(text_rows):
        for i, ch in enumerate(row):
            if ch == '#':
                for yy in range(2):
                    for xx in range(2):
                        px[(y0 + j * 2 + yy) * T + x0 + i * 2 + xx] = rgb(colour)
    return px


NINE = ['###', '#.#', '###', '..#', '###']


@texture('bk_wall')
def _t():
    px = _olive(880)
    light_strip(px, 44, '#c0e0ff', 8, 56)
    return px


@texture('bk_nine')
def _t():
    px = _olive(881)
    _stencil(px, NINE, 26, 12)
    stripes(px, 48, 54)
    return px


@texture('bk_terminal')
def _t():
    px = _olive(882)
    p = P(11)
    p.rect(6, 8, 52, 40, 'iron', lum=0.35)
    p.rect(10, 12, 26, 18, 'shadow', lum=0.05)
    for k in range(4):
        p.rect(12, 14 + k * 4, 10 + (k * 7) % 14, 1.5, 'toxic', lum=0.75)
    for k in range(3):
        p.circle(46 + (k % 2) * 6, 16 + k * 6, 3, 'shadow', lum=0.1)
        p.circle(46 + (k % 2) * 6, 16 + k * 6, 2, 'iron', lum=0.6)
    for k in range(6):
        p.circle(14 + k * 7, 40, 1.5, ['eyered', 'eyegold', 'eyegreen'][k % 3],
                 lum=0.9)
    out = overlay(px, p)
    glow_at(out, 23, 21, 16, '#60ff60', 0.15)
    return out


@texture('bk_hazard')
def _t():
    px = _olive(883)
    p = P(12)
    trefoil(p, 32, 24, 14)
    out = overlay(px, p)
    return stripes(out, 50, 58)


def _blastdoor(seed, locked=False):
    px = _olive(seed)
    p = P(seed)
    p.rect(8, 6, 48, 58, 'shadow', lum=0.1)
    p.rect(10, 8, 21, 56, 'olive', lum=0.55, gradx=-0.4)
    p.rect(33, 8, 21, 56, 'olive', lum=0.5, gradx=-0.4)
    for k in range(4):
        y = 22 + k * 10
        p.poly([(10, y), (31, y - 6), (31, y - 3), (10, y + 3)], 'gold',
               lum=0.6)
        p.poly([(33, y - 6), (54, y), (54, y + 3), (33, y - 3)], 'gold',
               lum=0.6)
    p.circle(32, 4, 2.5, 'eyered' if locked else 'eyegreen', lum=0.9)
    if locked:
        p.rect(44, 30, 8, 12, 'iron', lum=0.5)
        p.rect(46, 32, 4, 3, 'eyered', lum=0.85)
    return overlay(px, p)


@texture('bk_door')
def _t():
    return _blastdoor(884)


@texture('bk_locked')
def _t():
    return _blastdoor(885, locked=True)


@texture('bk_floor')
def _t():
    px = plates(886, '#5a5c58', '#2a2c2a', cols=(32, 32), rows=(32, 32),
                rivets=False, grime=0.25)
    return px


@texture('bk_ceil')
def _t():
    px = plates(887, '#3a3e36', '#141612', cols=(64,), rows=(32, 32),
                rivets=False)
    for y in range(28, 36):
        for x in range(12, 52):
            px[y * T + x] = rgb('#e8f4ff') if 29 <= y < 35 else rgb('#6a6a6a')
    return px


@texture('bk_lift')
def _t():
    px = list(tx.get('bk_floor'))
    for y in range(8, 56):
        for x in range(8, 56):
            edge = min(x - 8, 55 - x, y - 8, 55 - y)
            px[y * T + x] = (rgb('#d8b020') if ((x + y) // 4) % 2 else
                             rgb('#141414')) if edge < 4 else \
                scale('#4a4e46', 0.8 + 0.1 * ((x // 6 + y // 6) % 2))
    return px


# ------------------------------------------------------------- things

@picture('deadtree', 96, 150, height=1.2)
def _p(p):
    mats(p)
    p.limb(48, 150, 46, 60, 7, 4, 'wood', tex=0.2)
    for (x0, y0, x1, y1) in ((46, 90, 20, 50), (46, 80, 76, 40),
                             (47, 66, 30, 22), (47, 62, 66, 14),
                             (20, 50, 8, 40), (76, 40, 88, 30)):
        p.limb(x0, y0, x1, y1, 3, 1, 'wood', bias=-0.1)


@picture('carwreck', 128, 72, height=0.42)
def _p(p):
    mats(p)
    p.poly([(6, 40), (24, 22), (90, 20), (116, 38), (122, 58), (6, 58)],
           'rust', lum=0.5, gradx=-0.3, tex=0.15)
    p.poly([(30, 26), (86, 24), (100, 38), (26, 38)], 'shadow', lum=0.1)
    p.line(48, 25, 52, 38, 'rust', 0.4, 2)
    for x in (30, 98):
        p.circle(x, 60, 11, 'black', bias=-0.1)
        p.circle(x, 60, 5, 'scrap', lum=0.4)
    p.rect(110, 44, 10, 5, 'eyegold', lum=0.4)


@picture('signpost', 64, 120, height=0.7)
def _p(p):
    mats(p)
    p.rect(29, 30, 6, 90, 'wood', lum=0.5, gradx=-0.4)
    p.poly([(4, 16), (52, 16), (60, 24), (52, 32), (4, 32)], 'wood', lum=0.6,
           grad=-0.3)
    p.poly([(60, 40), (12, 40), (4, 48), (12, 56), (60, 56)], 'wood',
           lum=0.55, grad=-0.3)
    for y in (24, 48):
        p.line(14, y, 46, y, 'black', 0.2, 1)


@picture('barrels', 96, 80, height=0.4)
def _p(p):
    mats(p)
    for (x, y) in ((24, 46), (60, 50), (42, 30)):
        p.ellipse(x, y + 26, 15, 5, 'shadow', lum=0.1)
        p.rect(x - 14, y, 28, 26, 'gold', lum=0.5, gradx=-0.6, tex=0.1)
        p.ellipse(x, y, 14, 5, 'toxic', lum=0.7)
        for yy in (y + 8, y + 18):
            p.rect(x - 14, yy, 28, 2, 'rust', lum=0.4)
        trefoil(p, x, y + 13, 4, 'black', 'gold')


@picture('campfire', 64, 60, height=0.3)
def _p(p):
    mats(p)
    for k in range(5):
        a = k * math.pi / 5 + 0.2
        p.line(32 - 18 * math.cos(a), 54, 32 + 18 * math.cos(a), 50, 'wood',
               0.45, 3)
    p.ellipse(32, 36, 12, 18, 'flame', lum=0.6)
    p.ellipse(32, 40, 7, 11, 'flame', lum=0.85)
    p.glow.add('flame')


@picture('tent', 112, 80, height=0.5)
def _p(p):
    mats(p)
    p.poly([(56, 6), (108, 78), (4, 78)], 'scorch', lum=0.55, gradx=-0.4,
           tex=0.1)
    p.poly([(56, 30), (70, 78), (42, 78)], 'shadow', lum=0.05)
    p.line(56, 0, 56, 10, 'wood', 0.5, 2)
    skull(p, 56, 20, 5)


@picture('pylon', 80, 170, height=1.5)
def _p(p):
    mats(p)
    for s in (-1, 1):
        p.line(40 + s * 30, 170, 40 + s * 6, 20, 'iron', 0.5, 3)
    for y in range(40, 170, 26):
        w = 6 + (y - 20) * 24 / 150
        p.line(40 - w, y, 40 + w, y + 13, 'iron', 0.45, 1.5)
        p.line(40 + w, y, 40 - w, y + 13, 'iron', 0.45, 1.5)
    p.line(10, 32, 70, 32, 'iron', 0.55, 3)
    p.line(14, 52, 66, 52, 'iron', 0.5, 2.5)


@picture('purifier_sprite', 96, 120, height=0.8)
def _p(p):
    mats(p)
    for x in (24, 72):
        p.rect(x - 16, 20, 32, 90, 'scrap', lum=0.55, gradx=-0.6)
        p.ellipse(x, 20, 16, 5, 'scrap', bias=0.1)
    p.rect(0, 60, 96, 8, 'iron', lum=0.5, grad=-0.5)
    p.circle(48, 50, 10, 'water', lum=0.55)


@picture('robo', 64, 80, height=0.45)
def _p(p):
    mats(p)
    p.ellipse(32, 72, 20, 6, 'shadow', lum=0.1)
    p.rect(14, 30, 36, 34, 'robot', lum=0.6, gradx=-0.4)
    p.ellipse(32, 24, 16, 12, 'robot', bias=0.05)
    p.rect(20, 20, 24, 6, 'shadow', lum=0.05)
    eye(p, 26, 23, 2.2, 'eyecyan')
    eye(p, 38, 23, 2.2, 'eyecyan')
    for s in (-1, 1):
        p.limb(32 + s * 18, 36, 32 + s * 26, 52, 3, 2.5, 'iron')
    for x in (20, 44):
        p.circle(x, 66, 6, 'black', bias=-0.1)


# ------------------------------------------------------------ monsters

@picture('glowhound', 170, 140)
def _p(p):
    mats(p)
    p.chain([(132, 70), (150, 54), (160, 40)], 5, 2, 'scorch')
    for x, s in ((60, 1), (118, 1)):
        p.limb(x, 92, x - 4, 132, 7, 5, 'scorch', tex=0.15)
        p.ellipse(x - 4, 134, 8, 4, 'scorch')
    p.ellipse(92, 78, 46, 24, 'scorch', tex=0.25)
    for k in range(5):
        p.circle(70 + k * 14, 66 + (k % 2) * 8, 4, 'toxic', lum=0.6)
    p.ellipse(42, 62, 22, 18, 'scorch', tex=0.2, angle=-0.3)
    p.ellipse(22, 72, 16, 10, 'scorch', angle=0.3)
    p.poly([(36, 46), (44, 26), (52, 48)], 'scorch', lum=0.5)
    p.poly([(52, 44), (62, 26), (64, 48)], 'scorch', lum=0.45)
    eye(p, 34, 58, 3.5, 'toxic')
    eye(p, 48, 56, 3, 'toxic')
    p.ellipse(16, 78, 10, 4, 'mouth', lum=0.35)
    for k in range(4):
        p.poly([(10 + k * 4, 76), (12 + k * 4, 76), (11 + k * 4, 81)],
               'teeth', lum=0.9)


def raider(p, cx=80, boss=False):
    for s in (-1, 1):
        p.limb(cx + s * 10, 108, cx + s * 13, 134, 8, 7, 'denim', tex=0.1)
        p.limb(cx + s * 13, 134, cx + s * 13, 150, 7, 7, 'leather')
        p.ellipse(cx + s * 14, 153, 10, 4, 'leather')
    p.poly([(cx - 24, 52), (cx + 24, 52), (cx + 22, 110), (cx - 22, 110)],
           'leather', lum=0.5, gradx=-0.3, tex=0.1)
    p.rect(cx - 22, 70, 44, 14, 'scrap', lum=0.55, gradx=-0.3)
    for k in range(3):
        p.circle(cx - 14 + k * 14, 77, 2, 'iron', lum=0.8)
    for s in (-1, 1):
        p.ellipse(cx + s * 26, 56, 13, 9, 'scrap' if not boss else 'rust',
                  tex=0.1)
        if boss:
            for k in range(3):
                p.poly([(cx + s * (18 + k * 7), 50),
                        (cx + s * (21 + k * 7), 36),
                        (cx + s * (24 + k * 7), 50)], 'iron', lum=0.7)
    p.chain([(cx - 26, 60), (cx - 34, 84), (cx - 24, 98)], 7, 6, 'skin')
    p.chain([(cx + 26, 60), (cx + 30, 84), (cx + 18, 96)], 7, 6, 'skin')
    p.limb(cx, 44, cx, 54, 6, 6, 'skin')
    p.ellipse(cx, 34, 14, 16, 'skin', tex=0.08)
    p.rect(cx - 12, 30, 24, 7, 'black', lum=0.3)
    p.circle(cx - 5, 33, 3, 'eyered', lum=0.6)
    p.circle(cx + 5, 33, 3, 'eyered', lum=0.6)
    for k in range(5):
        p.poly([(cx - 3, 22 - k * 0), (cx + 3, 22), (cx, 8 + k * 2)],
               'redhair', lum=0.6)
    p.line(cx - 6, 43, cx + 6, 43, 'mouth', 0.3, 1.5)


@picture('raider')
def _p(p):
    mats(p)
    raider(p)
    p.rect(40, 92, 70, 7, 'scrap', lum=0.5, gradx=0.4)
    p.rect(104, 90, 22, 4, 'iron', lum=0.7)
    p.rect(52, 99, 8, 10, 'wood', lum=0.45)


@picture('raiderboss', 180, 170)
def _p(p):
    mats(p)
    raider(p, 90, boss=True)
    p.chain([(116, 96), (138, 120), (150, 110), (156, 130)], 3, 2, 'iron')
    p.circle(160, 140, 9, 'iron', bias=0.1)
    for k in range(6):
        a = k * math.pi / 3
        p.poly([(160 + 8 * math.cos(a), 140 + 8 * math.sin(a)),
                (160 + 14 * math.cos(a + 0.2), 140 + 14 * math.sin(a + 0.2)),
                (160 + 8 * math.cos(a + 0.4), 140 + 8 * math.sin(a + 0.4))],
               'iron', lum=0.7)
    p.ellipse(90, 18, 18, 8, 'gold', lum=0.6)


@picture('scorched')
def _p(p):
    mats(p)
    for s in (-1, 1):
        p.limb(80 + s * 10, 108, 80 + s * 14, 132, 8, 6, 'scorch', tex=0.2)
        p.limb(80 + s * 14, 132, 80 + s * 12, 152, 6, 5, 'scorch', tex=0.2)
    p.poly([(56, 52), (104, 52), (108, 112), (52, 112)], 'cloth', lum=0.4,
           gradx=-0.3, tex=0.2)
    p.ellipse(80, 82, 18, 22, 'scorch', tex=0.3)
    for k in range(6):
        p.circle(66 + (k * 11) % 30, 70 + (k * 7) % 30, 2.5, 'toxic', lum=0.7)
    p.chain([(56, 56), (40, 80), (30, 92)], 7, 5, 'scorch', tex=0.2)
    p.chain([(104, 56), (120, 80), (130, 92)], 7, 5, 'scorch', tex=0.2)
    p.limb(80, 44, 80, 54, 6, 6, 'scorch')
    p.ellipse(80, 32, 15, 17, 'scorch', tex=0.3)
    eye(p, 73, 30, 3, 'toxic')
    eye(p, 87, 31, 3, 'toxic')
    p.ellipse(80, 42, 6, 4, 'mouth', lum=0.3)
    p.speckle('scorch', 0.2, 0.25)


@picture('giantant', 170, 120)
def _p(p):
    mats(p)
    for s in (-1, 1):
        for i in range(3):
            bx = 85 + (i - 1) * 22
            p.limb(bx, 66, bx + s * 0 + (i - 1) * 16, 40 if s < 0 else 92,
                   3.5, 3, 'antred')
    for i in range(3):
        bx = 85 + (i - 1) * 22
        p.chain([(bx, 70), (bx + (i - 1) * 18, 86), (bx + (i - 1) * 26, 118)],
                3.5, 1.5, 'antred')
    p.ellipse(130, 64, 30, 22, 'antred', tex=0.1)
    p.ellipse(86, 66, 20, 14, 'antred', tex=0.1)
    p.ellipse(48, 62, 18, 16, 'antred', tex=0.1)
    p.chain([(40, 50), (24, 30), (10, 26)], 2, 1, 'antred')
    p.chain([(48, 48), (40, 24), (28, 14)], 2, 1, 'antred')
    eye(p, 40, 58, 3.5, 'black')
    p.chain([(36, 72), (24, 80), (28, 88)], 3, 1, 'antred')
    p.chain([(44, 74), (36, 84), (42, 90)], 3, 1, 'antred')


@picture('thornwalker', 160, 170)
def _p(p):
    mats(p)
    for s in (-1, 1):
        for k in range(3):
            p.chain([(80, 120), (80 + s * (16 + k * 12), 140),
                     (80 + s * (24 + k * 14), 168)], 6 - k, 2, 'wood')
    p.limb(80, 124, 80, 60, 14, 10, 'leaf', tex=0.2)
    for s in (-1, 1):
        p.chain([(80, 80), (80 + s * 34, 66), (80 + s * 56, 86),
                 (80 + s * 62, 116)], 6, 2, 'leaf')
    for k in range(14):
        y = 66 + k * 4
        p.poly([(80 - 12, y), (80 - 20, y - 4), (80 - 12, y + 2)], 'bone',
               lum=0.8)
        p.poly([(80 + 12, y), (80 + 20, y - 4), (80 + 12, y + 2)], 'bone',
               lum=0.8)
    for k in range(8):
        a = k * math.pi / 4
        p.ellipse(80 + 22 * math.cos(a), 40 + 18 * math.sin(a), 14, 8,
                  'crimson', bias=0.05, angle=a)
    p.circle(80, 40, 14, 'gold', tex=0.2)
    p.ellipse(80, 42, 8, 6, 'mouth', lum=0.3)
    for k in range(-2, 3):
        p.poly([(80 + k * 3 - 1, 38), (80 + k * 3 + 1, 38), (80 + k * 3, 44)],
               'teeth', lum=0.9)


@picture('mindworm', 170, 130)
def _p(p):
    mats(p)
    p.chain([(160, 120), (130, 112), (100, 118), (72, 104), (56, 80)], 14, 20,
            'pink', tex=0.15)
    for k in range(6):
        x = 150 - k * 18
        p.ellipse(x, 116 - (k % 2) * 4, 10, 16, 'pink', bias=0.1)
    p.ellipse(56, 62, 34, 30, 'pink', tex=0.12)
    for k in range(5):
        p.chain([(40 + k * 8, 40), (34 + k * 9, 22), (40 + k * 9, 8)], 2, 1,
                'pink')
        p.circle(40 + k * 9, 8, 3, 'violetglow', lum=0.8)
    p.ellipse(42, 70, 14, 12, 'mouth', lum=0.3)
    for k in range(8):
        a = k * math.pi / 4
        p.poly([(42 + 13 * math.cos(a), 70 + 11 * math.sin(a)),
                (42 + 8 * math.cos(a + 0.2), 70 + 7 * math.sin(a + 0.2)),
                (42 + 13 * math.cos(a + 0.4), 70 + 11 * math.sin(a + 0.4))],
               'teeth', lum=0.9)
    eye(p, 60, 48, 5, 'violetglow')
    eye(p, 76, 52, 4, 'violetglow')


@picture('secbot', 160, 160)
def _p(p):
    mats(p)
    p.ellipse(80, 154, 40, 6, 'shadow', lum=0.1)
    p.rect(50, 118, 60, 34, 'iron', lum=0.45, gradx=-0.4)
    for x in range(54, 110, 9):
        p.circle(x, 146, 5, 'black', lum=0.4)
    p.rect(52, 52, 56, 68, 'olive', lum=0.55, gradx=-0.4)
    trefoil(p, 80, 86, 9, 'black', 'gold')
    for s in (-1, 1):
        p.rect(80 + s * 40 - 10, 58, 20, 18, 'olive', lum=0.5)
        p.limb(80 + s * 40, 76, 80 + s * 46, 106, 7, 6, 'iron')
        p.rect(80 + s * 46 - 4, 104, 8, 20, 'iron', lum=0.6)
    p.ellipse(80, 40, 20, 14, 'olive', bias=0.05)
    p.rect(64, 36, 32, 7, 'shadow', lum=0.0)
    eye(p, 80, 39, 3.5, 'eyered')
    p.line(80, 26, 80, 12, 'iron', 0.5, 2)
    p.circle(80, 11, 3, 'eyered', lum=0.9)


@picture('drone', 140, 100)
def _p(p):
    mats(p)
    for s in (-1, 1):
        p.line(70 + s * 20, 46, 70 + s * 52, 30, 'iron', 0.5, 3)
        p.ellipse(70 + s * 52, 28, 18, 4, 'robot', lum=0.5)
    p.ellipse(70, 50, 26, 18, 'robot', tex=0.05)
    p.ellipse(70, 60, 14, 8, 'shadow', lum=0.1)
    eye(p, 70, 60, 4.5, 'eyecyan')
    p.line(60, 68, 52, 90, 'iron', 0.5, 2)
    p.line(80, 68, 88, 90, 'iron', 0.5, 2)


@picture('snapper', 200, 150)
def _p(p):
    mats(p)
    for (x, y) in ((44, 120), (156, 120), (60, 74), (150, 78)):
        p.ellipse(x, y, 18, 12, 'shell', tex=0.15)
    p.ellipse(108, 90, 78, 46, 'shell', tex=0.12)
    for k in range(5):
        for j in range(3):
            p.ellipse(60 + k * 24, 70 + j * 18, 10, 7, 'shell', bias=0.15)
    p.ellipse(108, 128, 76, 10, 'sand', bias=-0.1)
    p.chain([(40, 90), (24, 82), (16, 72)], 14, 12, 'shell', tex=0.1)
    p.ellipse(16, 62, 24, 18, 'shell', tex=0.1)
    p.poly([(-4, 66), (16, 74), (4, 82)], 'bone', lum=0.75)
    p.poly([(-4, 56), (14, 56), (4, 66)], 'bone', lum=0.65)
    eye(p, 20, 52, 4, 'eyegold')
    for k in range(4):
        p.circle(90 + k * 18, 52 + (k % 2) * 6, 4, 'toxic', lum=0.6)


@picture('guardian', 210, 180, height=0.84)
def _p(p):
    mats(p)
    p.rect(40, 140, 130, 36, 'iron', lum=0.4, gradx=-0.3)
    for x in range(46, 170, 12):
        p.circle(x, 170, 6, 'black', lum=0.4)
    p.poly([(60, 60), (150, 60), (160, 142), (50, 142)], 'olive', lum=0.55,
           gradx=-0.4, tex=0.05)
    p.rect(66, 84, 78, 30, 'shadow', lum=0.06)
    for k in range(6):
        p.rect(72 + k * 12, 92, 8, 14, 'eyered' if k % 2 else 'eyegold',
               lum=0.5)
    for s in (-1, 1):
        p.ellipse(105 + s * 62, 70, 26, 20, 'olive', tex=0.05)
        p.rect(105 + s * 62 - 14, 86, 28, 40, 'iron', lum=0.5, gradx=-0.4)
        for k in range(3):
            p.line(105 + s * 62 - 8 + k * 8, 126, 105 + s * 62 - 8 + k * 8,
                   150, 'steel', 0.8, 4)
    p.ellipse(105, 40, 34, 24, 'olive', bias=0.05)
    p.rect(80, 34, 50, 10, 'shadow', lum=0.0)
    eye(p, 105, 38, 5, 'eyered')
    trefoil(p, 105, 74, 8, 'black', 'gold')
    for s in (-1, 1):
        p.line(105 + s * 20, 20, 105 + s * 30, 2, 'iron', 0.5, 2)
        p.circle(105 + s * 30, 2, 3, 'eyered', lum=0.9)


# --------------------------------------------------------- the people

@picture('elder_face')
def _p(p):
    mats(p)
    person(p, skin='darkskin', robe='scorch', trim='gold', hair='greyhair',
           eyes='leaf', hood=True)
    p.circle(80, 122, 6, 'water', lum=0.7)


@picture('trader_face')
def _p(p):
    mats(p)
    person(p, skin='green', robe='denim', trim=None, bald=True, eyes='eyegold')
    for s in (-1, 1):
        p.poly([(80 + s * 18, 44), (80 + s * 30, 30), (80 + s * 22, 52)],
               'green', lum=0.55)
    p.rect(60, 116, 40, 6, 'leather', lum=0.5)


@picture('healer_face')
def _p(p):
    mats(p)
    person(p, skin='leaf', robe='white', trim='leaf', hair='leaf',
           eyes='eyegold')
    for k in range(6):
        a = k * math.pi / 3
        p.ellipse(80 + 26 * math.cos(a), 44 + 10 * math.sin(a), 8, 4,
                  'crimson', bias=0.1, angle=a)


@picture('keeper_face')
def _p(p):
    mats(p)
    person(p, skin='skin', robe='leather', trim=None, apron='cloth',
           bald=True, beard='redhair', eyes='blue')


@picture('mags_face')
def _p(p):
    mats(p)
    person(p, skin='paleskin', robe='scrap', trim=None, hair='greyhair',
           eyes='blue')
    p.rect(58, 50, 44, 8, 'leather', lum=0.4)
    for s in (-1, 1):
        p.circle(80 + s * 10, 54, 7, 'gold')
        p.circle(80 + s * 10, 54, 5, 'glass', lum=0.6)


@picture('nomad_face')
def _p(p):
    mats(p)
    person(p, skin='darkskin', robe='sand', trim=None, hood=True, eyes='leaf')
    p.rect(62, 70, 36, 14, 'sand', lum=0.45)


@picture('robo_face')
def _p(p):
    mats(p)
    p.rect(30, 100, 100, 60, 'robot', lum=0.55, gradx=-0.4)
    p.ellipse(80, 66, 46, 36, 'robot', bias=0.05)
    p.rect(46, 54, 68, 18, 'shadow', lum=0.05)
    eye(p, 62, 62, 6, 'eyecyan')
    eye(p, 98, 62, 6, 'eyecyan')
    p.rect(64, 86, 32, 4, 'eyecyan', lum=0.5)
    p.line(80, 30, 80, 14, 'iron', 0.5, 2)
    p.circle(80, 12, 4, 'eyegreen', lum=0.9)


@picture('nomad', 48, 124, height=0.62)
def _p(p):
    mats(p)
    standing(p, 24, 'sand', skin='darkskin', hood=True, staff=True)


@picture('hermit_face')
def _p(p):
    mats(p)
    person(p, skin='paleskin', robe='olive', trim=None, hair='greyhair',
           beard='greyhair', eyes='eyegreen', long_hair=True)
    for k in range(5):
        p.circle(56 + k * 12, 112 + (k % 2) * 4, 3, 'toxic', lum=0.7)


@picture('hermit', 48, 124, height=0.6)
def _p(p):
    mats(p)
    standing(p, 24, 'olive', skin='paleskin', hair='greyhair',
             beard='greyhair', staff=True)


@picture('dw_ornament', 44, 40)
def _p(p):
    mats(p)
    p.rect(4, 6, 36, 28, 'scrap', lum=0.45, tex=0.2)
    for x in (7, 37):
        for y in (9, 31):
            p.circle(x, y, 1.5, 'iron', lum=0.3)
    trefoil(p, 22, 20, 11, 'black', 'gold')


# --------------------------------------------------------- title, icon

@picture('dw_title', 200, 180)
def _p(p):
    mats(p)
    p.rect(0, 0, 200, 110, 'flame', lum=0.25, grad=0.5)
    p.circle(140, 70, 26, 'flame', lum=0.75)
    for (x, w, h) in ((10, 20, 50), (34, 16, 70), (54, 24, 40), (82, 14, 80),
                      (100, 22, 56), (128, 18, 66), (150, 26, 48),
                      (178, 18, 60)):
        p.rect(x, 110 - h, w, h, 'shadow', lum=0.08)
        for k in range(3):
            p.rect(x + 4, 110 - h + 8 + k * 14, 4, 6, 'flame', lum=0.4)
    p.rect(0, 108, 200, 72, 'sand', lum=0.5, grad=0.4, tex=0.08)
    standing(p, 70, 'leather', skin='skin', hair='hair', staff=True)
    standing(p, 100, 'denim', skin='green', hood=True)
    p.chain([(128, 120), (140, 100)], 3, 3, 'scorch')
    standing(p, 128, 'scorch', skin='scorch', hair='black')
    for k in range(3):
        p.rect(64 + k * 30, 30, 2, 2, 'white', lum=0.4)


@picture('dw_icon', 64, 64)
def _p(p):
    mats(p)
    p.rect(2, 2, 60, 60, 'flame', lum=0.4, grad=0.4)
    trefoil(p, 32, 30, 18, 'black', 'gold')
    p.ellipse(32, 46, 9, 12, 'water', lum=0.6)
    p.poly([(32, 30), (25, 44), (39, 44)], 'water', lum=0.6)
    p.circle(29, 46, 2, 'white', lum=1.0)

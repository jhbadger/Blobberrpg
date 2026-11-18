"""Wall, floor and ceiling textures, all drawn in code.

A texture is a list of T*T (r, g, b) tuples, row-major.  Textures are made
on first use from a registry of generators, so a game can add its own with
@texture('name').
"""

import math
import random

from .gfx import rgb, mix, scale
from .paint import Painter

T = 64

_GEN = {}
_CACHE = {}


def texture(name):
    def deco(fn):
        _GEN[name] = fn
        return fn
    return deco


def get(name):
    px = _CACHE.get(name)
    if px is None:
        if name not in _GEN:
            raise KeyError('no texture called %r' % name)
        px = _GEN[name]()
        _CACHE[name] = px
    return px


def names():
    return sorted(_GEN)


# ---------------------------------------------------------------- helpers


def fbm(rng, octaves=((4, 0.55), (8, 0.3), (16, 0.15))):
    """Tileable value noise in [0, 1], T*T values."""
    out = [0.0] * (T * T)
    for period, amp in octaves:
        g = [rng.random() for _ in range(period * period)]
        for y in range(T):
            fy = y * period / T
            y0 = int(fy)
            ty = fy - y0
            ty = ty * ty * (3 - 2 * ty)
            y1 = (y0 + 1) % period
            for x in range(T):
                fx = x * period / T
                x0 = int(fx)
                tx = fx - x0
                tx = tx * tx * (3 - 2 * tx)
                x1 = (x0 + 1) % period
                a = g[y0 * period + x0] + (g[y0 * period + x1] -
                                           g[y0 * period + x0]) * tx
                b = g[y1 * period + x0] + (g[y1 * period + x1] -
                                           g[y1 * period + x0]) * tx
                out[y * T + x] += (a + (b - a) * ty) * amp
    return out


def blocks(rng, bands, wmin, wmax, gap=1, round_=2):
    """An irregular stone-block layout.  Returns per-pixel (block id or -1
    for mortar, distance from the block's top/left edge, distance from its
    bottom/right edge)."""
    info = [(-1, 0, 0)] * (T * T)
    bid = 0
    y = 0
    for bh in bands:
        widths = []
        while sum(widths) < T:
            widths.append(rng.randint(wmin, wmax))
        widths[-1] -= sum(widths) - T
        if widths[-1] < wmin // 2 and len(widths) > 1:
            widths[-2] += widths.pop()
        off = rng.randint(0, T - 1)
        x = 0
        for bw in widths:
            for yy in range(bh):
                for xx in range(bw):
                    if yy >= bh - gap or xx >= bw - gap:
                        continue
                    # round the corners
                    cx = min(xx, bw - gap - 1 - xx)
                    cy = min(yy, bh - gap - 1 - yy)
                    if cx < round_ and cy < round_ and \
                            (round_ - cx) ** 2 + (round_ - cy) ** 2 > round_ * round_ + 1:
                        continue
                    top = min(xx, yy)
                    bot = min(bw - gap - 1 - xx, bh - gap - 1 - yy)
                    px = (off + x + xx) % T
                    info[(y + yy) * T + px] = (bid, top, bot)
            x += bw
            bid += 1
        y += bh
    return info, bid


def stone_wall(seed, base, mortar, bands, wmin, wmax, jitter=0.16,
               noise=0.35, gap=1, round_=2, hue=None):
    rng = random.Random(seed)
    info, nb = blocks(rng, bands, wmin, wmax, gap, round_)
    n = fbm(rng)
    n2 = fbm(rng, ((16, 0.6), (32, 0.4)))
    tints = []
    for _ in range(nb):
        f = 1 + (rng.random() - 0.5) * 2 * jitter
        t = base
        if hue and rng.random() < 0.35:
            t = mix(base, hue, rng.random() * 0.5)
        tints.append((t, f))
    base, mortar = rgb(base), rgb(mortar)
    px = []
    for i in range(T * T):
        b, top, bot = info[i]
        if b < 0:
            px.append(scale(mortar, 0.7 + 0.5 * n[i]))
            continue
        col, f = tints[b]
        f *= 1 - noise / 2 + noise * (0.6 * n[i] + 0.4 * n2[i])
        if top == 0:
            f *= 1.28
        elif top == 1:
            f *= 1.12
        if bot == 0:
            f *= 0.6
        elif bot == 1:
            f *= 0.8
        px.append(scale(col, f))
    # chips and pits
    for _ in range(40):
        x, y = rng.randrange(T), rng.randrange(T)
        if info[y * T + x][0] >= 0:
            px[y * T + x] = scale(px[y * T + x], 0.55)
            if x + 1 < T:
                px[y * T + x + 1] = scale(px[y * T + x + 1], 1.15)
    return px


def brick_wall(seed, base, mortar, bw=16, bh=8, gap=1, jitter=0.14):
    rng = random.Random(seed)
    n = fbm(rng)
    shades = {}
    base, mortar = rgb(base), rgb(mortar)
    px = []
    for y in range(T):
        r = y // bh
        yy = y % bh
        off = bw // 2 if r % 2 else 0
        for x in range(T):
            xx = (x + off) % bw
            c = ((x + off) // bw) % (T // bw)
            i = y * T + x
            if yy >= bh - gap or xx >= bw - gap:
                px.append(scale(mortar, 0.7 + 0.5 * n[i]))
                continue
            f = shades.get((r, c))
            if f is None:
                f = shades[(r, c)] = 1 + (rng.random() - 0.5) * 2 * jitter
            f *= 0.78 + 0.44 * n[i]
            if yy == 0 or xx == 0:
                f *= 1.22
            if yy == bh - gap - 1 or xx == bw - gap - 1:
                f *= 0.74
            px.append(scale(base, f))
    for _ in range(50):
        x, y = rng.randrange(T), rng.randrange(T)
        px[y * T + x] = scale(px[y * T + x], 0.6)
    return px


def cobbles(seed, base, gap_col, cells=6, jitter=0.2):
    """Rounded cobblestones: a tileable Voronoi pattern."""
    rng = random.Random(seed)
    pts = []
    for j in range(cells):
        for i in range(cells):
            pts.append(((i + 0.2 + rng.random() * 0.6) * T / cells,
                        (j + 0.2 + rng.random() * 0.6) * T / cells,
                        1 + (rng.random() - 0.5) * 2 * jitter))
    n = fbm(rng, ((8, 0.5), (32, 0.5)))
    base, gap_col = rgb(base), rgb(gap_col)
    px = []
    for y in range(T):
        for x in range(T):
            best = second = 1e9
            bf = 1
            for (cx, cy, f) in pts:
                dx = abs(x + 0.5 - cx)
                dy = abs(y + 0.5 - cy)
                dx = min(dx, T - dx)
                dy = min(dy, T - dy)
                d = math.sqrt(dx * dx + dy * dy)
                if d < best:
                    second = best
                    best, bf = d, f
                elif d < second:
                    second = d
            edge = second - best
            i = y * T + x
            if edge < 1.6:
                px.append(scale(gap_col, 0.8 + 0.4 * n[i]))
            else:
                k = min(1.0, (edge - 1.6) / 5)
                f = bf * (0.62 + 0.38 * k) * (0.8 + 0.35 * n[i])
                px.append(scale(base, f))
    return px


def tint(px, colour, amount, test):
    colour = rgb(colour)
    for y in range(T):
        for x in range(T):
            if test(x, y):
                i = y * T + x
                px[i] = mix(px[i], colour, amount)


def moss(px, seed, colour='#3e6a24', amount=0.55, where='top'):
    rng = random.Random(seed)
    n = fbm(rng, ((4, 0.4), (8, 0.35), (32, 0.25)))
    for y in range(T):
        bias = (1 - y / T) if where == 'top' else (y / T) if where == 'bottom' else 0.5
        for x in range(T):
            v = n[y * T + x] + bias * 0.45 - 0.62
            if v > 0:
                i = y * T + x
                k = min(1.0, v * 5)
                c = scale(colour, 0.7 + 0.6 * rng.random())
                px[i] = mix(px[i], c, amount * k + 0.25 * (k > 0.5))
    return px


def cracks(px, seed, n=3, colour='#100c0a', glow=None):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.uniform(4, T - 4), rng.uniform(4, T - 4)
        a = rng.uniform(0, math.tau)
        for _ in range(rng.randint(12, 30)):
            xi, yi = int(x) % T, int(y) % T
            if glow:
                px[yi * T + xi] = rgb(glow)
                for (ox, oy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    j = ((yi + oy) % T) * T + (xi + ox) % T
                    px[j] = mix(px[j], glow, 0.35)
            else:
                px[yi * T + xi] = rgb(colour)
            a += rng.uniform(-0.7, 0.7)
            x += math.cos(a)
            y += math.sin(a)
    return px


def overlay(px, painter, ox=0, oy=0):
    """Composite a Painter's picture over a texture."""
    img = painter.image(outline='#0a0806')
    for j, runs in enumerate(img.rows):
        y = oy + j
        if not 0 <= y < T:
            continue
        for x0, b in runs:
            for k in range(len(b) // 3):
                x = ox + x0 + k
                if 0 <= x < T:
                    px[y * T + x] = (b[3 * k], b[3 * k + 1], b[3 * k + 2])
    return px


def glow_at(px, cx, cy, r, colour, amount):
    colour = rgb(colour)
    for y in range(max(0, int(cy - r)), min(T, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(T, int(cx + r) + 1)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
            if d < 1:
                i = y * T + x
                px[i] = mix(px[i], scale(colour, 1.0), amount * (1 - d) ** 2)


# ---------------------------------------------------------------- props


def sconce(px, seed=1):
    glow_at(px, 32, 22, 26, '#ffb050', 0.55)
    p = Painter(T, T, seed)
    p.rect(29, 30, 6, 16, 'wood', lum=0.5, gradx=0.4)
    p.rect(27, 28, 10, 4, 'iron', lum=0.55, grad=0.3)
    p.rect(30, 44, 4, 8, 'iron', lum=0.4)
    p.rect(26, 50, 12, 3, 'iron', lum=0.5)
    p.ellipse(32, 21, 6, 10, 'flame', lum=0.55)
    p.ellipse(32, 23, 4, 6, 'flame', lum=0.8)
    p.ellipse(32, 25, 2, 3, 'flame', lum=1.0)
    p.glow.add('flame')
    return overlay(px, p)


def skull_niche(px, seed=2):
    p = Painter(T, T, seed)
    p.ellipse(32, 24, 14, 12, 'shadow', lum=0.2)
    p.rect(18, 24, 28, 22, 'shadow', lum=0.15, grad=-0.15)
    # bones lying in the niche
    p.limb(21, 43, 42, 41, 2, 2, 'bone', bias=-0.1)
    p.circle(20, 43, 2.5, 'bone', bias=-0.1)
    p.circle(43, 41, 2.5, 'bone', bias=-0.1)
    skull(p, 32, 34, 8, bias=-0.05)
    return overlay(px, p)


def skull(p, cx, cy, r, bias=0.0, eyes='shadow', eye_lum=0.1):
    p.ellipse(cx, cy, r, r * 0.92, 'bone', bias=bias)
    p.ellipse(cx, cy + r * 0.85, r * 0.62, r * 0.42, 'bone', bias=bias - 0.08)
    p.ellipse(cx - r * 0.38, cy + r * 0.1, r * 0.27, r * 0.3, eyes, lum=eye_lum)
    p.ellipse(cx + r * 0.38, cy + r * 0.1, r * 0.27, r * 0.3, eyes, lum=eye_lum)
    p.poly([(cx, cy + r * 0.38), (cx - r * 0.12, cy + r * 0.62),
            (cx + r * 0.12, cy + r * 0.62)], 'shadow', lum=0.1)
    for k in (-2, -1, 0, 1, 2):
        p.line(cx + k * r * 0.17, cy + r * 0.75, cx + k * r * 0.17,
               cy + r * 1.05, 'shadow', lum=0.15)


def banner(px, cloth='red', emblem='gold', seed=3):
    p = Painter(T, T, seed)
    p.limb(16, 6, 48, 6, 1.6, 1.6, 'wood')
    p.poly([(20, 7), (44, 7), (44, 50), (32, 58), (20, 50)], cloth, lum=0.55,
           gradx=-0.35, grad=-0.2)
    for x in (24, 30, 36, 41):
        p.line(x, 9, x, 49, cloth, lum=0.38)
    p.circle(32, 26, 7, emblem)
    p.circle(32, 26, 3.5, cloth, lum=0.4)
    p.poly([(20, 50), (32, 58), (44, 50), (44, 52), (32, 60), (20, 52)],
           'gold', lum=0.6)
    return overlay(px, p)


def door_overlay(px, frame='stone', wood='wood', locked=False, seed=4,
                 arch=True):
    p = Painter(T, T, seed)
    # frame
    if arch:
        p.ellipse(32, 22, 22, 18, frame, bias=0.05)
        p.rect(10, 22, 44, 42, frame, lum=0.55, gradx=-0.2)
        p.ellipse(32, 23, 18, 15, 'shadow', lum=0.1)
        p.rect(14, 23, 36, 41, 'shadow', lum=0.1)
        for (x0, y0, x1, y1) in ((12, 30, 14, 31), (50, 30, 52, 31),
                                 (12, 44, 14, 45), (50, 44, 52, 45)):
            p.rect(x0, y0, x1 - x0, 1, frame, lum=0.3)
    # planks
    top = 24
    p.ellipse(32, 24, 16, 13, wood, lum=0.5)
    p.rect(16, top, 32, 40, wood, lum=0.5, gradx=-0.25)
    for x in range(16, 48, 6):
        p.rect(x, 11, 1, 53, 'shadow', lum=0.2)
        p.rect(x + 1, 11, 1, 53, wood, lum=0.62)
    # iron bands and studs
    for y in (26, 50):
        p.rect(16, y, 32, 4, 'iron', lum=0.5, grad=0.4)
        for x in range(19, 47, 6):
            p.circle(x, y + 2, 1.2, 'iron', lum=0.85)
    p.circle(42, 40, 3.2, 'iron', lum=0.55)
    p.circle(42, 40, 1.8, wood, lum=0.4)
    if locked:
        p.rect(26, 34, 12, 12, 'iron', lum=0.6, grad=0.3)
        p.circle(32, 39, 1.8, 'shadow', lum=0.0)
        p.rect(31, 39, 2, 4, 'shadow', lum=0.0)
    # trim the plank top to the arch
    for y in range(T):
        for x in range(T):
            dx, dy = (x + 0.5 - 32) / 16, (y + 0.5 - 24) / 13
            if y < 24 and dx * dx + dy * dy > 1 and 16 <= x < 48:
                i = y * T + x
                if p.mat[i] in (wood, 'iron'):
                    p.mat[i] = 'shadow'
                    p.lum[i] = 0.1
    return overlay(px, p)


def runes(px, colour='#b070ff', seed=5):
    rng = random.Random(seed)
    glow_at(px, 32, 32, 30, colour, 0.25)
    for k in range(5):
        cx = 12 + k * 10
        cy = 30 + rng.randint(-3, 3)
        for _ in range(3):
            x0, y0 = cx + rng.randint(-3, 3), cy + rng.randint(-6, 6)
            x1, y1 = cx + rng.randint(-3, 3), cy + rng.randint(-6, 6)
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for s in range(steps + 1):
                x = int(x0 + (x1 - x0) * s / steps)
                y = int(y0 + (y1 - y0) * s / steps)
                px[y * T + x] = rgb('#f0d8ff')
                for (ox, oy) in ((1, 0), (0, 1)):
                    j = (y + oy) * T + x + ox
                    px[j] = mix(px[j], colour, 0.6)
    return px


# ------------------------------------------------- dungeon: the undercroft

def _cellar():
    return brick_wall(11, '#7a3e30', '#2a1a16', bw=16, bh=8)


@texture('cellar')
def _t():
    return _cellar()


@texture('cellar_moss')
def _t():
    return moss(_cellar(), 12, '#4a6a2a', 0.5, 'bottom')


@texture('cellar_torch')
def _t():
    return sconce(_cellar())


@texture('cellar_crack')
def _t():
    return cracks(_cellar(), 13, 4)


@texture('cellar_door')
def _t():
    return door_overlay(_cellar(), 'stone')


@texture('cellar_locked')
def _t():
    return door_overlay(_cellar(), 'stone', locked=True)


@texture('cellar_banner')
def _t():
    return banner(_cellar(), 'crimson')


@texture('cellar_runes')
def _t():
    return runes(_cellar(), '#ff7040')


@texture('cellar_floor')
def _t():
    px = stone_wall(14, '#6a3424', '#2a140c', [16, 16, 16, 16], 14, 22,
                    noise=0.4, round_=1)
    rng = random.Random(15)
    # dead leaves and grit
    for _ in range(220):
        x, y = rng.randrange(T), rng.randrange(T)
        px[y * T + x] = rgb(rng.choice(['#8a2a14', '#a83c18', '#5a1c0c',
                                         '#c05020']))
    return px


@texture('cellar_ceil')
def _t():
    return brick_wall(16, '#4a2a24', '#1a100c', bw=32, bh=16, gap=2)


@texture('stairs_down')
def _t():
    px = list(get('cellar_floor'))
    for y in range(10, 56):
        for x in range(10, 54):
            step = (y - 10) // 9
            f = 0.55 - step * 0.1
            if (y - 10) % 9 == 0:
                f += 0.25
            px[y * T + x] = scale('#5a4a40', max(0.04, f))
    return px


# ------------------------------------------------ dungeon: the catacombs

def _cata():
    return stone_wall(21, '#6c6a66', '#24221f', [14, 18, 16, 16], 14, 30,
                      hue='#6a6450')


@texture('cata')
def _t():
    return _cata()


@texture('cata_niche')
def _t():
    return skull_niche(_cata())


@texture('cata_moss')
def _t():
    return moss(_cata(), 22, '#5a7a3a', 0.45, 'top')


@texture('cata_torch')
def _t():
    return sconce(_cata())


@texture('cata_door')
def _t():
    return door_overlay(_cata(), 'stone', 'wood')


@texture('cata_locked')
def _t():
    return door_overlay(_cata(), 'stone', 'wood', locked=True)


@texture('cata_runes')
def _t():
    return runes(_cata(), '#a060ff')


@texture('cata_floor')
def _t():
    return stone_wall(23, '#5a5852', '#22201c', [16, 16, 16, 16], 16, 32,
                      noise=0.45, round_=1)


@texture('cata_ceil')
def _t():
    return stone_wall(24, '#3a3834', '#121110', [20, 22, 22], 18, 34,
                      noise=0.5)


@texture('cata_stairs')
def _t():
    px = list(get('cata_floor'))
    for y in range(10, 56):
        for x in range(10, 54):
            step = (y - 10) // 9
            f = 0.55 - step * 0.1 + (0.25 if (y - 10) % 9 == 0 else 0)
            px[y * T + x] = scale('#605c56', max(0.04, f))
    return px


# ---------------------------------------------- dungeon: the ashen halls

def _ashen():
    return stone_wall(31, '#3a3236', '#0c0a0a', [22, 20, 22], 20, 36,
                      hue='#4a2a2a', noise=0.4)


@texture('ashen')
def _t():
    return _ashen()


@texture('ashen_ember')
def _t():
    return cracks(_ashen(), 32, 3, glow='#ff7a1c')


@texture('ashen_torch')
def _t():
    return sconce(_ashen())


@texture('ashen_banner')
def _t():
    return banner(_ashen(), 'black', 'red')


@texture('ashen_door')
def _t():
    return door_overlay(_ashen(), 'darksteel', 'iron')


@texture('ashen_locked')
def _t():
    return door_overlay(_ashen(), 'darksteel', 'iron', locked=True)


@texture('ashen_runes')
def _t():
    return runes(_ashen(), '#ff3020')


@texture('ashen_floor')
def _t():
    px = stone_wall(33, '#2c2628', '#0a0808', [16, 16, 16, 16], 16, 16,
                    noise=0.3, round_=0, jitter=0.1)
    return cracks(px, 34, 2, glow='#c84a10')


@texture('ashen_ceil')
def _t():
    return stone_wall(35, '#221c1e', '#060404', [32, 32], 24, 40, noise=0.5)


@texture('ashen_stairs')
def _t():
    px = list(get('ashen_floor'))
    for y in range(10, 56):
        for x in range(10, 54):
            step = (y - 10) // 9
            f = 0.5 - step * 0.09 + (0.25 if (y - 10) % 9 == 0 else 0)
            px[y * T + x] = scale('#4a3a3a', max(0.04, f))
    return px


# ---------------------------------------------------------------- the town

def _plaster(seed, colour):
    rng = random.Random(seed)
    n = fbm(rng, ((8, 0.5), (32, 0.5)))
    return [scale(colour, 0.86 + 0.22 * v) for v in n]


def _timber_frame(px, seed, timber, braces=True, plinth='#6a6a6a'):
    rng = random.Random(seed)
    timber = rgb(timber)

    def beam(x0, y0, x1, y1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                edge = y == y0 or x == x0
                f = (1.2 if edge else 0.9) * (0.85 + 0.3 * rng.random())
                px[y * T + x] = scale(timber, f)

    for (x0, x1) in ((0, 4), (60, 64)):
        beam(x0, 0, x1, 58)
    beam(0, 0, 64, 4)
    beam(0, 30, 64, 34)
    beam(0, 54, 64, 58)
    if braces:
        for t in range(0, 20):
            for k in range(3):
                x, y = 5 + t * 12 // 20 + k, 35 + t
                if y < 54:
                    px[y * T + x] = scale(timber, 0.9)
                x2 = 58 - t * 12 // 20 - k
                if y < 54:
                    px[y * T + x2] = scale(timber, 0.9)
    stones = stone_wall(seed + 1, plinth, '#2a2a2a', [6], 8, 14, round_=1)
    for y in range(58, 64):
        for x in range(T):
            px[y * T + x] = stones[(y - 58) * T + x]
    return px


def _window(px, x0, y0, w, h, lit, timber='#3a2414', seed=0):
    rng = random.Random(seed)
    glass = '#f8c860' if lit else '#40607a'
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            i = y * T + x
            if x in (x0, x0 + 1, x0 + w - 1, x0 + w - 2) or \
                    y in (y0, y0 + 1, y0 + h - 1, y0 + h - 2) or \
                    x in (x0 + w // 2, x0 + w // 2 - 1) or \
                    y == y0 + h // 2:
                px[i] = scale(timber, 0.8 + 0.3 * rng.random())
            else:
                f = 1.0 + 0.35 * (((x - x0) - (y - y0)) % 9 < 2) \
                    - 0.25 * ((y - y0) / h)
                px[i] = scale(glass, f)
    # sill
    for x in range(x0 - 2, x0 + w + 2):
        px[(y0 + h) * T + x] = scale('#8a8a84', 1.0)
    if lit:
        glow_at(px, x0 + w / 2, y0 + h / 2, w, '#ffc860', 0.18)
    return px


def house(seed, plaster, timber, lit=False, stone_base=False,
          window2=False):
    px = _plaster(seed, plaster)
    if stone_base:
        st = stone_wall(seed + 7, '#7a766c', '#3a3630', [10, 10, 10, 6], 10,
                        18, round_=1)
        for y in range(32, 64):
            for x in range(T):
                px[y * T + x] = st[(y - 32) * T + x]
    px = _timber_frame(px, seed, timber, braces=not stone_base)
    _window(px, 20, 8, 24, 20, lit, timber, seed)
    if window2 and not stone_base:
        _window(px, 22, 37, 20, 14, not lit, timber, seed + 1)
    return px


@texture('house_a')
def _t():
    return house(41, '#d8ccb0', '#4a2c18')


@texture('house_b')
def _t():
    return house(42, '#c8b490', '#3a2010', lit=True, window2=True)


@texture('house_c')
def _t():
    return house(43, '#e0d8c8', '#5a3418', stone_base=True)


@texture('house_d')
def _t():
    px = brick_wall(44, '#8a4a34', '#3a2a22', bw=12, bh=6)
    _window(px, 12, 12, 16, 18, False, '#3a2414', 44)
    _window(px, 36, 12, 16, 18, True, '#3a2414', 45)
    return px


@texture('citywall')
def _t():
    px = stone_wall(45, '#8a8680', '#3a3834', [20, 22, 22], 18, 30,
                    hue='#8a8070')
    return moss(px, 46, '#4a6a2a', 0.45, 'bottom')


@texture('cobbles')
def _t():
    return cobbles(47, '#8a8070', '#3a342c', cells=6)


def _sign_facade(seed, plaster, timber, board, icon):
    px = house(seed, plaster, timber, stone_base=True)
    # replace the window with a door
    px = door_overlay(px, 'stone', 'wood', arch=True, seed=seed)
    p = Painter(T, T, seed)
    p.limb(40, 6, 60, 6, 1.2, 1.2, 'iron')
    p.line(44, 6, 44, 10, 'iron', 0.5)
    p.line(56, 6, 56, 10, 'iron', 0.5)
    p.rect(40, 10, 20, 16, board, lum=0.5, grad=-0.3)
    p.rect(40, 10, 20, 1, 'gold', lum=0.7)
    p.rect(40, 25, 20, 1, 'gold', lum=0.4)
    icon(p, 50, 18)
    return overlay(px, p)


def _icon_swords(p, cx, cy):
    p.line(cx - 6, cy + 6, cx + 6, cy - 6, 'steel', 0.85, 2)
    p.line(cx + 6, cy + 6, cx - 6, cy - 6, 'steel', 0.85, 2)
    p.line(cx - 6, cy + 3, cx - 3, cy + 6, 'gold', 0.7, 2)
    p.line(cx + 6, cy + 3, cx + 3, cy + 6, 'gold', 0.7, 2)


def _icon_shield(p, cx, cy):
    p.poly([(cx - 6, cy - 6), (cx + 6, cy - 6), (cx + 6, cy), (cx, cy + 7),
            (cx - 6, cy)], 'steel', lum=0.7, gradx=-0.4)
    p.rect(cx - 1, cy - 5, 2, 10, 'red', lum=0.6)
    p.rect(cx - 5, cy - 2, 10, 2, 'red', lum=0.6)


def _icon_tankard(p, cx, cy):
    p.rect(cx - 5, cy - 5, 9, 12, 'wood', lum=0.6, gradx=-0.4)
    p.ellipse(cx, cy - 6, 5, 2, 'white', lum=0.9)
    p.limb(cx + 5, cy - 2, cx + 5, cy + 4, 1.5, 1.5, 'iron')
    p.rect(cx - 5, cy - 1, 9, 1, 'iron', lum=0.4)


def _icon_eye(p, cx, cy):
    p.ellipse(cx, cy, 7, 4, 'white', lum=0.9)
    p.circle(cx, cy, 3, 'blue', lum=0.6)
    p.circle(cx, cy, 1.4, 'shadow', lum=0.0)


@texture('shop_guild')
def _t():
    return _sign_facade(51, '#d4c8a8', '#3a2414', 'blue', _icon_swords)


@texture('shop_armory')
def _t():
    return _sign_facade(52, '#ccbca0', '#4a2c18', 'black', _icon_shield)


@texture('shop_inn')
def _t():
    return _sign_facade(53, '#dccca4', '#4a2c18', 'leaf', _icon_tankard)


@texture('shop_sage')
def _t():
    return _sign_facade(54, '#b8b0c8', '#2a2034', 'purple', _icon_eye)


@texture('shop_temple')
def _t():
    px = stone_wall(55, '#d8d4c8', '#7a766c', [16, 16, 16, 16], 20, 32,
                    jitter=0.06, noise=0.2)
    px = door_overlay(px, 'white', 'wood', seed=55)
    p = Painter(T, T, 55)
    p.circle(32, 8, 6, 'gold')
    for a in range(8):
        ang = a * math.pi / 4
        p.line(32 + 7 * math.cos(ang), 8 + 7 * math.sin(ang),
               32 + 10 * math.cos(ang), 8 + 10 * math.sin(ang), 'gold', 0.8, 1.5)
    return overlay(px, p)


@texture('crypt_gate')
def _t():
    px = stone_wall(56, '#5a5654', '#1a1818', [16, 16, 16, 16], 16, 28,
                    noise=0.5)
    moss(px, 57, '#3a5a24', 0.5, 'bottom')
    p = Painter(T, T, 56)
    p.ellipse(32, 26, 20, 20, 'stone', bias=-0.05)
    p.rect(12, 26, 40, 38, 'stone', lum=0.45, gradx=-0.2)
    p.ellipse(32, 27, 16, 16, 'shadow', lum=0.04)
    p.rect(16, 27, 32, 37, 'shadow', lum=0.04)
    for x in range(18, 48, 5):
        p.rect(x, 12, 2, 52, 'iron', lum=0.5, gradx=0.6)
    for y in (24, 44):
        p.rect(16, y, 32, 2, 'iron', lum=0.55)
    for y in range(T):
        for x in range(T):
            dx, dy = (x + 0.5 - 32) / 16, (y + 0.5 - 27) / 16
            if y < 27 and dx * dx + dy * dy > 1 and p.mat[y * T + x] == 'iron':
                p.mat[y * T + x] = 'stone'
                p.lum[y * T + x] = 0.45
    skull(p, 32, 7, 5)
    return overlay(px, p)


# Something for a game to use when it has no texture of its own.
@texture('plain')
def _t():
    return stone_wall(1, '#707070', '#303030', [16, 16, 16, 16], 16, 28)

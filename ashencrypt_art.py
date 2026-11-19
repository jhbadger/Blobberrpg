"""The Ashen Crypt's own pictures and textures, beyond the engine's stock:
the Old Mine, the people of Hollowmere and the dead who linger.
Importing this module registers them with the engine."""

import math
import random

from blobber import textures as tx
from blobber.textures import texture, T, fbm, overlay, glow_at
from blobber.art import picture, eye, skull, person, standing
from blobber.paint import Painter
from blobber.gfx import rgb, mix, scale

GHOST = ('#0a2a30', '#1a5a64', '#3a9098', '#78c8c8', '#c0f4ec', '#ffffff')
ROCK = ('#16120e', '#30281e', '#4e4232', '#6e5e48', '#928066', '#b8a688')


def P(seed=1, w=T, h=T):
    p = Painter(w, h, seed)
    p.material('ghostly', *GHOST, glow=True)
    p.material('rock', *ROCK)
    return p


# ---------------------------------------------------------------- the mine

def _rock(seed=601):
    return tx.stone_wall(seed, '#6a5a46', '#241c14', [12, 14, 10, 16, 12],
                         8, 22, jitter=0.25, noise=0.55, round_=3,
                         hue='#7a6040')


@texture('mine_wall')
def _t():
    return _rock()


def _timbers(px, seed):
    p = P(seed)
    for x in (4, 52):
        p.rect(x, 0, 8, 64, 'wood', lum=0.55, gradx=-0.5, tex=0.15)
    p.rect(0, 2, 64, 8, 'wood', lum=0.6, grad=-0.5, tex=0.15)
    for x in (8, 56):
        p.circle(x, 6, 1.5, 'iron', lum=0.8)
    return overlay(px, p)


@texture('mine_timber')
def _t():
    return _timbers(_rock(602), 31)


@texture('mine_lantern')
def _t():
    px = _timbers(_rock(603), 32)
    glow_at(px, 32, 26, 22, '#ffc060', 0.5)
    p = P(33)
    p.line(32, 10, 32, 18, 'iron', 0.5, 1.5)
    p.rect(26, 18, 12, 16, 'iron', lum=0.4)
    p.rect(28, 20, 8, 12, 'flame', lum=0.85)
    p.poly([(25, 18), (32, 13), (39, 18)], 'iron', lum=0.5)
    p.glow.add('flame')
    return overlay(px, p)


@texture('mine_ore')
def _t():
    px = _rock(604)
    return tx.cracks(px, 34, 5, glow='#ffd040')


@texture('mine_door')
def _t():
    px = _timbers(_rock(605), 35)
    p = P(36)
    p.rect(14, 12, 36, 52, 'wood', lum=0.5, gradx=-0.3, tex=0.1)
    for x in range(14, 50, 6):
        p.rect(x, 12, 1, 52, 'shadow', lum=0.2)
    for y in (20, 50):
        p.rect(14, y, 36, 3, 'iron', lum=0.55)
    p.circle(44, 38, 2.5, 'iron', lum=0.7)
    return overlay(px, p)


@texture('mine_locked')
def _t():
    px = tx.get('mine_door')
    px = list(px)
    p = P(37)
    p.rect(10, 34, 44, 5, 'iron', lum=0.7, grad=0.4)
    p.rect(27, 31, 10, 11, 'iron', lum=0.6)
    p.circle(32, 36, 1.5, 'shadow', lum=0.0)
    return overlay(px, p)


@texture('mine_floor')
def _t():
    rng = random.Random(38)
    n = fbm(rng, ((8, 0.5), (16, 0.3), (32, 0.2)))
    px = [scale('#5a4a38', 0.7 + 0.5 * v) for v in n]
    for _ in range(140):
        x, y = rng.randrange(T), rng.randrange(T)
        px[y * T + x] = scale('#7a6a58', 0.8 + 0.4 * rng.random())
    # rails
    for x0 in (18, 44):
        for y in range(T):
            for x in (x0, x0 + 1):
                px[y * T + x] = rgb('#8a8a90') if x == x0 else rgb('#4a4a50')
    for y in range(4, T, 12):
        for x in range(14, 50):
            px[y * T + x] = scale('#4a3420', 0.9)
            px[(y + 1) * T + x] = scale('#4a3420', 0.7)
    return px


@texture('mine_ceil')
def _t():
    return [scale(c, 0.7) for c in _rock(606)]


@texture('mine_gate')
def _t():
    px = tx.stone_wall(607, '#8a8680', '#3a3834', [20, 22, 22], 18, 30,
                       hue='#8a8070')
    p = P(39)
    p.rect(14, 18, 36, 46, 'shadow', lum=0.04)
    p.rect(10, 14, 6, 50, 'wood', lum=0.55, gradx=-0.4)
    p.rect(48, 14, 6, 50, 'wood', lum=0.45, gradx=-0.4)
    p.rect(8, 10, 48, 7, 'wood', lum=0.6, grad=-0.4)
    p.line(20, 64, 26, 30, 'iron', 0.6, 2)
    p.line(44, 64, 38, 30, 'iron', 0.6, 2)
    p.rect(22, 2, 20, 8, 'wood', lum=0.5)
    p.line(25, 6, 39, 6, 'black', 0.2, 1)
    return overlay(px, p)


# --------------------------------------------------------------- people

@picture('townsman', 48, 124, height=0.62)
def _p(p):
    standing(p, 24, 'cloth', hair='greyhair', beard='greyhair', staff=True)


@picture('gravedigger', 48, 124, height=0.6)
def _p(p):
    standing(p, 22, 'leather', hair='redhair', apron='cloth')
    p.line(40, 30, 38, 122, 'wood', 0.55, 2.5)
    p.poly([(33, 104), (43, 104), (42, 122), (34, 122)], 'iron', lum=0.6)


@picture('ghost_warden', 56, 124, height=0.62)
def _p(p):
    p.material('ghostly', *GHOST, glow=True)
    standing(p, 28, 'ghostly', skin='ghostly', hair='ghostly',
             beard='ghostly', staff=True)
    p.speckle('ghostly', 0.2, 0.25)


@picture('ghost_dwarf', 56, 110, height=0.5)
def _p(p):
    p.material('ghostly', *GHOST, glow=True)
    p.poly([(16, 34), (40, 34), (46, 104), (10, 104)], 'ghostly', lum=0.5,
           gradx=-0.3)
    for s in (-1, 1):
        p.limb(28 + s * 14, 40, 28 + s * 18, 70, 5, 4.5, 'ghostly')
    p.ellipse(28, 24, 11, 12, 'ghostly', bias=0.1)
    p.poly([(18, 28), (38, 28), (34, 60), (22, 60)], 'ghostly', lum=0.85)
    p.ellipse(28, 13, 12, 5, 'ghostly', lum=0.7)
    p.speckle('ghostly', 0.2, 0.25)


@picture('prisoner', 56, 110, height=0.55)
def _p(p):
    p.rect(2, 0, 52, 110, 'shadow', lum=0.0)
    for x in range(4, 54, 8):
        p.rect(x, 0, 3, 110, 'iron', lum=0.55, gradx=-0.6)
    p.rect(2, 20, 52, 3, 'iron', lum=0.6)
    p.ellipse(28, 50, 9, 10, 'skin', bias=-0.2)
    p.ellipse(28, 43, 9, 5, 'black', lum=0.3)
    p.circle(25, 50, 1, 'eyegold', lum=0.9)
    p.circle(31, 50, 1, 'eyegold', lum=0.9)
    for x in range(4, 54, 8):
        p.rect(x, 0, 3, 110, 'iron', lum=0.55, gradx=-0.6)


# Portraits for talking to them.

@picture('tam_face')
def _p(p):
    person(p, robe='cloth', trim=None, hair='greyhair', beard='greyhair',
           eyes='blue')


@picture('wenna_face')
def _p(p):
    person(p, robe='leather', trim=None, apron='cloth', hair='redhair',
           eyes='leaf')


@picture('hobb_face')
def _p(p):
    p.material('ghostly', *GHOST, glow=True)
    person(p, skin='ghostly', robe='ghostly', trim=None, hair='ghostly',
           beard='ghostly', eyes='eyecyan')
    p.speckle('ghostly', 0.15, 0.25)


@picture('brokk_face')
def _p(p):
    p.material('ghostly', *GHOST, glow=True)
    person(p, skin='ghostly', robe='ghostly', trim=None, hair='ghostly',
           beard='ghostly', eyes='eyecyan', bald=True)
    p.rect(52, 104, 56, 8, 'ghostly', lum=0.85)
    p.speckle('ghostly', 0.15, 0.25)


@picture('nim_face')
def _p(p):
    p.rect(0, 0, 160, 160, 'shadow', lum=0.02)
    person(p, robe='black', trim=None, hair='hair', eyes='leaf',
           mustache=True)
    for x in range(8, 160, 22):
        p.rect(x, 0, 6, 160, 'iron', lum=0.55, gradx=-0.6)
    p.rect(0, 30, 160, 6, 'iron', lum=0.6)


# -------------------------------------------------------------- monsters

@picture('koboldking', 170, 170)
def _p(p):
    p.line(140, 20, 132, 166, 'wood', 0.55, 5)
    p.poly([(140, 8), (156, 22), (146, 30), (134, 22)], 'gold', lum=0.7)
    p.chain([(90, 128), (120, 146), (140, 136), (150, 120)], 9, 3, 'rust')
    for s in (-1, 1):
        p.limb(85 + s * 14, 120, 85 + s * 20, 146, 12, 9, 'rust', tex=0.15)
        p.limb(85 + s * 20, 146, 85 + s * 18, 164, 9, 6, 'rust')
        p.ellipse(85 + s * 20, 166, 12, 4, 'rust')
    p.poly([(52, 70), (118, 70), (128, 150), (42, 150)], 'crimson', lum=0.5,
           gradx=-0.3, tex=0.06)
    p.ellipse(85, 98, 26, 32, 'rust', tex=0.2)
    p.ellipse(85, 104, 16, 22, 'bone', bias=-0.15)
    for k in range(4):
        p.circle(66 + k * 12, 84, 3, 'gold', lum=0.8)
    p.chain([(62, 84), (50, 108), (62, 124)], 8, 6, 'rust')
    p.chain([(108, 84), (124, 70), (134, 52)], 8, 6, 'rust')
    p.circle(134, 50, 7, 'rust')
    p.ellipse(85, 56, 24, 21, 'rust', tex=0.2)
    p.ellipse(64, 66, 16, 10, 'rust', angle=0.25, tex=0.2)
    p.limb(73, 40, 58, 18, 5, 1.5, 'bone')
    p.limb(97, 40, 112, 18, 5, 1.5, 'bone')
    p.poly([(68, 40), (72, 26), (78, 34), (85, 22), (92, 34), (98, 26),
            (102, 40)], 'gold', lum=0.7, grad=-0.3)
    for x in (76, 85, 94):
        p.circle(x, 37, 2, 'red', lum=0.8)
    eye(p, 75, 54, 4, 'eyegold')
    eye(p, 95, 54, 4, 'eyegold')
    p.line(52, 70, 72, 72, 'mouth', 0.2, 2)
    p.poly([(56, 70), (60, 70), (58, 77)], 'teeth', lum=0.9)

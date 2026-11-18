"""The first-person view.

The party always stands in the middle of a square and faces one of four
ways, so every place a wall, floor or ceiling can appear on the screen is
known in advance: a "slot".  For each slot the renderer works out once
which texture pixel lands on each screen pixel and how far away it is;
after that, drawing a wall of a given texture at a given light is a cached
list of byte rows copied into the framebuffer.  Distance darkens towards a
fog colour with ordered dithering.
"""

import math
import operator
import random

from .gfx import rgb, mix, BAYER4, Image
from . import textures

NL = 8                  # shade levels between fog and full light


class Look:
    """What the view needs to know about one square."""
    __slots__ = ('solid', 'wall', 'floor', 'ceil', 'sprite')

    def __init__(self, solid=False, wall=None, floor=None, ceil=None,
                 sprite=None):
        self.solid, self.wall, self.floor = solid, wall, floor
        self.ceil, self.sprite = ceil, sprite


SOLID_DARK = Look(True, None)


def shade(z, R):
    """Brightness at distance z with light radius R."""
    b = 1.05 - (z - 0.3) / R
    return 0.0 if b < 0 else 1.0 if b > 1 else b


class View:
    def __init__(self, w=320, h=224, hh=0.42, maxd=6):
        self.w, self.h = w, h
        self.cx, self.cy = w / 2, h / 2
        self.f = w / 2
        self.hh = hh
        self.maxd = maxd
        self.T = textures.T
        self._geo = {}
        self._idx = {}
        self._out = {}
        self._levels = {}
        self._spr = {}
        self.sprite_source = None     # name -> (Image, world height)
        self._build_floor()

    # ------------------------------------------------------------ geometry

    def _build_floor(self):
        W, H, f, hh, cx, cy, T = (self.w, self.h, self.f, self.hh, self.cx,
                                  self.cy, self.T)
        groups = {}
        for py in range(H):
            dy = py + 0.5 - cy
            if dy <= 0:
                continue
            z = f * hh / dy
            k = int(math.floor(z + 0.5))
            if k > self.maxd:
                continue
            v = min(T - 1, max(0, int(((k + 0.5) - z) * T)))
            cur = None
            for px in range(W):
                X = (px + 0.5 - cx) * z / f
                xi = int(math.floor(X + 0.5))
                u = min(T - 1, max(0, int((X - xi + 0.5) * T)))
                if cur is None or cur[0] != xi:
                    cur = [xi, px, []]
                    groups.setdefault(('f', k, xi), []).append(
                        (py, px, cur[2], z))
                cur[2].append(v * T + u)
        for key, rows in groups.items():
            self._geo[key] = rows
            self._geo[('c',) + key[1:]] = [(H - 1 - py, px, tx, z)
                                           for (py, px, tx, z) in rows]
        self.floor_keys = sorted({(k[1], k[2]) for k in groups})

    def _front(self, k, x):
        f, hh, cx, cy, T = self.f, self.hh, self.cx, self.cy, self.T
        z = k - 0.5
        sx0, sx1 = cx + f * (x - 0.5) / z, cx + f * (x + 0.5) / z
        sy0, sy1 = cy - f * hh / z, cy + f * hh / z
        px0 = max(0, int(math.ceil(sx0 - 0.5)))
        px1 = min(self.w, int(math.ceil(sx1 - 0.5)))
        py0 = max(0, int(math.ceil(sy0 - 0.5)))
        py1 = min(self.h, int(math.ceil(sy1 - 0.5)))
        if px0 >= px1 or py0 >= py1:
            return []
        us = [min(T - 1, max(0, int((px + 0.5 - sx0) / (sx1 - sx0) * T)))
              for px in range(px0, px1)]
        rows = []
        for py in range(py0, py1):
            v = min(T - 1, max(0, int((py + 0.5 - sy0) / (sy1 - sy0) * T)))
            rows.append((py, px0, [v * T + u for u in us], z))
        return rows

    def _side(self, k, x):
        f, hh, cx, cy, T = self.f, self.hh, self.cx, self.cy, self.T
        X = x + 0.5 if x < 0 else x - 0.5
        z0, z1 = max(k - 0.5, 0.05), k + 0.5
        a, b = cx + f * X / z0, cx + f * X / z1
        lo, hi = min(a, b), max(a, b)
        px0 = max(0, int(math.ceil(lo - 0.5)))
        px1 = min(self.w, int(math.ceil(hi - 0.5)))
        byrow = {}
        for px in range(px0, px1):
            d = px + 0.5 - cx
            if d == 0 or (d < 0) != (X < 0):
                continue
            z = f * X / d
            if not z0 <= z < z1:
                continue
            u = z - (k - 0.5)
            if X > 0:
                u = 1 - u
            ui = min(T - 1, max(0, int(u * T)))
            top, bot = cy - f * hh / z, cy + f * hh / z
            ya = max(0, int(math.ceil(top - 0.5)))
            yb = min(self.h, int(math.ceil(bot - 0.5)))
            for py in range(ya, yb):
                v = min(T - 1, max(0, int((py + 0.5 - top) / (bot - top) * T)))
                byrow.setdefault(py, []).append((px, v * T + ui, z))
        rows = []
        for py in sorted(byrow):
            cols = sorted(byrow[py])
            # split into contiguous runs (they are, but be safe)
            run = [cols[0]]
            for c in cols[1:]:
                if c[0] == run[-1][0] + 1:
                    run.append(c)
                else:
                    rows.append((py, run[0][0], [r[1] for r in run],
                                 [r[2] for r in run]))
                    run = [c]
            rows.append((py, run[0][0], [r[1] for r in run],
                         [r[2] for r in run]))
        return rows

    def _geom(self, key):
        g = self._geo.get(key)
        if g is None:
            kind, k, x = key
            g = self._front(k, x) if kind == 'w' else self._side(k, x)
            self._geo[key] = g
        return g

    # ------------------------------------------------------------- shading

    def _index(self, key, R):
        ik = (key, R)
        out = self._idx.get(ik)
        if out is not None:
            return out
        TT = self.T * self.T
        out = []
        for (py, px0, texels, zs) in self._geom(key):
            brow = BAYER4[py & 3]
            idx = []
            ext = idx.extend
            if isinstance(zs, float):
                bn = shade(zs, R) * NL
                for j, t in enumerate(texels):
                    l = int(bn + (brow[(px0 + j) & 3] + 0.5) / 16)
                    if l > NL:
                        l = NL
                    base = (l * TT + t) * 3
                    ext((base, base + 1, base + 2))
            else:
                for j, t in enumerate(texels):
                    l = int(shade(zs[j], R) * NL + (brow[(px0 + j) & 3] + 0.5) / 16)
                    if l > NL:
                        l = NL
                    base = (l * TT + t) * 3
                    ext((base, base + 1, base + 2))
            out.append((py, px0, operator.itemgetter(*idx)))
        self._idx[ik] = out
        return out

    def levels(self, tex, fog):
        key = (tex, fog)
        lv = self._levels.get(key)
        if lv is None:
            px = textures.get(tex)
            parts = []
            for l in range(NL + 1):
                t = l / NL
                parts.append(b''.join(bytes(mix(fog, c, t)) for c in px))
            lv = self._levels[key] = b''.join(parts)
        return lv

    def _rows(self, key, tex, R, fog):
        ok = (key, tex, R, fog)
        rows = self._out.get(ok)
        if rows is None:
            if len(self._out) > 1500:
                self._out.clear()
            lv = self.levels(tex, fog)
            rows = [(py, px0, bytes(g(lv)))
                    for (py, px0, g) in self._index(key, R)]
            self._out[ok] = rows
        return rows

    # ------------------------------------------------------------- sprites

    def _sprite(self, name, k, R, fog):
        key = (name, k, R, fog)
        img = self._spr.get(key)
        if img is None:
            if len(self._spr) > 400:
                self._spr.clear()
            src, wh = self.sprite_source(name)
            z = float(k)
            hpx = self.f * wh / z
            wpx = src.w * hpx / src.h
            img = src.scaled(wpx, hpx).shaded(shade(z, R), fog)
            self._spr[key] = img
        return img

    # ------------------------------------------------------------ drawing

    def depth_for(self, R):
        return max(1, min(self.maxd, int(math.ceil(R + 0.3))))

    def render(self, surf, ox, oy, look, R, fog=(0, 0, 0), sky=None,
               ground=None):
        """Draw the view with its top-left at ox, oy.

        look(k, x) describes the square k ahead and x to the right (None for
        nothing there).  R is the light radius in squares, fog the colour
        things fade into, sky the rgb bytes of the upper half (or None for
        ceilings) and ground the colour under everything else."""
        W, H = self.w, self.h
        fog = rgb(fog)
        D = self.depth_for(R)
        old = surf.clip
        surf.set_clip(ox, oy, W, H)
        half = H // 2
        if sky:
            surf.put(ox, oy, W, half, sky)
        else:
            surf.rect(ox, oy, W, half, fog)
        surf.rect(ox, oy + half, W, H - half, rgb(ground) if ground else fog)
        cache = {}

        def get(k, x):
            c = cache.get((k, x))
            if c is None:
                c = cache[(k, x)] = look(k, x) or SOLID_DARK
            return c

        for (k, x) in self.floor_keys:
            if k > D:
                continue
            c = get(k, x)
            if c.solid:
                continue
            if c.floor:
                surf.blit_rows(ox, oy, self._rows(('f', k, x), c.floor, R, fog))
            if c.ceil and not sky:
                surf.blit_rows(ox, oy, self._rows(('c', k, x), c.ceil, R, fog))
        for k in range(D, -1, -1):
            L = k + 1
            xs = sorted(range(-L, L + 1), key=lambda v: -abs(v))
            for x in xs:
                c = get(k, x)
                if not c.solid or not c.wall:
                    continue
                if k >= 1:
                    surf.blit_rows(ox, oy, self._rows(('w', k, x), c.wall, R, fog))
                if x != 0:
                    surf.blit_rows(ox, oy, self._rows(('s', k, x), c.wall, R, fog))
            if k >= 1 and self.sprite_source:
                for x in xs:
                    c = get(k, x)
                    if c.solid or not c.sprite:
                        continue
                    img = self._sprite(c.sprite, k, R, fog)
                    z = float(k)
                    by = self.cy + self.f * self.hh / z
                    sx = self.cx + self.f * x / z - img.w / 2
                    surf.blit(img, ox + int(sx), oy + int(by - img.h))
        surf.clip = old


def make_sky(w, h, top='#2c4c8c', horizon='#c4d4e0', seed=7, clouds=True):
    """The rgb bytes of a dithered sky with a few clouds."""
    rng = random.Random(seed)
    top, horizon = rgb(top), rgb(horizon)
    period = 8
    g = [rng.random() for _ in range(period * period)]

    def noise(x, y):
        fx, fy = x * period / w, y * period / (h * 2)
        x0, y0 = int(fx) % period, int(fy) % period
        tx, ty = fx - int(fx), fy - int(fy)
        x1, y1 = (x0 + 1) % period, (y0 + 1) % period
        a = g[y0 * period + x0] * (1 - tx) + g[y0 * period + x1] * tx
        b = g[y1 * period + x0] * (1 - tx) + g[y1 * period + x1] * tx
        return a * (1 - ty) + b * ty

    out = bytearray()
    steps = 16
    for y in range(h):
        t = (y / (h - 1)) ** 1.4
        for x in range(w):
            q = t * steps
            k = int(q)
            if q - k > (BAYER4[y & 3][x & 3] + 0.5) / 16:
                k += 1
            c = mix(top, horizon, min(1.0, k / steps))
            if clouds:
                n = noise(x, y) * 0.7 + noise(x * 3 % w, y * 2) * 0.3
                v = (n - 0.55) * 3.2 * (0.3 + t)
                if v > (BAYER4[y & 3][x & 3] + 0.5) / 16 * 0.6:
                    c = mix(c, (250, 250, 255), min(0.85, v))
            out += bytes(c)
    return bytes(out)

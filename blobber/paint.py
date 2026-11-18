"""A little painter for monsters, people and things.

Pictures are built from shaded shapes (spheres, limbs, flat polygons) on a
grid that remembers, for every pixel, a material and a brightness.  At the
end each material's brightness is mapped onto a short ramp of colours with
ordered dithering and the silhouette gets a dark outline, which gives the
look of hand-shaded 16-colour-era pixel art at whatever size you paint.
"""

import math
import random

from .gfx import Image, bayer, rgb, ramp as make_ramp

LIGHT = (-0.48, -0.62, 0.62)
_l = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _l for v in LIGHT)

# Ramps shared by every picture (dark to light).  A painting can add its
# own with Painter.material().
RAMPS = {
    'bone':    ('#2a2018', '#5a4a38', '#8f7f66', '#c2b496', '#e8dfc6', '#fffbea'),
    'skin':    ('#3a1c14', '#7a3e2c', '#b06a4c', '#d89a74', '#f4c8a0'),
    'paleskin': ('#2c2830', '#5e5660', '#8e8690', '#bcb4b8', '#e6e0dc'),
    'darkskin': ('#20120c', '#4a2a1a', '#74462c', '#9c6a46', '#c49068'),
    'green':   ('#0e1a0c', '#24401c', '#3e6a2c', '#62983e', '#94c45a', '#cceb8c'),
    'rotgreen': ('#141a10', '#2e3a22', '#4c5a36', '#6e7c50', '#98a274'),
    'slime':   ('#06200e', '#0e4a1c', '#1c7a2c', '#38b040', '#7ade5c', '#d2ffa8'),
    'fur':     ('#1a120c', '#3c2a1c', '#634630', '#8a6848', '#b48e66'),
    'greyfur': ('#141418', '#34343c', '#58585e', '#808084', '#acacae'),
    'black':   ('#060608', '#141418', '#24242c', '#3a3a46', '#56566a'),
    'steel':   ('#101418', '#2c3440', '#4e5a68', '#7e8c9c', '#b4c2d0', '#eef6ff'),
    'darksteel': ('#08080c', '#18181f', '#2c2c38', '#484858', '#70708a', '#a0a0c0'),
    'iron':    ('#100c0a', '#2a221e', '#463a32', '#665648', '#8c7a68'),
    'rust':    ('#1c0c06', '#4a2210', '#78401e', '#a4602e', '#c88a52'),
    'gold':    ('#2a1804', '#6a4408', '#a8780e', '#dcb020', '#fae070', '#fffbd0'),
    'wood':    ('#1a0e06', '#3e2412', '#62401e', '#8a5e30', '#b08048'),
    'stone':   ('#18181c', '#38383e', '#5a5a60', '#7e7e82', '#a6a6a6', '#d0d0cc'),
    'red':     ('#1e0406', '#4c0a0e', '#801418', '#b82424', '#e45038', '#ffa078'),
    'crimson': ('#160208', '#3a0614', '#600c22', '#8c1830', '#b83048'),
    'blue':    ('#060a1e', '#0e1e4a', '#1c367a', '#3058b0', '#5a8ae0', '#a8ccff'),
    'purple':  ('#100618', '#2a0e3c', '#481a62', '#6a2c8c', '#9450b8', '#c890e4'),
    'cloth':   ('#16100c', '#32261c', '#52402e', '#766048', '#9c8466'),
    'white':   ('#3a3a44', '#7a7a86', '#b4b4be', '#dcdce4', '#ffffff'),
    'ash':     ('#141214', '#2e2a2c', '#4c4648', '#6e6668', '#948a8a', '#bcb2ae'),
    'ember':   ('#3a0a00', '#8a2200', '#d45a00', '#ff9a10', '#ffd860', '#fffde0'),
    'ghost':   ('#061418', '#0e3038', '#1c5a64', '#3a8c94', '#7cc4c4', '#d4fff8'),
    'eyered':  ('#5a0000', '#c00000', '#ff3020', '#ff9a70', '#ffffff'),
    'eyegold': ('#5a3a00', '#c08800', '#ffd020', '#fff090', '#ffffff'),
    'eyecyan': ('#004a5a', '#00a0c0', '#40f0ff', '#c0ffff', '#ffffff'),
    'eyegreen': ('#003a10', '#00a030', '#40ff60', '#c0ffc8', '#ffffff'),
    'water':   ('#04142a', '#0a2c54', '#14508a', '#2c7cbc', '#64b0e4', '#c8ecff'),
    'leaf':    ('#06140a', '#0e2a12', '#1c4a1c', '#2e6e28', '#4c9636', '#86c454'),
    'pink':    ('#3a1018', '#7a2c38', '#b45664', '#e08c94', '#ffc4c4'),
    'flame':   ('#5a0a00', '#c42800', '#ff6a00', '#ffb020', '#fff070', '#ffffff'),
    'shadow':  ('#000000', '#08060a', '#121018', '#1c1a24'),
    'teeth':   ('#5a5040', '#a89c80', '#e6dcc0', '#ffffff'),
    'mouth':   ('#100204', '#3a0810', '#6a1420'),
    'hair':    ('#0c0806', '#2a1a10', '#4a301c', '#6e4a2a', '#94683c'),
    'greyhair': ('#2a2a2e', '#5e5e64', '#8e8e94', '#c0c0c4', '#eeeeee'),
    'blond':   ('#2a1a06', '#6a4a14', '#a8822c', '#d8b450', '#f8e08c'),
    'redhair': ('#200804', '#5a1a08', '#963414', '#c85a24', '#ec8c48'),
    'leather': ('#140c06', '#341e10', '#583620', '#7e5432', '#a47a50'),
    'glass':   ('#0a1420', '#1c3448', '#38607e', '#6a98b4', '#b4dcf0', '#ffffff'),
    'violetglow': ('#2a0a40', '#6a20a0', '#a050e0', '#d8a0ff', '#ffffff'),
}


class Painter:
    def __init__(self, w, h, seed=0):
        self.w, self.h = w, h
        self.mat = [None] * (w * h)
        self.lum = [0.0] * (w * h)
        self.rng = random.Random(seed)
        self.ramps = dict(RAMPS)
        self.glow = set()

    def material(self, name, *colours, glow=False):
        self.ramps[name] = colours
        if glow:
            self.glow.add(name)

    def _box(self, x0, y0, x1, y1):
        return (max(0, int(math.floor(x0))), max(0, int(math.floor(y0))),
                min(self.w, int(math.ceil(x1)) + 1),
                min(self.h, int(math.ceil(y1)) + 1))

    def _put(self, x, y, m, L, tex):
        i = y * self.w + x
        if tex:
            L += (self.rng.random() - 0.5) * tex
        self.mat[i] = m
        self.lum[i] = L

    # Shapes.

    def ellipse(self, cx, cy, rx, ry, m, lum=None, bias=0.0, tex=0.0,
                angle=0.0, light=LIGHT, power=1.0):
        """A shaded ellipsoid (lum=None) or a flat one at brightness lum."""
        r = max(rx, ry)
        x0, y0, x1, y1 = self._box(cx - r, cy - r, cx + r, cy + r)
        ca, sa = math.cos(angle), math.sin(angle)
        for y in range(y0, y1):
            dy = y + 0.5 - cy
            for x in range(x0, x1):
                dx = x + 0.5 - cx
                u = (dx * ca + dy * sa) / rx
                v = (-dx * sa + dy * ca) / ry
                d2 = u * u + v * v
                if d2 > 1.0:
                    continue
                if m is None:
                    self.mat[y * self.w + x] = None
                    continue
                if lum is None:
                    nz = math.sqrt(1.0 - d2)
                    # back to screen space for the normal
                    nx = u * ca - v * sa
                    ny = u * sa + v * ca
                    L = nx * light[0] + ny * light[1] + nz * light[2]
                    L = max(0.0, L) ** power * 0.8 + 0.18 + bias
                else:
                    L = lum
                self._put(x, y, m, L, tex)

    def circle(self, cx, cy, r, m, lum=None, **kw):
        self.ellipse(cx, cy, r, r, m, lum, **kw)

    def limb(self, x0, y0, x1, y1, r0, r1, m, lum=None, bias=0.0, tex=0.0):
        """A shaded tapered cylinder with rounded ends (a capsule)."""
        rr = max(r0, r1)
        bx0, by0, bx1, by1 = self._box(min(x0, x1) - rr, min(y0, y1) - rr,
                                       max(x0, x1) + rr, max(y0, y1) + rr)
        vx, vy = x1 - x0, y1 - y0
        ll = vx * vx + vy * vy or 1e-9
        for y in range(by0, by1):
            py = y + 0.5
            for x in range(bx0, bx1):
                px = x + 0.5
                t = ((px - x0) * vx + (py - y0) * vy) / ll
                t = 0.0 if t < 0 else 1.0 if t > 1 else t
                qx, qy = x0 + vx * t, y0 + vy * t
                r = r0 + (r1 - r0) * t
                ddx, ddy = px - qx, py - qy
                d2 = ddx * ddx + ddy * ddy
                if d2 > r * r:
                    continue
                if m is None:
                    self.mat[y * self.w + x] = None
                    continue
                if lum is None:
                    nx, ny = ddx / r, ddy / r
                    nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
                    L = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
                    L = max(0.0, L) * 0.8 + 0.18 + bias
                else:
                    L = lum
                self._put(x, y, m, L, tex)

    def chain(self, pts, r0, r1, m, **kw):
        """Limbs along a path of points, tapering from r0 to r1."""
        n = len(pts) - 1
        for i in range(n):
            ra = r0 + (r1 - r0) * i / n
            rb = r0 + (r1 - r0) * (i + 1) / n
            self.limb(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                      ra, rb, m, **kw)

    def poly(self, pts, m, lum=0.6, grad=0.0, tex=0.0, gradx=0.0):
        """A filled polygon; grad brightens/darkens it from top to bottom
        (gradx from left to right)."""
        ys = [p[1] for p in pts]
        xs = [p[0] for p in pts]
        ymin, ymax = min(ys), max(ys)
        xmin, xmax = min(xs), max(xs)
        hh = max(1e-6, ymax - ymin)
        ww = max(1e-6, xmax - xmin)
        n = len(pts)
        for y in range(max(0, int(ymin)), min(self.h, int(math.ceil(ymax)) + 1)):
            py = y + 0.5
            cross = []
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                if (ay <= py < by) or (by <= py < ay):
                    cross.append(ax + (py - ay) * (bx - ax) / (by - ay))
            cross.sort()
            for k in range(0, len(cross) - 1, 2):
                xa = max(0, int(math.ceil(cross[k] - 0.5)))
                xb = min(self.w, int(math.ceil(cross[k + 1] - 0.5)))
                for x in range(xa, xb):
                    if m is None:
                        self.mat[y * self.w + x] = None
                        continue
                    L = lum + grad * ((py - ymin) / hh - 0.5) \
                        + gradx * ((x + 0.5 - xmin) / ww - 0.5)
                    self._put(x, y, m, L, tex)

    def rect(self, x, y, w, h, m, lum=0.6, grad=0.0, tex=0.0, gradx=0.0):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], m, lum,
                  grad, tex, gradx)

    def line(self, x0, y0, x1, y1, m, lum=0.5, w=1.0):
        self.limb(x0, y0, x1, y1, w / 2, w / 2, m, lum=lum)

    def shade_where(self, test, delta, mats=None):
        """Add delta to the brightness of painted pixels where test(x, y)."""
        for y in range(self.h):
            for x in range(self.w):
                i = y * self.w + x
                if self.mat[i] is not None and (mats is None or
                                                self.mat[i] in mats):
                    if test(x, y):
                        self.lum[i] += delta

    def speckle(self, m, p, delta):
        """Randomly brighten/darken a fraction p of pixels of material m."""
        for i, mm in enumerate(self.mat):
            if mm == m and self.rng.random() < p:
                self.lum[i] += delta * (1 if self.rng.random() < 0.5 else -1)

    # Finishing.

    def image(self, outline='#0a080c', inner_lines=True):
        """The finished picture.  inner_lines darkens a pixel where it
        borders a different material that is drawn brighter, which keeps
        overlapping parts readable."""
        w, h = self.w, self.h
        mat, lum = self.mat, self.lum
        px = [None] * (w * h)
        oc = rgb(outline) if outline else None
        ramps = {k: [rgb(c) for c in v] for k, v in self.ramps.items()}
        for y in range(h):
            for x in range(w):
                i = y * w + x
                m = mat[i]
                if m is None:
                    if oc is not None:
                        if ((x > 0 and mat[i - 1] is not None) or
                                (x < w - 1 and mat[i + 1] is not None) or
                                (y > 0 and mat[i - w] is not None) or
                                (y < h - 1 and mat[i + w] is not None)):
                            px[i] = oc
                    continue
                r = ramps[m]
                L = lum[i]
                if inner_lines and m not in self.glow:
                    if (y > 0 and mat[i - w] is not None and mat[i - w] != m
                            and lum[i - w] > L + 0.05) or \
                       (x > 0 and mat[i - 1] is not None and mat[i - 1] != m
                            and lum[i - 1] > L + 0.05):
                        L -= 0.22
                L = 0.0 if L < 0 else 0.999 if L >= 1 else L
                q = L * (len(r) - 1)
                k = int(q)
                if q - k > bayer(x, y) and k < len(r) - 1:
                    k += 1
                px[i] = r[k]
        return Image.from_pixels(w, h, px)


def ramp(*stops, n=6):
    return make_ramp(*stops, n=n)

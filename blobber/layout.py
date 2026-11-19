"""The upright (portrait) screen, for a phone held upright.

The game always draws its usual 640x400 screen.  For an upright window
the shell asks for this layout instead: the view with its frame on top,
the scroll under it, and a narrower roster at the bottom (name, hits,
power and condition; the rest is on the character sheet), 360x676 in
all.  Taps on it are mapped back to where they would have landed on the
wide screen, so the game itself never knows the difference.  Screens
that need the whole width (the character sheet) stay wide.
"""

from .gfx import Surface, rgb
from . import art
from . import font
from .words import w

W, H = 360, 676
FRAME = (8, 0, 344, 274)        # the view, its frame and the nameplate
PAPER_SRC = (364, 8, 268, 266)  # the scroll on the wide screen
PAPER_AT = (46, 282)
ROSTER = (8, 556, 344, 112)

_backgrounds = {}


def background(g):
    """Bytes of the upright screen's background, made once per look."""
    ch = g.chrome
    key = (ch['background'], ch['bg_colours'], ch['bg_shade'])
    bg = _backgrounds.get(key)
    if bg is None:
        s = Surface(W, H)
        if ch['background']:
            s.put(0, 0, W, H, art.texture_panel(W, H, ch['background'],
                                                ch['bg_shade']))
        else:
            s.put(0, 0, W, H, art.stone_panel(W, H, 3, *ch['bg_colours']))
            s.darken(0, 0, W, H, ch['bg_shade'])
        bg = _backgrounds[key] = bytes(s.buf)
    return bg


def compose(g, wide):
    """The upright screen, from the wide one."""
    s = Surface(W, H)
    s.put(0, 0, W, H, background(g))
    x, y, fw, fh = FRAME
    s.put(x, y, fw, fh, wide.get(x, y, fw, fh))
    px, py, pw, ph = PAPER_SRC
    s.put(PAPER_AT[0], PAPER_AT[1], pw, ph, wide.get(px, py, pw, ph))
    draw_roster(g, s, getattr(g.mode, 'roster_sel', None))
    return s


def to_wide(x, y):
    """Where a tap on the upright screen lands on the wide one (or None)."""
    fx, fy, fw, fh = FRAME
    if fx <= x < fx + fw and fy <= y < fy + fh:
        return x, y
    ax, ay = PAPER_AT
    px, py, pw, ph = PAPER_SRC
    if ax <= x < ax + pw and ay <= y < ay + ph:
        return x - ax + px, y - ay + py
    rx, ry, rw, rh = ROSTER
    if rx <= x < rx + rw and ry + 19 <= y < ry + rh:
        from .game import RX, RY
        i = (y - ry - 19) // 15
        return RX + 40, RY + 21 + 15 * i + 4
    return None


def draw_roster(g, s, sel):
    from .game import ROSTER_BG, ROSTER_TXT, ROSTER_HEAD
    rx, ry, rw, rh = ROSTER
    s.rect(rx, ry, rw, rh, ROSTER_BG)
    s.bevel(rx, ry, rw, rh, rgb('#4a4658'), rgb('#08070a'), 2)
    s.rect(rx + 6, ry + 17, rw - 12, 1, rgb('#4a4030'))
    cols = [(rx + 6, '#'), (rx + 18, 'Name'), (rx + 124, 'Hits'),
            (rx + 210, w('pts')), (rx + 276, 'Status')]
    for x, t in cols:
        s.text(x, ry + 5, t, ROSTER_HEAD)
    if not g.st:
        return
    over = g.roster_override or {}
    y = ry + 21
    for i, c in enumerate(g.party):
        hp, status, sp = over.get(i, (c.hp, c.status, c.sp))
        if sel == i:
            s.rect(rx + 3, y - 2, rw - 6, 14, rgb('#3c3456'))
            s.frame(rx + 3, y - 2, rw - 6, 14, rgb('#8a7ab0'))
        if g.flash_rows.get(i, 0) > 0:
            s.rect(rx + 3, y - 2, rw - 6, 14, rgb('#801010'))
        col = ROSTER_TXT
        if status in ('dead', 'stoned'):
            col = rgb('#7a7480')
        elif status == 'poisoned':
            col = rgb('#9ae070')
        elif status in ('paralyzed', 'asleep'):
            col = rgb('#80b0ff')
        elif hp <= c.maxhp // 4:
            col = rgb('#ff8060')
        s.text(rx + 6, y, str(i + 1), ROSTER_HEAD)
        name = c.name
        while font.width(name) > 100 and len(name) > 3:
            name = name[:-1]
        s.text(rx + 18, y, name, col)
        s.text(rx + 166, y, '%d/%d' % (hp, c.maxhp), col, align='right')
        frac = 0 if c.maxhp <= 0 else max(0, min(1, hp / c.maxhp))
        s.rect(rx + 170, y + 3, 30, 4, rgb('#3a1010'))
        s.rect(rx + 170, y + 3, int(30 * frac), 4,
               rgb('#40c040') if frac > 0.5 else rgb('#e0b020')
               if frac > 0.25 else rgb('#e03020'))
        if c.maxsp:
            s.text(rx + 236, y, '%d/%d' % (sp, c.maxsp), col, align='right')
            frac = max(0, min(1, sp / c.maxsp))
            s.rect(rx + 240, y + 3, 28, 4, rgb('#101a3a'))
            s.rect(rx + 240, y + 3, int(28 * frac), 4, rgb('#5080ff'))
        st = w(status)
        if status == 'ok' and c.can_level():
            st = w('trainable')
        s.text(rx + 276, y, st, col)
        y += 15

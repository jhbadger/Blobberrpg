"""The game: the screen layout, the party's state, walking about, what
happens in each square, spells and items, saving, and the stack of modes
(exploring, menus, combat, the map, character sheets) that take turns
handling keys and drawing.

The front end (tkshell.py) only calls Game.key(), Game.click(),
Game.update() and Game.render(), and shows the bytes render() returns.
"""

import json
import math
import os
import random

from .gfx import Surface, rgb, mix, scale
from . import font
from .view import View, Look, make_sky
from .world import Level, DIRS, DIR_NAMES, DIR_LETTERS
from . import rules
from .rules import Character, ITEMS, SPELLS, roll, bonus
from . import art
from . import textures
from . import home_dir
from . import words
from . import music
from .words import w

W, H = 640, 400
VX, VY, VW, VH = 20, 20, 320, 224          # the 3D view
NX, NY, NW, NH = 20, 249, 320, 15           # the nameplate under it
PX, PY, PW, PH = 364, 8, 268, 266           # the parchment
TX, TY, TW, TH = 378, 28, 240, 228          # text area on the parchment
RX, RY, RW, RH = 8, 282, 624, 112           # the roster

INK = rgb('#3a2210')
INK_DIM = rgb('#8a6a44')
INK_HI = rgb('#9a1a08')
INK_TITLE = rgb('#5a1a08')
ROSTER_BG = rgb('#17151d')
ROSTER_TXT = rgb('#e8dcc0')
ROSTER_HEAD = rgb('#d8b050')

# How the screen round the view looks.  A game changes any of these with a
# CHROME dict: background and frame name a texture to tile (None for the
# stone of the default), ornament a picture over the top of the view, paper
# and roller the colours of the scroll on the right.
CHROME = dict(background=None, bg_colours=('#8a8884', '#56544f'),
              bg_shade=0.9, frame=None, frame_colours=('#7a7670', '#2e2c28'),
              frame_shade=1.0, bevel=('#c8c4bc', '#2a2824'), moss=True,
              ornament='ornament', paper=('#e2c894', '#9a6a30'),
              roller=('#6a3e14', '#e8b858'))

KITS = {
    'Fighter': ['shortsword', 'leather', 'buckler'],
    'Paladin': ['mace', 'leather', 'buckler'],
    'Rogue':   ['shortsword', 'leather'],
    'Priest':  ['mace', 'leather'],
    'Mage':    ['staff', 'robes'],
}


# ------------------------------------------------------------------ state

class State:
    """Everything that is saved."""

    def __init__(self):
        self.party = []
        self.roster = []
        self.gold = 0
        self.level = ''
        self.x = self.y = self.facing = 0
        self.prev = None
        self.flags = {}
        self.seen = {}
        self.light_r = 0.0
        self.light_turns = 0
        self.sight = 0
        self.steps = 0
        self.won = False
        self.supplies = {}          # ammunition and the like, by kind
        self.saved_at = 0

    def to_json(self):
        d = dict(self.__dict__)
        d['party'] = [c.to_dict() for c in self.party]
        d['roster'] = [c.to_dict() for c in self.roster]
        d['seen'] = {k: sorted(v) for k, v in self.seen.items()}
        return d

    @classmethod
    def from_json(cls, d):
        s = cls()
        s.__dict__.update(d)
        s.party = [Character.from_dict(c) for c in d['party']]
        s.roster = [Character.from_dict(c) for c in d.get('roster', [])]
        s.seen = {k: set(v) for k, v in d.get('seen', {}).items()}
        return s


# ---------------------------------------------------------------- buttons

BTN_FACE = rgb('#7a5a34')
BTN_HI = rgb('#c09860')
BTN_LO = rgb('#2e1e0e')
BTN_TEXT = rgb('#f6ecd4')


def draw_buttons(s, buttons, x, y, w, h=14, gap=2):
    """A row of tap buttons [(label, value), ...] filling width w from x;
    returns [(x0, y0, x1, y1, value)] for hit_button()."""
    rects = []
    n = len(buttons)
    if not n:
        return rects
    bw = (w - gap * (n - 1)) // n
    for i, (label, value) in enumerate(buttons):
        bx = x + i * (bw + gap)
        s.rect(bx, y, bw, h, BTN_FACE)
        s.bevel(bx, y, bw, h, BTN_HI, BTN_LO)
        s.text(bx + bw // 2, y + (h - 9) // 2, label, BTN_TEXT,
               align='center')
        rects.append((bx, y, bx + bw, y + h, value))
    return rects


def hit_button(rects, x, y):
    for (x0, y0, x1, y1, value) in rects:
        if x0 <= x < x1 and y0 <= y < y1:
            return value
    return None


# ------------------------------------------------------------------ modes

class Mode:
    """Something that owns the keyboard: draws itself and handles keys."""
    roster_sel = None
    place = None

    def draw(self, g, s):
        g.draw_scene(s)
        g.draw_log(s)

    def key(self, g, k):
        pass

    def click(self, g, x, y):
        pass

    def update(self, g, dt):
        pass


class Menu(Mode):
    """A prompt with numbered choices on the parchment.

    options: list of labels, or (label, value), or (label, value, enabled).
    on_choose(value) is called after the menu closes; on_cancel() on Esc
    (if given; otherwise Esc does nothing)."""

    def __init__(self, title, options, on_choose, text='', on_cancel=None,
                 view=None, place=None, roster_sel=None, sel=0, keep=False,
                 quiet=False):
        self.title, self.text = title, text
        self.opts = []
        for o in options:
            if isinstance(o, str):
                o = (o, o)
            if len(o) == 2:
                o = (o[0], o[1], True)
            self.opts.append(o)
        self.on_choose, self.on_cancel = on_choose, on_cancel
        self.view = view
        self.place = place
        self.roster_sel = roster_sel
        self.sel = sel
        self.keep = keep            # stay open after choosing
        self.rects = []
        self.top = 0
        while self.sel < len(self.opts) - 1 and not self.opts[self.sel][2]:
            self.sel += 1

    def hotkey(self, i):
        return '123456789abcdefghijklmnopqrstuvwxyz'[i] if i < 35 else ''

    def draw(self, g, s):
        if self.view is None:
            g.draw_scene(s)
        else:
            self.view(g, s)
        self.rects = g.draw_menu(s, self.title, self.text, self.opts,
                                 self.sel, self)

    def choose(self, g, i):
        if not (0 <= i < len(self.opts)) or not self.opts[i][2]:
            g.sound.play('bump')
            return
        g.sound.play('menu')
        if not self.keep:
            g.pop(self)
        self.on_choose(self.opts[i][1])

    def key(self, g, k):
        n = len(self.opts)
        if k in ('up', 'w') and n:
            self.sel = (self.sel - 1) % n
        elif k in ('down', 's') and n:
            self.sel = (self.sel + 1) % n
        elif k in ('enter', 'space'):
            self.choose(g, self.sel)
        elif k == 'esc':
            if self.on_cancel:
                g.pop(self)
                self.on_cancel()
        elif len(k) == 1:
            keys = '123456789abcdefghijklmnopqrstuvwxyz'
            kl = k.lower()
            if kl in keys and keys.index(kl) < n:
                self.choose(g, keys.index(kl))

    def click(self, g, x, y):
        for (i, x0, y0, x1, y1) in self.rects:
            if x0 <= x < x1 and y0 <= y < y1:
                self.sel = i
                self.choose(g, i)
                return
        if self.on_cancel and not (PX <= x < PX + PW and PY <= y < PY + PH) \
                and not (RY <= y):
            g.pop(self)
            self.on_cancel()


class Say(Menu):
    """Text on the parchment until a key is pressed."""

    def __init__(self, text, then=None, title='', view=None, place=None,
                 more='(press a key)'):
        super().__init__(title, [], None, text, view=view, place=place)
        self.then = then
        self.more = more

    def draw(self, g, s):
        super().draw(g, s)
        s.text(TX + TW // 2, TY + TH - 10, self.more, INK_DIM,
               align='center')

    def key(self, g, k):
        if k in ('shift', 'ctrl', 'alt', 'meta'):
            return
        g.pop(self)
        if self.then:
            self.then()

    def click(self, g, x, y):
        self.key(g, 'enter')


class TextInput(Menu):
    def __init__(self, title, text, on_done, maxlen=14, initial='',
                 on_cancel=None, view=None, upper=False):
        super().__init__(title, [], None, text, on_cancel=on_cancel,
                         view=view)
        self.value = initial
        self.on_done = on_done
        self.maxlen = maxlen
        self.upper = upper
        self.blink = 0.0

    def draw(self, g, s):
        super().draw(g, s)
        y = self.text_end + 8
        s.rect(TX, y - 2, TW, 15, rgb('#f2e2b8'))
        s.frame(TX, y - 2, TW, 15, INK_DIM)
        tw = s.text(TX + 4, y + 1, self.value, INK)
        if int(self.blink * 2) % 2 == 0:
            s.rect(TX + 5 + tw, y, 5, 10, INK)
        # a keyboard to tap, for phones
        y += 20
        self.rects = []
        for row in ('ABCDEFGHIJ', 'KLMNOPQRST', "UVWXYZ'-.0"):
            self.rects += draw_buttons(s, [(ch, ch) for ch in row], TX, y,
                                       TW, 15)
            y += 17
        last = [('Space', 'space'), ('Delete', 'backspace'), ('OK', 'enter')]
        if self.on_cancel:
            last.append(('Cancel', 'esc'))
        self.rects += draw_buttons(s, last, TX, y, TW, 15)

    def update(self, g, dt):
        old = int(self.blink * 2)
        self.blink += dt
        if int(self.blink * 2) != old:
            g.dirty = True

    def key(self, g, k):
        if k == 'enter':
            if self.value.strip():
                g.pop(self)
                self.on_done(self.value.strip())
        elif k == 'esc':
            if self.on_cancel:
                g.pop(self)
                self.on_cancel()
        elif k == 'backspace':
            self.value = self.value[:-1]
        elif k == 'space':
            if len(self.value) < self.maxlen:
                self.value += ' '
        elif len(k) == 1 and k.isprintable() and len(self.value) < self.maxlen:
            self.value += k.upper() if self.upper else k

    def click(self, g, x, y):
        k = hit_button(getattr(self, 'rects', []), x, y)
        if k is None:
            return
        if len(k) == 1 and k.isalpha():
            # tapped letters: capitals at the start of each word
            k = k.upper() if (not self.value or self.value[-1] == ' ' or
                              self.upper) else k.lower()
        self.key(g, k)


# ------------------------------------------------------------------- game

class Game:
    def __init__(self, gdef, sound, save_path=None):
        self.d = gdef
        self.id = gdef.ID
        self.title = gdef.TITLE
        self.levels = {k: Level(k, v) for k, v in gdef.LEVELS.items()}
        self.s = Surface(W, H)
        self.view = View(VW, VH)
        self.view.sprite_source = art.sprite_source
        self.sound = sound
        self.save_path = save_path or os.path.join(
            home_dir(), '.%s.json' % self.id)
        self.rng = random.Random()
        self.modes = []
        self.log = []
        self.st = None
        self.dirty = True
        self.quit = False
        self.flash_t = 0.0
        self.flash_rows = {}        # roster row -> time left
        self.view_flash = 0.0
        self.roster_override = None
        self.portrait = False           # set by the shell for an upright
        self.showing_portrait = False   # window
        self.view_flash_col = None
        self.clock = 0.0
        self.warm = None            # a generator preparing the view
        self.warmed_for = None
        self.skies = {}
        self.speed = 1.0
        self.kits = dict(KITS)
        self.kits.update(getattr(gdef, 'KITS', {}))
        self.hooks = getattr(gdef, 'HOOKS', {})
        self.chrome = dict(CHROME)
        self.chrome.update(getattr(gdef, 'CHROME', {}))
        words.setup(getattr(gdef, 'WORDS', {}))
        self.tunes = dict(music.TUNES)
        self.tunes.update(getattr(gdef, 'MUSIC', {}))
        self._build_base()
        from .modes import TitleMode
        self.push(TitleMode())

    # ---------------------------------------------------------- mode stack

    @property
    def mode(self):
        return self.modes[-1]

    def push(self, m):
        self.modes.append(m)
        self.dirty = True
        return m

    def pop(self, m=None):
        if m is None or (self.modes and self.modes[-1] is m):
            self.modes.pop()
        elif m in self.modes:
            self.modes.remove(m)
        self.dirty = True

    def replace_all(self, m):
        self.modes = [m]
        self.dirty = True

    def ask(self, title, options, on_choose, text='', on_cancel=None, **kw):
        return self.push(Menu(title, options, on_choose, text, on_cancel,
                              **kw))

    def tell(self, text, then=None, title='', **kw):
        return self.push(Say(text, then, title, **kw))

    def yesno(self, text, on_yes, on_no=None, title=''):
        def done(v):
            if v:
                on_yes()
            elif on_no:
                on_no()
        self.ask(title, [('Yes', True), ('No', False)], done, text,
                 on_cancel=on_no or (lambda: None))

    # ----------------------------------------------------------- the log

    def say(self, text, colour=None):
        for line in font.wrap(text, TW):
            self.log.append((line, colour))
        self.log = self.log[-120:]
        self.dirty = True

    # ------------------------------------------------------------ helpers

    @property
    def level(self):
        return self.levels[self.st.level]

    @property
    def party(self):
        return self.st.party

    def flag(self, name):
        return self.st.flags.get(name)

    def set_flag(self, name, value=True):
        self.st.flags[name] = value

    def sqkey(self, x=None, y=None, what=''):
        if x is None:
            x, y = self.st.x, self.st.y
        return '%s:%d,%d%s' % (self.st.level, x, y, what)

    def ahead(self, n=1, rel=0):
        dx, dy = DIRS[(self.st.facing + rel) % 4]
        return self.st.x + dx * n, self.st.y + dy * n

    def has_item(self, iid):
        for c in self.party:
            if iid in c.pack or iid in c.equip.values():
                return c
        return None

    def take_item(self, iid):
        for c in self.party:
            if iid in c.pack:
                c.pack.remove(iid)
                return True
        return False

    def give_party(self, iid):
        """Put an item in the first pack with room; returns who got it."""
        for c in self.party:
            if c.alive and c.give(iid):
                return c
        for c in self.party:
            if c.give(iid):
                return c
        return None

    def living(self):
        return [c for c in self.party if c.alive]

    def able(self):
        return [c for c in self.party if c.able]

    def item_name(self, iid):
        return ITEMS[iid]['name'] if iid in ITEMS else iid

    # ------------------------------------------------------------ saving

    SLOTS = 6

    def save(self, quiet=True, path=None):
        """Save to the autosave (or to path, a save slot)."""
        if not self.st:
            return False
        path = path or self.save_path
        try:
            import time
            self.st.saved_at = time.time()
            with open(path + '.tmp', 'w') as f:
                json.dump(self.st.to_json(), f)
            os.replace(path + '.tmp', path)
            if not quiet:
                self.say('Game saved.', INK_DIM)
            return True
        except OSError as e:
            self.say('Could not save: %s' % e, INK_HI)
            return False

    def has_save(self):
        return os.path.exists(self.save_path)

    def slot_path(self, n):
        base = self.save_path[:-5] if self.save_path.endswith('.json') \
            else self.save_path
        return '%s-%d.json' % (base, n)

    def slot_info(self, n):
        """A line describing save slot n, or None if it is empty."""
        import time
        try:
            with open(self.slot_path(n)) as f:
                d = json.load(f)
            where = self.levels[d['level']].name
            lv = max(c['level'] for c in d['party'])
            when = time.strftime('%d %b %H:%M',
                                 time.localtime(d.get('saved_at', 0)))
            return '%s, level %d, %s' % (where, lv, when)
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def any_slots(self):
        return any(self.slot_info(n) for n in range(1, self.SLOTS + 1))

    def load(self, path=None):
        try:
            with open(path or self.save_path) as f:
                st = State.from_json(json.load(f))
        except (OSError, ValueError, KeyError, TypeError):
            return False
        if st.level not in self.levels:
            return False
        self.st = st
        self.log = []
        self.say('Welcome back to %s.' % self.level.name)
        from .modes import ExploreMode
        self.replace_all(ExploreMode())
        self.mark_seen()
        return True

    def new_game(self):
        st = State()
        d = self.d
        for spec in d.PARTY:
            c = Character.roll_new(spec['name'], spec['race'], spec['cls'],
                                   self.rng)
            for k in rules.STATS:
                if k in spec:
                    setattr(c, k, spec[k])
            for k in ('powers', 'traits'):
                if k in spec:
                    setattr(c, k, list(spec[k]))
            if rules.HOOKS['start_hp']:
                c.maxhp = rules.HOOKS['start_hp'](c, self.rng)
            c.maxhp = c.hp = max(c.maxhp, spec.get('hp', 0))
            c.maxsp = c.sp_for_level(1)
            c.sp = c.maxsp
            for iid in spec.get('gear', self.kits.get(c.cls, [])):
                c.give(iid)
                c.equip_item(len(c.pack) - 1)
            for iid in spec.get('pack', []):
                c.give(iid)
            st.party.append(c)
        st.gold = getattr(d, 'GOLD', 100)
        st.supplies = dict(getattr(d, 'SUPPLIES', {}))
        lid, x, y, f = d.START
        st.level, st.x, st.y, st.facing = lid, x, y, f
        self.st = st
        self.log = []
        from .modes import ExploreMode
        self.replace_all(ExploreMode())
        self.mark_seen()
        self.save()

    # ------------------------------------------------------------ the view

    def light_radius(self):
        L = self.level
        sq = L.sq(self.st.x, self.st.y)
        if sq.get('dark'):
            return 0.62
        if L.outdoor:
            return L.theme.get('light', 8.0)
        r = L.theme.get('ambient', 1.25)
        if self.st.light_turns > 0:
            r = max(r, self.st.light_r)
        for c in self.party:
            if c.able and c.trait('sight'):
                r = max(r, c.trait('sight'))
        return r

    def award_xp(self, amount, lines=None):
        """Experience shared among the living (for treasure, say)."""
        alive = [c for c in self.party if c.alive]
        if amount <= 0 or not alive:
            return
        share = amount // len(alive)
        for c in alive:
            c.xp += share
        text = 'Each of you gains %d experience.' % share
        if lines is not None:
            lines.append(text)
        else:
            self.say(text)

    def look_at(self, X, Y):
        L = self.level
        sq = L.sq(X, Y)
        t = L.theme
        if sq.get('solid'):
            if sq.get('door'):
                locked = sq['door'] == 'locked' and \
                    not self.flag(self.sqkey(X, Y, ':open'))
                tex = sq.get('wall') or t.get('locked' if locked else 'door',
                                              'plain')
            elif sq.get('riddle'):
                solved = self.flag(sq['riddle'].get('flag') or
                                   self.sqkey(X, Y, ':open'))
                tex = sq.get('wall') or t.get('door' if solved else 'locked',
                                              'plain')
            elif sq.get('secret') and (self.st.sight > 0 or
                                       self.flag(self.sqkey(X, Y, ':found'))):
                tex = t.get('door', 'plain')
            else:
                tex = L.wall_texture(X, Y, sq)
            return Look(True, tex)
        if sq.get('dark'):
            return Look(False)
        floor = sq.get('floor') or t.get('floor')
        if floor == '@stairs':
            floor = t.get('stairs') or t.get('floor')
        ceil = sq.get('ceil', t.get('ceil'))
        sprite = sq.get('sprite')
        if sq.get('requires') and not self.flag(sq['requires']):
            sprite = None
        elif sq.get('chest') and self.flag(self.sqkey(X, Y, ':chest')):
            sprite = sq.get('sprite_open', 'chest_open')
        elif sq.get('fight') and sq.get('sprite_after') is not None and \
                self.flag(sq.get('flag') or self.sqkey(X, Y, ':won')):
            sprite = sq.get('sprite_after') or None
        elif sq.get('unless') and self.flag(sq['unless']) and \
                'sprite_after' in sq:
            sprite = sq['sprite_after'] or None
        return Look(False, None, floor, ceil, sprite)

    def draw_scene(self, s, dim=None):
        st = self.st
        if st is None:
            s.rect(VX, VY, VW, VH, (0, 0, 0))
            return
        L = self.level
        f = st.facing
        dx, dy = DIRS[f]
        rx, ry = DIRS[(f + 1) % 4]
        sx, sy = st.x, st.y

        def look(k, x):
            return self.look_at(sx + dx * k + rx * x, sy + dy * k + ry * x)

        sky = None
        if L.outdoor:
            key = (L.theme.get('sky_top', '#2c4c8c'),
                   L.theme.get('sky_horizon', '#c4d4e0'))
            sky = self.skies.get(key)
            if sky is None:
                sky = self.skies[key] = make_sky(VW, VH // 2, *key)
        fog = rgb(L.theme.get('fog', '#000000'))
        self.view.render(s, VX, VY, look, self.light_radius(), fog, sky)
        if L.theme.get('falling'):
            self.draw_falling(s, L.theme['falling'])
        if dim is not None:
            s.darken(VX, VY, VW, VH, dim)

    def draw_falling(self, s, colour):
        """Ash, snow or rain drifting down over the view."""
        t = self.clock
        c = rgb(colour)
        dark = scale(c, 0.6)
        rng = random.Random(11)
        for i in range(70):
            x0 = rng.uniform(0, VW)
            speed = rng.uniform(10, 26)
            ph = rng.uniform(0, VH)
            sway = rng.uniform(2, 6)
            y = (ph + t * speed) % VH
            x = (x0 + math.sin(t * 0.8 + i) * sway) % VW
            big = rng.random() < 0.3
            s.rect(VX + int(x), VY + int(y), 2 if big else 1, 1,
                   c if big else dark)

    # ------------------------------------------------------------- chrome

    def _build_base(self):
        ch = self.chrome
        s = Surface(W, H)
        if ch['background']:
            s.put(0, 0, W, H, art.texture_panel(W, H, ch['background'],
                                                ch['bg_shade']))
        else:
            s.put(0, 0, W, H, art.stone_panel(W, H, 3, *ch['bg_colours']))
            s.darken(0, 0, W, H, ch['bg_shade'])
        # the frame round the view
        if ch['frame']:
            s.put(8, 8, 344, 266, art.texture_panel(344, 266, ch['frame'],
                                                    ch['frame_shade']))
        else:
            s.put(8, 8, 344, 266, art.stone_panel(344, 266, 8,
                                                  *ch['frame_colours'],
                                                  [10, 12, 10]))
        hi, lo = rgb(ch['bevel'][0]), rgb(ch['bevel'][1])
        s.bevel(8, 8, 344, 266, hi, lo, 2)
        s.bevel(VX - 2, VY - 2, VW + 4, VH + 4, lo, hi, 2)
        s.bevel(NX - 2, NY - 2, NW + 4, NH + 4, lo, hi, 1)
        rng = random.Random(4)
        for _ in range(90 if ch['moss'] else 0):
            # moss clumps on the frame
            side = rng.randrange(4)
            if side == 0:
                x, y = rng.randrange(10, 350), rng.randrange(9, 17)
            elif side == 1:
                x, y = rng.randrange(10, 350), rng.randrange(VY + VH + 2, 272)
            elif side == 2:
                x, y = rng.randrange(9, 17), rng.randrange(10, 270)
            else:
                x, y = rng.randrange(VX + VW + 2, 350), rng.randrange(10, 270)
            r = rng.randint(1, 3)
            for yy in range(y - r, y + r + 1):
                for xx in range(x - r, x + r + 1):
                    if (xx - x) ** 2 + (yy - y) ** 2 <= r * r and \
                            rng.random() < 0.8:
                        c = rng.choice(['#3e6a24', '#4e7a2c', '#2e5a1c',
                                        '#62903a'])
                        if not (VX <= xx < VX + VW and VY <= yy < VY + VH) \
                                and not (NX <= xx < NX + NW and
                                         NY <= yy < NY + NH):
                            s.pixel(xx, yy, c)
        # the parchment
        par = art.parchment(PW - 12, PH - 24, 5, *ch['paper'])
        from .gfx import Image
        s.blit(Image.from_pixels(PW - 12, PH - 24, par), PX + 6, PY + 12)
        roll = Image.from_pixels(PW, 14, art.scroll_roll(PW, 14,
                                                         *ch['roller']))
        s.blit(roll, PX, PY)
        s.blit(roll, PX, PY + PH - 14)
        # the roster panel
        s.rect(RX, RY, RW, RH, ROSTER_BG)
        s.bevel(RX, RY, RW, RH, rgb('#4a4658'), rgb('#08070a'), 2)
        s.rect(RX + 6, RY + 17, RW - 12, 1, rgb('#4a4030'))
        s.rect(NX, NY, NW, NH, (0, 0, 0))
        self.base = bytes(s.buf)

    def draw_log(self, s, lines=None, bottom=TY + TH):
        lines = self.log if lines is None else lines
        n = (bottom - TY) // font.LINE
        show = lines[-n:]
        y = bottom - len(show) * font.LINE
        for i, (text, col) in enumerate(show):
            age = len(show) - 1 - i
            c = col or (INK if age < 6 else mix(INK, INK_DIM, min(1, (age - 5) / 8)))
            s.text(TX, y, text, c)
            y += font.LINE

    def draw_menu(self, s, title, text, opts, sel, menu):
        y = TY
        if title:
            s.text(TX + TW // 2, y, title, INK_TITLE, align='center')
            tw = font.width(title)
            s.rect(TX + TW // 2 - tw // 2, y + 10, tw, 1, INK_DIM)
            y += font.LINE + 5
        if text:
            for line in font.wrap(text, TW):
                if y > TY + TH - font.LINE:
                    break
                s.text(TX, y, line, INK)
                y += font.LINE
            y += 5
        menu.text_end = y
        rects = []
        room = (TY + TH - y) // font.LINE
        if room <= 0 or not opts:
            return rects
        top = menu.top
        if sel < top:
            top = sel
        if sel >= top + room:
            top = sel - room + 1
        top = max(0, min(top, max(0, len(opts) - room)))
        menu.top = top
        for i in range(top, min(len(opts), top + room)):
            label, _, ok = opts[i]
            hk = menu.hotkey(i)
            col = INK_HI if i == sel else INK if ok else INK_DIM
            if i == sel:
                s.rect(TX - 4, y - 1, TW + 8, font.LINE, rgb('#e8cc90'))
                s.text(TX - 2, y, font.RIGHT, INK_HI)
            if hk:
                s.text(TX + 8, y, hk + ')', col)
            if '\t' in label:
                label, right = label.split('\t', 1)
                s.text(TX + TW - 10, y, right, col, align='right')
            s.text(TX + 22, y, label, col)
            rects.append((i, TX - 4, y - 1, TX + TW + 4, y + font.LINE - 1))
            y += font.LINE
        if top > 0:
            s.text(TX + TW - 6, menu.text_end, font.UP, INK_DIM)
        if top + room < len(opts):
            s.text(TX + TW - 6, TY + TH - font.LINE, font.DOWN, INK_DIM)
        return rects

    def draw_roster(self, s, sel=None):
        cols = [(RX + 10, '#'), (RX + 24, 'Name'), (RX + 150, w('class')),
                (RX + 262, 'Lv'), (RX + 296, 'AC'), (RX + 330, 'Hits'),
                (RX + 420, w('pts')), (RX + 520, 'Status')]
        for x, t in cols:
            s.text(x, RY + 5, t, ROSTER_HEAD)
        if not self.st:
            return
        y = RY + 21
        over = self.roster_override or {}
        for i, c in enumerate(self.party):
            hp, status, sp = over.get(i, (c.hp, c.status, c.sp))
            if sel == i:
                s.rect(RX + 4, y - 2, RW - 8, 14, rgb('#3c3456'))
                s.frame(RX + 4, y - 2, RW - 8, 14, rgb('#8a7ab0'))
            t = self.flash_rows.get(i, 0)
            if t > 0:
                s.rect(RX + 4, y - 2, RW - 8, 14, rgb('#801010'))
            col = ROSTER_TXT
            if status in ('dead', 'stoned'):
                col = rgb('#7a7480')
            elif status == 'poisoned':
                col = rgb('#9ae070')
            elif status in ('paralyzed', 'asleep'):
                col = rgb('#80b0ff')
            elif hp <= c.maxhp // 4:
                col = rgb('#ff8060')
            s.text(cols[0][0], y, str(i + 1), ROSTER_HEAD)
            s.text(cols[1][0], y, c.name, col)
            who = '%s %s' % (c.race, c.cls)
            if font.width(who) > cols[3][0] - cols[2][0] - 4:
                who = c.cls
            s.text(cols[2][0], y, who, col)
            s.text(cols[3][0] + 10, y, str(c.level), col, align='right')
            ac = c.ac()
            s.text(cols[4][0] + 12, y, str(ac) if ac > -10 else 'LO', col,
                   align='right')
            s.text(cols[5][0] + 28, y, '%d/%d' % (hp, c.maxhp), col,
                   align='right')
            # a little bar of hit points
            bw = 42
            frac = 0 if c.maxhp <= 0 else max(0, min(1, hp / c.maxhp))
            s.rect(cols[5][0] + 34, y + 3, bw, 4, rgb('#3a1010'))
            s.rect(cols[5][0] + 34, y + 3, int(bw * frac), 4,
                   rgb('#40c040') if frac > 0.5 else rgb('#e0b020')
                   if frac > 0.25 else rgb('#e03020'))
            if c.maxsp:
                s.text(cols[6][0] + 28, y, '%d/%d' % (sp, c.maxsp), col,
                       align='right')
                frac = max(0, min(1, sp / c.maxsp))
                s.rect(cols[6][0] + 34, y + 3, bw, 4, rgb('#101a3a'))
                s.rect(cols[6][0] + 34, y + 3, int(bw * frac), 4,
                       rgb('#5080ff'))
            st = w(status)
            if status == 'ok' and c.can_level():
                st = w('trainable')
            s.text(cols[7][0], y, st, col)
            y += 15

    def draw_nameplate(self, s, place=None):
        if not self.st:
            text = place or ''
        else:
            text = place or self.level.name
        s.text(NX + NW // 2, NY + 3, text, rgb('#f0e6d0'), align='center')
        if self.st:
            letter = DIR_LETTERS[self.st.facing]
            s.rect(NX + 2, NY + 1, 13, 13, rgb('#3a3020'))
            s.text(NX + 9, NY + 3, letter, rgb('#ffd860'), align='center')
            g = '%s %d' % (font.COIN, self.st.gold)
            s.text(NX + NW - 4, NY + 3, g, rgb('#ffd860'), align='right')
            fx = NX + 20
            if self.st.light_turns > 0 and not self.level.outdoor:
                s.text(fx, NY + 3, '*', rgb('#ffb040'))
                fx += 8
            if self.st.sight > 0:
                s.text(fx, NY + 3, 'o', rgb('#a0d0ff'))

    # ------------------------------------------------------------ drawing

    def render(self):
        s = self.s
        s.put(0, 0, W, H, self.base)
        m = self.mode
        m.draw(self, s)
        if self.view_flash > 0:
            if self.view_flash_col is None:
                s.translate(VX, VY, VW, VH, bytes(min(255, i + 90)
                                                    for i in range(256)))
            else:
                self.wash(s, self.view_flash_col)
        if not getattr(m, 'full', False) and self.chrome['ornament']:
            orn = art.get(self.chrome['ornament'])
            s.blit(orn, VX + VW // 2 - orn.w // 2, 0)
        if not getattr(m, 'full', False):
            self.draw_nameplate(s, getattr(m, 'place', None))
        self.draw_roster(s, getattr(m, 'roster_sel', None))
        self.dirty = False
        return s

    def frame(self):
        """The picture for the shell to show: the wide screen, or the
        upright one when the shell has set self.portrait (and the mode
        doesn't need the full width)."""
        s = self.render()
        self.showing_portrait = self.portrait and \
            not getattr(self.mode, 'full', False)
        if self.showing_portrait:
            from . import layout
            return layout.compose(self, s)
        return s

    def tap(self, x, y):
        """A click or touch on the picture frame() last returned."""
        if self.showing_portrait:
            from . import layout
            p = layout.to_wide(x, y)
            if p is None:
                return
            x, y = p
        if 0 <= x < W and 0 <= y < H:
            self.click(x, y)

    # ----------------------------------------------------------- input

    def key(self, k):
        if not self.modes:
            return
        self.mode.key(self, k)
        self.dirty = True

    def click(self, x, y):
        if not self.modes:
            return
        self.mode.click(self, x, y)
        self.dirty = True

    def music_for(self):
        """The tune that suits what is on the screen."""
        from .modes import TitleMode, EndMode, GameOverMode
        from .combat import CombatMode
        kinds = [type(m) for m in self.modes]
        if not self.modes or TitleMode in kinds or not self.st:
            return 'title'
        if GameOverMode in kinds:
            return None
        if EndMode in kinds:
            return 'victory'
        if CombatMode in kinds:
            return 'combat'
        L = self.level
        return L.spec.get('music') or ('town' if L.outdoor else 'dungeon')

    def warm_jobs(self):
        """Everything the current level and light will want drawn."""
        L = self.level
        t = L.theme
        walls = {t.get('wall'), t.get('door'), t.get('locked')}
        walls |= {name for name, _ in t.get('variants', ())}
        floors = {t.get('floor'), t.get('stairs')}
        ceils = {t.get('ceil')}
        sprites = set()
        for sq in L.legend.values():
            w_ = sq.get('wall')
            walls |= set(w_) if isinstance(w_, (list, tuple)) else {w_}
            if sq.get('floor') and sq['floor'] != '@stairs':
                floors.add(sq['floor'])
            if sq.get('ceil'):
                ceils.add(sq['ceil'])
            for key in ('sprite', 'sprite_after', 'sprite_open'):
                if sq.get(key):
                    sprites.add(sq[key])
            if sq.get('chest') and not sq.get('sprite_open'):
                sprites.add('chest_open')
        known = set(textures.names())
        walls = sorted(x for x in walls if x in known)
        floors = sorted(x for x in floors if x in known)
        ceils = [] if L.outdoor else sorted(x for x in ceils if x in known)
        sprites = sorted(x for x in sprites if x in art.names())
        fog = L.theme.get('fog', '#000000')
        for _ in self.view.prepare(self.light_radius(), fog, walls, floors,
                                   ceils, sprites):
            yield
        # the monsters met here
        kinds = {k for _, groups in L.encounters for (k, lo, hi) in groups}
        kinds |= {k for sq in L.legend.values()
                  for (k, n) in sq.get('fight', [])}
        for k in sorted(kinds):
            if k in rules.MONSTERS:
                art.get(rules.MONSTERS[k]['art'])
                yield

    def keep_warm(self, budget=0.02):
        """Run the view's preparation for up to budget seconds."""
        if not self.st:
            return
        want = (self.st.level, self.light_radius())
        if want != self.warmed_for:
            self.warmed_for = want
            self.warm = self.warm_jobs()
        if self.warm is None:
            return
        import time
        end = time.perf_counter() + budget
        try:
            while time.perf_counter() < end:
                next(self.warm)
        except StopIteration:
            self.warm = None

    def update(self, dt):
        self.clock += dt
        self.keep_warm()
        if hasattr(self.sound, 'tick'):
            self.sound.music(self.music_for())
            self.sound.tick()
        if self.st and self.levels[self.st.level].theme.get('falling') and \
                int(self.clock * 12) != int((self.clock - dt) * 12):
            self.dirty = True
        if self.view_flash > 0:
            self.view_flash -= dt
            self.dirty = True
        for k in list(self.flash_rows):
            self.flash_rows[k] -= dt
            if self.flash_rows[k] <= 0:
                del self.flash_rows[k]
            self.dirty = True
        if self.modes:
            self.mode.update(self, dt)

    def flash(self, colour=None, t=0.15):
        """Flash the view: brighter (colour None), or washed with a
        colour, as a spell is cast."""
        self.view_flash = t
        self.view_flash_col = rgb(colour) if colour else None

    def wash(self, s, c):
        """Every other pixel of the view, in a checkerboard, set to c."""
        buf = s.buf
        n = VW // 2
        for y in range(VY, VY + VH):
            start = (y * W + VX + (y & 1)) * 3
            end = start + n * 6
            for ch in range(3):
                buf[start + ch:end:6] = bytes((c[ch],)) * n

    def hurt_flash(self, i):
        self.flash_rows[i] = 0.25

    # ------------------------------------------------------- moving about

    def mark_seen(self):
        """Remember the squares the party can see from here."""
        st = self.st
        L = self.level
        seen = st.seen.setdefault(st.level, set())
        f = st.facing
        dx, dy = DIRS[f]
        rx, ry = DIRS[(f + 1) % 4]
        R = self.light_radius()
        depth = max(1, int(R + 0.5))
        if L.outdoor:
            depth = 6
        for nb in range(4):
            ox, oy = DIRS[nb]
            seen.add((st.y + oy) * L.w + st.x + ox)
        seen.add(st.y * L.w + st.x)
        for k in range(0, depth + 1):
            X, Y = st.x + dx * k, st.y + dy * k
            if not (0 <= X < L.w and 0 <= Y < L.h):
                break
            seen.add(Y * L.w + X)
            for side in (-1, 1):
                sx, sy = X + rx * side, Y + ry * side
                if 0 <= sx < L.w and 0 <= sy < L.h:
                    seen.add(sy * L.w + sx)
            if L.sq(X, Y).get('solid'):
                break

    def turn(self, d):
        self.st.facing = (self.st.facing + d) % 4
        self.mark_seen()

    def walk(self, rel):
        """Try to move: rel 0 forward, 1 right, 2 back, 3 left."""
        st = self.st
        L = self.level
        d = (st.facing + rel) % 4
        dx, dy = DIRS[d]
        nx, ny = st.x + dx, st.y + dy
        sq = L.sq(nx, ny)
        if sq.get('solid') or self.active(sq).get('block'):
            self.bump(nx, ny, self.active(sq), d)
            return
        self.move_to(nx, ny)

    def move_to(self, x, y, facing=None, quiet=False):
        st = self.st
        st.prev = [st.x, st.y]
        st.x, st.y = x, y
        if facing is not None:
            st.facing = facing
        if not quiet:
            self.sound.play('step')
        self.mark_seen()
        self.after_step()

    def pass_through(self, wx, wy, d, what='door'):
        """Go through the door at wx, wy into the square beyond."""
        dx, dy = DIRS[d]
        bx, by = wx + dx, wy + dy
        if self.level.sq(bx, by).get('solid'):
            self.sound.play('bump')
            return
        self.sound.play('door')
        st = self.st
        st.prev = [st.x, st.y]
        st.x, st.y = bx, by
        self.mark_seen()
        self.after_step()

    def bump(self, x, y, sq, d):
        if sq.get('talk'):
            from .talk import talk
            talk(self, sq)
            return
        if sq.get('block'):
            self.sound.play('bump')
            return
        if sq.get('shop'):
            from .town import enter_shop
            enter_shop(self, sq)
            return
        if sq.get('goto') and not sq.get('door'):
            self.ask_goto(sq)
            return
        if sq.get('hook'):
            fn = self.hooks.get(sq['hook'])
            if fn:
                fn(self, sq, lambda: None)
                return
        if sq.get('riddle'):
            self.riddle(x, y, sq, d)
            return
        if sq.get('door'):
            if sq['door'] == 'locked' and not self.flag(self.sqkey(x, y, ':open')):
                self.locked_door(x, y, sq, d)
                return
            self.pass_through(x, y, d)
            return
        if sq.get('secret'):
            if not self.flag(self.sqkey(x, y, ':found')):
                self.set_flag(self.sqkey(x, y, ':found'))
                self.say('The wall gives way: a hidden door!')
            self.pass_through(x, y, d)
            return
        if sq.get('msg_bump'):
            self.tell(sq['msg_bump'])
        self.sound.play('bump')

    def ask_goto(self, sq):
        lid, x, y, f = sq['goto']
        word = sq.get('stairs')
        if sq.get('ask'):
            q = sq['ask']
        elif word == 'down':
            q = 'There are stairs going down here. Take them?'
        elif word == 'up':
            q = 'There are stairs going up here. Take them?'
        else:
            q = sq.get('ask', 'Go on to %s?' % self.levels[lid].name)
        self.yesno(q, lambda: self.change_level(lid, x, y, f))

    def change_level(self, lid, x, y, f):
        self.sound.play('stairs')
        st = self.st
        st.level, st.x, st.y, st.facing = lid, x, y, f
        st.prev = None
        self.say('You enter %s.' % self.level.name, INK_TITLE)
        self.mark_seen()
        self.save()
        sq = self.level.sq(x, y)
        if sq.get('msg') and not (sq.get('once') and
                                  self.flag(self.sqkey(what=':msg'))):
            self.arrive(skip_goto=True)

    def after_step(self):
        st = self.st
        st.steps += 1
        if st.light_turns > 0:
            st.light_turns -= 1
            if st.light_turns == 0:
                self.say(w('light_out'), INK_DIM)
        if st.sight > 0:
            st.sight -= 1
            if st.sight == 0:
                self.say('Your truesight fades.', INK_DIM)
        if st.steps % 6 == 0:
            for c in self.party:
                if c.alive and c.sp < c.maxsp and c.status != 'paralyzed':
                    c.sp += 1
        if st.steps % 4 == 0:
            for c in self.party:
                regen = c.trait('regen')
                if regen and c.alive and c.hp < c.maxhp:
                    c.hp = min(c.maxhp, c.hp + regen)
        if st.steps % 5 == 0:
            for i, c in enumerate(self.party):
                if c.status == 'poisoned':
                    c.hp -= 1
                    self.hurt_flash(i)
                    if c.hp <= 0:
                        c.hp = 0
                        c.status = 'dead'
                        self.say(w('poison_kills', c.name), INK_HI)
                        self.sound.play('die')
            if self.check_wipe():
                return
        self.arrive()

    def check_wipe(self):
        if not any(c.able for c in self.party):
            from .modes import GameOverMode
            self.push(GameOverMode())
            return True
        return False

    # ---------------------------------------------------- squares' events

    def arrive(self, skip_goto=False):
        st = self.st
        L = self.level
        sq = self.active(L.sq(st.x, st.y))
        if sq.get('setflag'):
            self.set_flag(sq['setflag'])
        steps = []
        if sq.get('spin'):
            st.facing = self.rng.randrange(4)
            self.mark_seen()
        if sq.get('rad'):
            steps.append(lambda nxt: self.ev_radiation(sq, nxt))
        if sq.get('trap'):
            steps.append(lambda nxt: self.ev_trap(sq, nxt))
        if sq.get('msg'):
            steps.append(lambda nxt: self.ev_msg(sq, nxt))
        if sq.get('teleport'):
            steps.append(lambda nxt: self.ev_teleport(sq, nxt))
        fixed = False
        if sq.get('fight') and not self.flag(sq.get('flag') or
                                             self.sqkey(what=':won')):
            fixed = True
            steps.append(lambda nxt: self.ev_fight(sq, nxt))
        if sq.get('chest') and not self.flag(self.sqkey(what=':chest')):
            steps.append(lambda nxt: self.ev_chest(sq, nxt))
        if sq.get('fountain'):
            steps.append(lambda nxt: self.ev_fountain(sq, nxt))
        if sq.get('item') and not self.flag(self.sqkey(what=':item')):
            steps.append(lambda nxt: self.ev_item(sq, nxt))
        if sq.get('hook') and not sq.get('solid'):
            fn = self.hooks.get(sq['hook'])
            if fn:
                steps.append(lambda nxt: fn(self, sq, nxt))
        if sq.get('goto') and not skip_goto:
            steps.append(lambda nxt: (self.ask_goto(sq), nxt()))
        if not fixed and not sq.get('goto') and L.rate and L.encounters:
            if self.rng.random() < L.rate:
                steps.append(lambda nxt: self.random_encounter(nxt))
        self.run_chain(steps)

    def active(self, sq):
        """A square's legend entry, without its events if it is switched
        off ('unless' a flag is set, or it 'requires' one that isn't)."""
        if (sq.get('unless') and self.flag(sq['unless'])) or \
                (sq.get('requires') and not self.flag(sq['requires'])):
            return {k: v for k, v in sq.items()
                    if k in ('floor', 'ceil', 'dark', 'antimagic', 'solid',
                             'wall')}
        return sq

    def run_chain(self, steps):
        if not steps:
            return
        first, rest = steps[0], steps[1:]
        first(lambda: self.run_chain(rest))

    def ev_msg(self, sq, nxt):
        key = self.sqkey(what=':msg')
        if sq.get('once') and self.flag(key):
            nxt()
            return
        self.set_flag(key)
        if sq.get('flag') and not sq.get('fight'):
            self.set_flag(sq['flag'])       # something learned by reading
        self.tell(sq['msg'], nxt, title=sq.get('title', ''))

    def ev_teleport(self, sq, nxt):
        x, y, f = sq['teleport']
        self.sound.play('magic')
        self.flash('#c080ff', 0.2)
        st = self.st
        st.x, st.y = x, y
        if f is not None:
            st.facing = f
        self.mark_seen()
        if sq.get('tmsg'):
            self.say(sq['tmsg'])
        nxt()

    def ev_trap(self, sq, nxt):
        t = sq['trap']
        key = self.sqkey(what=':trap')
        if t.get('once') and self.flag(key):
            nxt()
            return
        self.set_flag(key)
        self.sound.play('trap')
        lines = [t.get('msg', 'A trap!')]
        for i, c in enumerate(self.party):
            if not c.alive:
                continue
            dmg = roll(t.get('dmg', '1d6'), self.rng)
            if rules.save(c, 'trap', self.rng):
                dmg //= 2
            if dmg <= 0:
                continue
            c.hp -= dmg
            self.hurt_flash(i)
            if c.hp <= 0:
                c.hp = 0
                c.status = 'dead'
                lines.append('%s is killed!' % c.name)
            else:
                lines.append('%s takes %d damage.' % (c.name, dmg))
        for l in lines:
            self.say(l, INK_HI)
        if self.check_wipe():
            return
        self.tell('\n'.join(lines), nxt)

    def ev_radiation(self, sq, nxt):
        """A square hot with radiation: each of the living saves, and
        takes the radiation class in d6s (half on a save)."""
        cls = sq['rad']
        lines = []
        for i, c in enumerate(self.party):
            if not c.alive or c.trait('rad_immune'):
                continue
            dmg = roll('%dd6' % cls, self.rng)
            if rules.save(c, 'radiation', self.rng):
                dmg //= 2
            else:
                c.radfail += 1
            if dmg <= 0:
                continue
            c.hp -= dmg
            self.hurt_flash(i)
            if c.hp <= 0:
                c.hp = 0
                c.status = 'dead'
                lines.append(w('rad_kills', c.name))
            else:
                lines.append(w('rad_hurt', c.name, dmg))
                if c.radfail >= 5 and rules.HOOKS['on_radiation']:
                    c.radfail = 0
                    note = rules.HOOKS['on_radiation'](self, c)
                    if note:
                        lines.append(note)
        self.flash('#80ff40', 0.3)
        self.sound.play('trap')
        for l in lines:
            self.say(l, INK_HI)
        if self.check_wipe():
            return
        if lines and sq.get('rad_msg') and not self.flag(self.sqkey(what=':rad')):
            self.set_flag(self.sqkey(what=':rad'))
            self.tell(sq['rad_msg'] + '\n\n' + '\n'.join(lines), nxt)
            return
        nxt()

    def ev_item(self, sq, nxt):
        iid = sq['item']
        who = self.give_party(iid)
        if who:
            self.set_flag(self.sqkey(what=':item'))
            self.sound.play('coin')
            text = sq.get('item_msg', 'You find %s.' % self.item_name(iid))
            self.say('%s takes the %s.' % (who.name, self.item_name(iid)))
            self.tell(text + '\n\n%s takes it.' % who.name, nxt)
        else:
            self.tell('You find %s, but nobody has room to carry it.'
                      % self.item_name(iid), nxt)

    def ev_fight(self, sq, nxt):
        groups = []
        for (kind, n) in sq['fight']:
            groups.append((kind, n))
        flag = sq.get('flag') or self.sqkey(what=':won')

        def won():
            self.set_flag(flag)
            if sq.get('after'):
                self.tell(sq['after'], nxt)
            else:
                nxt()

        def go():
            self.start_combat(groups, on_win=won, can_run=sq.get('run', True),
                              fled_back=True)

        if sq.get('fight_msg'):
            self.tell(sq['fight_msg'], go)
        else:
            go()

    def random_encounter(self, nxt):
        L = self.level
        total = sum(wt for wt, _ in L.encounters)
        r = self.rng.uniform(0, total)
        for wt, groups in L.encounters:
            r -= wt
            if r <= 0:
                break
        gs = []
        for (kind, lo, hi) in groups:
            gs.append((kind, self.rng.randint(lo, hi)))
        self.start_combat(gs, on_win=nxt)

    def start_combat(self, groups, on_win=None, can_run=True,
                     fled_back=False):
        from .combat import CombatMode
        self.sound.play('fight')
        m = self.push(CombatMode(self, groups, on_win, can_run, fled_back))
        m.begin(self)

    def ev_chest(self, sq, nxt):
        ch = sq['chest']
        key = self.sqkey(what=':chest')
        trapped = ch.get('trap') and not self.flag(key + 'safe')
        rogues = [c for c in self.able() if rules.skilled(c, 'traps')]

        def open_it():
            if trapped:
                self.spring_chest_trap(ch['trap'])
            self.set_flag(key)
            lines = []
            gold = roll(ch.get('gold', '0'), self.rng)
            if gold:
                self.st.gold += gold
                lines.append(w('chest_money', gold))
                self.award_xp(int(gold * rules.GOLD_XP), lines)
            for iid in ch.get('items', []):
                who = self.give_party(iid)
                if who:
                    lines.append('%s takes the %s.' % (who.name,
                                                       self.item_name(iid)))
                else:
                    lines.append('There is a %s, but no one can carry it.'
                                 % self.item_name(iid))
            if not lines:
                lines.append('It is empty.')
            if ch.get('msg'):
                lines.insert(0, ch['msg'])
            self.sound.play('coin')
            for l in lines:
                self.say(l)
            if self.check_wipe():
                return
            self.tell('\n'.join(lines), nxt)

        def disarm():
            r = rogues[0]
            chance = 45 + r.level * 7 + bonus(r.dx) * 5
            if not ch.get('trap'):
                self.tell('%s finds no trap on the chest.' % r.name,
                          lambda: self.ev_chest(sq, nxt))
            elif self.rng.randint(1, 100) <= chance:
                self.set_flag(key + 'safe')
                self.sound.play('menu')
                self.tell('%s finds a trap and disarms it.' % r.name,
                          lambda: self.ev_chest(sq, nxt))
            elif self.rng.randint(1, 100) <= 50:
                self.tell('%s fumbles, and the trap goes off!' % r.name,
                          lambda: (self.set_flag(key + 'safe'),
                                   self.spring_chest_trap(ch['trap']),
                                   self.ev_chest(sq, nxt)))
            else:
                self.tell("%s can't make sense of the mechanism." % r.name,
                          lambda: self.ev_chest(sq, nxt))

        opts = [('Open it', 'open')]
        if rogues:
            opts.append(('%s checks it for traps' % rogues[0].name, 'disarm'))
        opts.append(('Leave it', 'leave'))

        def pick(v):
            if v == 'open':
                open_it()
            elif v == 'disarm':
                disarm()
            else:
                nxt()
        self.ask('A Chest', opts, pick, ch.get('look', 'There is a chest here.'),
                 on_cancel=nxt)

    def spring_chest_trap(self, kind):
        self.sound.play('trap')
        if kind == 'poison':
            self.say('A cloud of green gas bursts from the chest!', INK_HI)
            for i, c in enumerate(self.party):
                if c.alive and not rules.save(c, 'poison', self.rng):
                    c.status = 'poisoned'
                    self.hurt_flash(i)
                    self.say(w('is_poisoned', c.name), INK_HI)
        else:
            self.say('The chest explodes!', INK_HI)
            for i, c in enumerate(self.party):
                if c.alive:
                    dmg = roll('2d6', self.rng)
                    c.hp -= dmg
                    self.hurt_flash(i)
                    if c.hp <= 0:
                        c.hp = 0
                        c.status = 'dead'
                        self.say('%s is killed!' % c.name, INK_HI)

    def ev_fountain(self, sq, nxt):
        kind = sq['fountain']

        def drink():
            lines = []
            if kind in ('heal', 'mana', 'cure'):
                self.sound.play('heal')
            for i, c in enumerate(self.party):
                if not c.alive:
                    continue
                if kind == 'heal':
                    c.hp = c.maxhp
                elif kind == 'mana':
                    c.sp = c.maxsp
                elif kind == 'cure':
                    if c.status in ('poisoned', 'paralyzed', 'asleep'):
                        c.status = 'ok'
                elif kind == 'poison':
                    c.status = 'poisoned'
                    self.hurt_flash(i)
            text = sq.get('drink', {
                'heal': 'The water is cool and sweet. Your wounds close.',
                'mana': 'The water tingles. Your minds are clear and full '
                        'of power.',
                'cure': 'The water burns, then soothes. You feel clean.',
                'poison': 'The water is foul! Your stomachs knot.'}[kind])
            self.say(text)
            self.tell(text, nxt)
        self.yesno(sq.get('look', 'A fountain bubbles here. Drink from it?'),
                   drink, nxt)

    def locked_door(self, x, y, sq, d):
        key = sq.get('key', '')
        if key and self.has_item(key):
            self.set_flag(self.sqkey(x, y, ':open'))
            self.say('You unlock the door with the %s.' % self.item_name(key))
            self.sound.play('door')
            self.pass_through(x, y, d)
            return
        if key:
            self.sound.play('bump')
            self.tell(sq.get('locked_msg', 'The door is locked. It needs '
                                           'a %s.' % self.item_name(key)))
            return
        rogues = [c for c in self.able() if rules.skilled(c, 'locks')]
        strong = max(self.able(), key=lambda c: c.st, default=None)
        opts = []
        if rogues:
            opts.append(('%s picks the lock' % rogues[0].name, 'pick'))
        if strong:
            opts.append(('%s forces it' % strong.name, 'force'))
        opts.append(('Leave it', 'leave'))

        def pick(v):
            if v == 'pick':
                r = rogues[0]
                if self.rng.randint(1, 100) <= 40 + r.level * 8 + bonus(r.dx) * 5:
                    self.set_flag(self.sqkey(x, y, ':open'))
                    self.say('%s picks the lock.' % r.name)
                    self.pass_through(x, y, d)
                else:
                    self.say("%s can't pick the lock." % r.name)
                    self.sound.play('bump')
            elif v == 'force':
                c = strong
                if self.rng.randint(1, 100) <= (c.st - 7) * 6:
                    self.set_flag(self.sqkey(x, y, ':open'))
                    self.say('%s breaks the door open!' % c.name)
                    self.pass_through(x, y, d)
                else:
                    dmg = self.rng.randint(1, 3)
                    c.hp = max(1, c.hp - dmg)
                    self.hurt_flash(self.party.index(c))
                    self.say('%s bruises a shoulder on the door.' % c.name)
                    self.sound.play('bump')
        self.ask('A Locked Door', opts, pick, 'The door is locked.',
                 on_cancel=lambda: None)

    def riddle(self, x, y, sq, d):
        r = sq['riddle']
        flag = r.get('flag') or self.sqkey(x, y, ':open')
        if self.flag(flag):
            self.pass_through(x, y, d)
            return

        def answer(text):
            a = ''.join(ch for ch in text.lower() if ch.isalnum())
            if a in [''.join(ch for ch in s.lower() if ch.isalnum())
                     for s in r['a']]:
                self.set_flag(flag)
                self.sound.play('magic')
                self.tell(r.get('right', 'The door swings open.'))
            else:
                self.sound.play('bump')
                self.tell(r.get('wrong', 'Nothing happens.'))

        self.push(TextInput(r.get('title', 'A Voice Speaks'), r['q'], answer,
                            maxlen=20, on_cancel=lambda: None))

    def search(self):
        """Look for hidden doors around the party."""
        L = self.level
        best = max((c.lk + (c.level * 2 if rules.skilled(c, 'search') else 0)
                    for c in self.able()), default=0)
        found = False
        for rel in (0, 1, 3):
            x, y = self.ahead(1, rel)
            sq = L.sq(x, y)
            if sq.get('secret') and not self.flag(self.sqkey(x, y, ':found')):
                if self.rng.randint(1, 30) <= best + 6:
                    self.set_flag(self.sqkey(x, y, ':found'))
                    found = True
        if found:
            self.sound.play('magic')
            self.say('You find a hidden door!', INK_HI)
        else:
            self.say('You search the walls and find nothing.')
        self.after_step()

    # ---------------------------------------------------------- magic

    def antimagic(self):
        return self.level.sq(self.st.x, self.st.y).get('antimagic')

    def cast_menu(self):
        casters = [(i, c) for i, c in enumerate(self.party)
                   if c.able and c.spells()]
        if not casters:
            self.say(w('none_cast'))
            return

        def pick_caster(i):
            c = self.party[i]
            opts = []
            for sid in c.spells():
                sp = SPELLS[sid]
                usable = sp['effect'] in ('heal', 'cure', 'light', 'locate',
                                          'phase', 'recall', 'sight', 'raise')
                opts.append(('%s\t%d %s' % (sp['name'], sp['sp'], w('sp')),
                             sid, usable and c.sp >= sp['sp']))
            self.ask('%s %s' % (c.name, w('casts')), opts,
                     lambda sid: self.pick_target(i, sid),
                     '%d of %d %s.' % (c.sp, c.maxsp, w('points')),
                     on_cancel=lambda: None, roster_sel=i)

        if len(casters) == 1:
            pick_caster(casters[0][0])
        else:
            self.ask(w('who_casts'), [('%s (%d %s)' % (c.name, c.sp, w('sp')),
                                       i) for i, c in casters],
                     pick_caster, on_cancel=lambda: None)

    def pick_target(self, ci, sid):
        sp = SPELLS[sid]
        if sp['target'] == 'ally':
            self.ask(sp['name'] + ' on whom?',
                     [(c.name, j, True) for j, c in enumerate(self.party)],
                     lambda j: self.cast_out(ci, sid, j),
                     on_cancel=lambda: None)
        else:
            self.cast_out(ci, sid, None)

    def cast_out(self, ci, sid, target, free=False, power=None):
        """Cast a spell outside a fight."""
        c = self.party[ci]
        sp = SPELLS[sid]
        if not free:
            if c.sp < sp['sp']:
                self.say(w('too_few', c.name))
                return
            c.sp -= sp['sp']
        lvl = power or c.level
        if self.antimagic():
            self.say(w('fizzle'), INK_HI)
            self.sound.play('bump')
            return
        e = sp['effect']
        self.sound.play('heal' if e in ('heal', 'cure', 'raise') else 'spell')
        from .combat import spell_colour
        self.flash(spell_colour(sp), 0.35)
        st = self.st
        if e == 'heal':
            whom = [self.party[target]] if target is not None else self.party
            for t in whom:
                if t.alive:
                    n = roll(sp['dice'], self.rng) + lvl * sp.get('per', 0)
                    t.hp = min(t.maxhp, t.hp + n)
            self.say('%s %s %s.' % (c.name, w('casts'), sp['name']))
        elif e == 'cure':
            t = self.party[target]
            if t.status in ('poisoned', 'paralyzed', 'asleep'):
                t.status = 'ok'
                self.say(w('is_cured', t.name))
            else:
                self.say('%s needed no cure.' % t.name)
        elif e == 'raise':
            t = self.party[target]
            if t.status == 'dead':
                t.status = 'ok'
                t.hp = 1
                self.say('%s draws breath again!' % t.name, INK_HI)
            else:
                self.say('%s is not dead.' % t.name)
        elif e == 'light':
            st.light_r = sp['light']
            st.light_turns = sp['turns'] + lvl * 20
            self.say('Light blooms around the party.')
        elif e == 'sight':
            st.sight = sp['turns'] + lvl * 10
            self.say('Your eyes see through deceit and stone.')
        elif e == 'locate':
            self.locate()
        elif e == 'phase':
            self.phase()
        elif e == 'recall':
            if self.level.outdoor:
                self.say('You are already in the open air.')
            else:
                lid, x, y, f = self.d.START
                self.say('The world spins away...')
                self.change_level(lid, x, y, f)
        self.mark_seen()

    def locate(self):
        st = self.st
        L = self.level
        seen = st.seen.setdefault(st.level, set())
        for y in range(st.y - 4, st.y + 5):
            for x in range(st.x - 4, st.x + 5):
                if 0 <= x < L.w and 0 <= y < L.h:
                    seen.add(y * L.w + x)
        depth = L.depth
        where = ('%d below the town' % depth) if depth else 'above ground'
        self.tell('You are in %s, %s.\n\nYou stand %d squares east and %d '
                  'squares north of the south-west corner, facing %s.\n\n'
                  'The halls around you are now on your map.'
                  % (L.name, where, st.x, L.h - 1 - st.y,
                     DIR_NAMES[st.facing]), title='Seeker')

    def phase(self):
        L = self.level
        x, y = self.ahead(1)
        bx, by = self.ahead(2)
        sq = L.sq(x, y)
        if not sq.get('solid'):
            self.say('There is no wall in front of you.')
            return
        if L.spec.get('nophase') or not (0 < x < L.w - 1 and 0 < y < L.h - 1) \
                or L.sq(bx, by).get('solid') or sq.get('shop') or \
                sq.get('riddle'):
            self.say('The wall resists your magic.')
            return
        self.say('You step through the solid stone.')
        self.move_to(bx, by, quiet=True)

    # ------------------------------------------------------------ items

    def use_item(self, ci, pi, then=None):
        c = self.party[ci]
        iid = c.pack[pi]
        it = ITEMS[iid]
        use = it.get('use')
        if not c.able:
            self.say('%s cannot do that now.' % c.name)
            return
        if use == 'heal':
            c.pack.pop(pi)
            n = roll(it.get('amount', '2d8'), self.rng)
            c.hp = min(c.maxhp, c.hp + n)
            self.sound.play('heal')
            self.say('%s %s the %s.' % (c.name, it.get('verb', 'uses'),
                                        it['name']))
        elif use == 'cure':
            c.pack.pop(pi)
            if c.status in ('poisoned', 'paralyzed'):
                c.status = 'ok'
            self.sound.play('heal')
            self.say('%s %s the %s.' % (c.name, it.get('verb', 'uses'),
                                        it['name']))
        elif use == 'light':
            if self.level.outdoor:
                self.say(w('too_bright'))
                return
            c.pack.pop(pi)
            self.st.light_r = it.get('light', 3.0)
            self.st.light_turns = it.get('turns', 120)
            self.say('%s %s the %s.' % (c.name, it.get('verb', 'uses'),
                                        it['name'].lower()))
            self.mark_seen()
        elif use == 'spell':
            sp = SPELLS[it['spell']]
            if sp['effect'] in ('damage', 'sleep', 'turn', 'ward', 'bless',
                                'smite'):
                self.say('That scroll is for fighting.')
                return
            c.pack.pop(pi)
            self.say('%s %s the %s.' % (c.name, it.get('verb', 'uses'),
                                        it['name']))
            self.cast_out(ci, it['spell'], ci, free=True, power=5)
        else:
            self.say("%s can't use the %s like that." % (c.name, it['name']))
            return
        if then:
            then()

    # ------------------------------------------------------------- the end

    def victory(self, pages):
        from .modes import EndMode
        self.st.won = True
        self.save()
        self.sound.play('win')
        self.push(EndMode(pages))

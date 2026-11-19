"""The game's screens: the title, walking about, the map, character
sheets, the game menu, help, defeat and victory."""

from .game import (Mode, Menu, Say, W, H, VX, VY, VW, VH, PX, PY, PW, PH,
                   TX, TY, TW, TH, RX, RY, RW, RH, INK, INK_DIM, INK_HI,
                   INK_TITLE)
from .gfx import rgb, mix
from . import font
from . import art
from .words import w
from .rules import (ITEMS, SPELLS, SLOTS, STAT_NAMES, STATS, xp_for, bonus,
                    can_use, PACK)
from .world import DIRS

HELP = """Walk: arrow keys or W A S D (Q and E step sideways).
Enter or Space: deal with what's in front of you (doors, shops) or here.
C: %s.   1-6: a character's sheet (items, equipment).
M: the map.   F: search for hidden doors.
Esc: the game menu (save, sound, quit).   ?: this help.

Mouse: click the left or right of the view to turn, the middle to walk; \
click a character to see their sheet; click choices on the scroll.

In a fight, give each character an order, then watch the round play out. \
Only the first three can fight hand to hand."""


def scene_with(picture, dim=0.45, y_off=0):
    """A view function: the dimmed corridor with a picture over it."""
    def draw(g, s):
        g.draw_scene(s, dim=dim)
        img = art.get(picture)
        s.set_clip(VX, VY, VW, VH)
        s.blit(img, VX + VW // 2 - img.w // 2, VY + VH - img.h - 2 + y_off)
        s.set_clip()
    return draw


def picture_view(picture, backdrop='#000000', texture=None, dim=0.5):
    """A view function: a picture in front of a tiled texture."""
    def draw(g, s):
        if texture:
            from . import textures
            px = textures.get(texture)
            T = textures.T
            row = []
            data = bytearray()
            for y in range(VH):
                ty = (y // 2) % T
                for x in range(VW):
                    data += bytes(px[ty * T + (x // 2) % T])
            s.put(VX, VY, VW, VH, bytes(data))
            s.darken(VX, VY, VW, VH, dim)
            # the counter
            s.rect(VX, VY + VH - 40, VW, 40, rgb('#4a2c14'))
            s.rect(VX, VY + VH - 40, VW, 3, rgb('#8a5a2c'))
            s.rect(VX, VY + VH - 37, VW, 1, rgb('#20120a'))
        else:
            s.rect(VX, VY, VW, VH, rgb(backdrop))
        img = art.get(picture)
        s.set_clip(VX, VY, VW, VH)
        s.blit(img, VX + VW // 2 - img.w // 2, VY + VH - img.h)
        s.set_clip()
    return draw


# ------------------------------------------------------------------ title

class TitleMode(Mode):
    place = ''

    def __init__(self):
        self.sel = 0
        self.rects = []

    def options(self, g):
        opts = []
        if g.has_save():
            opts.append(('Continue the adventure', 'load'))
        opts.append(('Begin a new adventure', 'new'))
        opts.append(('Quit', 'quit'))
        return opts

    def draw(self, g, s):
        s.rect(VX, VY, VW, VH, rgb('#050408'))
        img = art.get(getattr(g.d, 'TITLE_ART', 'ashenking'))
        s.set_clip(VX, VY, VW, VH)
        s.blit(img, VX + VW // 2 - img.w // 2, VY + VH - img.h)
        s.set_clip()
        y = TY + 4
        for line in font.wrap(g.title, TW // 2, 2):
            s.text(TX + TW // 2, y, line, rgb('#7a1a08'), rgb('#c8a060'), 2,
                   align='center')
            y += 22
        sub = getattr(g.d, 'SUBTITLE', '')
        for line in font.wrap(sub, TW):
            s.text(TX + TW // 2, y, line, INK, align='center')
            y += font.LINE
        y += 10
        opts = self.options(g)
        self.sel = min(self.sel, len(opts) - 1)
        self.rects = []
        for i, (label, v) in enumerate(opts):
            col = INK_HI if i == self.sel else INK
            if i == self.sel:
                s.rect(TX - 4, y - 1, TW + 8, font.LINE, rgb('#e8cc90'))
            s.text(TX + TW // 2, y, label, col, align='center')
            self.rects.append((y - 1, y + font.LINE - 1, v))
            y += font.LINE + 3
        s.text(TX + TW // 2, TY + TH - 10, 'A blobber made with the Blobber '
               'engine', INK_DIM, align='center')

    def key(self, g, k):
        opts = self.options(g)
        if k in ('up', 'w'):
            self.sel = (self.sel - 1) % len(opts)
        elif k in ('down', 's'):
            self.sel = (self.sel + 1) % len(opts)
        elif k in ('enter', 'space'):
            self.do(g, opts[self.sel][1])
        elif k == 'n':
            self.do(g, 'new')
        elif k == 'c' and g.has_save():
            self.do(g, 'load')
        elif k in ('q', 'esc'):
            g.quit = True

    def click(self, g, x, y):
        for (y0, y1, v) in self.rects:
            if y0 <= y < y1 and PX <= x < PX + PW:
                self.do(g, v)

    def do(self, g, v):
        if v == 'quit':
            g.quit = True
        elif v == 'load':
            if not g.load():
                g.tell('That saved game could not be read.')
        elif v == 'new':
            def start():
                g.new_game()
                pages = list(getattr(g.d, 'INTRO', []))

                def show(i):
                    if i < len(pages):
                        g.tell(pages[i], lambda: show(i + 1),
                               title=g.title if i == 0 else '')
                    else:
                        g.say(getattr(g.d, 'WELCOME', 'Your adventure '
                                      'begins.'))
                        g.say('Press ? for help.', INK_DIM)
                show(0)
            if g.has_save():
                g.yesno('Begin again? Your saved game will be replaced.',
                        start)
            else:
                start()


# ---------------------------------------------------------------- exploring

class ExploreMode(Mode):
    def draw(self, g, s):
        g.draw_scene(s)
        g.draw_log(s)

    def key(self, g, k):
        if k in ('up', 'w'):
            g.walk(0)
        elif k in ('down', 's'):
            g.walk(2)
        elif k in ('left', 'a'):
            g.turn(-1)
        elif k in ('right', 'd'):
            g.turn(1)
        elif k == 'q':
            g.walk(3)
        elif k == 'e':
            g.walk(1)
        elif k in ('enter', 'space'):
            self.interact(g)
        elif k == 'c':
            g.cast_menu()
        elif k == 'm':
            g.push(MapMode())
        elif k == 'f':
            g.search()
        elif k in '123456' and len(k) == 1:
            i = int(k) - 1
            if i < len(g.party):
                g.push(SheetMode(i))
        elif k == '?' or k == 'h' or k == 'f1':
            g.tell(HELP % w('help_cast'), title='Help', more='')
        elif k == 'esc':
            game_menu(g)

    def interact(self, g):
        x, y = g.ahead(1)
        sq = g.level.sq(x, y)
        if sq.get('solid') and (sq.get('shop') or sq.get('door') or
                                sq.get('goto') or sq.get('riddle') or
                                sq.get('hook') or sq.get('msg_bump')):
            g.bump(x, y, sq, g.st.facing)
            return
        here = g.active(g.level.sq(g.st.x, g.st.y))
        if any(here.get(k) for k in ('chest', 'fountain', 'goto', 'msg')):
            if here.get('msg'):
                g.tell(here['msg'], title=here.get('title', ''))
            elif here.get('chest') and not g.flag(g.sqkey(what=':chest')):
                g.ev_chest(here, lambda: None)
            elif here.get('fountain'):
                g.ev_fountain(here, lambda: None)
            elif here.get('goto'):
                g.ask_goto(here)
            else:
                g.say('There is nothing more to do here.')
        else:
            g.say('You see nothing special.')

    def click(self, g, x, y):
        if VX <= x < VX + VW and VY <= y < VY + VH:
            third = (x - VX) * 3 // VW
            if third == 0:
                g.turn(-1)
            elif third == 2:
                g.turn(1)
            elif y > VY + VH * 3 // 4:
                g.walk(2)
            else:
                g.walk(0)
        elif RX <= x < RX + RW and RY + 19 <= y < RY + RH:
            i = (y - RY - 19) // 15
            if 0 <= i < len(g.party):
                g.push(SheetMode(i))


def game_menu(g):
    def pick(v):
        if v == 'save':
            g.save(quiet=False)
        elif v == 'sound':
            g.sound.on = not g.sound.on
            g.say('Sound is %s.' % ('on' if g.sound.on else 'off'))
        elif v == 'music':
            g.sound.music_on = not g.sound.music_on
            g.say('Music is %s.' % ('on' if g.sound.music_on else 'off'))
        elif v == 'speed':
            g.speed = {1.0: 0.5, 0.5: 2.0, 2.0: 1.0}[g.speed]
            g.say('Fights now play %s.' % {0.5: 'fast', 1.0: 'at normal '
                                           'speed', 2.0: 'slowly'}[g.speed])
        elif v == 'help':
            g.tell(HELP % w('help_cast'), title='Help', more='')
        elif v == 'title':
            g.save()
            g.replace_all(TitleMode())
        elif v == 'quit':
            g.save()
            g.quit = True
    g.ask('The Game', [
        ('Back to the game', 'back'),
        ('Save', 'save'),
        ('Sound: %s' % ('on' if g.sound.on else 'off'), 'sound',
         g.sound.available),
        ('Music: %s' % ('on' if getattr(g.sound, 'music_on', False)
                        else 'off'), 'music',
         g.sound.available and g.sound.on),
        ('Fight speed: %s' % {0.5: 'fast', 1.0: 'normal', 2.0: 'slow'}[g.speed],
         'speed'),
        ('Help', 'help'),
        ('Save and go to the title', 'title'),
        ('Save and quit', 'quit')], pick, on_cancel=lambda: None)


# ------------------------------------------------------------------- map

class MapMode(Mode):
    def draw(self, g, s):
        st = g.st
        L = g.level
        s.rect(VX, VY, VW, VH, rgb('#0c0a08'))
        seen = st.seen.get(st.level, set())
        cs = max(4, min((VW - 8) // L.w, (VH - 8) // L.h))
        ox = VX + (VW - cs * L.w) // 2
        oy = VY + (VH - cs * L.h) // 2
        floor_c = rgb('#5a4a34') if not L.outdoor else rgb('#6a6a5a')
        wall_c = rgb('#d8c8a0')
        for y in range(L.h):
            for x in range(L.w):
                i = y * L.w + x
                if i not in seen:
                    continue
                sq = L.sq(x, y)
                X, Y = ox + x * cs, oy + y * cs
                if sq.get('solid') and not (sq.get('door') or sq.get('riddle')
                                            or (sq.get('secret') and
                                                g.flag(g.sqkey(x, y, ':found')))
                                            or sq.get('shop') or sq.get('goto')):
                    continue
                if sq.get('dark'):
                    s.rect(X, Y, cs, cs, rgb('#1a1010'))
                else:
                    s.rect(X, Y, cs, cs, floor_c)
                # walls drawn as lines on the edges that face solid squares
                for d, (dx, dy) in enumerate(DIRS):
                    n = L.sq(x + dx, y + dy)
                    if n.get('solid') and not (n.get('door') or n.get('riddle')
                                               or n.get('shop') or n.get('goto')
                                               or (n.get('secret') and
                                                   g.flag(g.sqkey(x + dx, y + dy,
                                                                  ':found')))):
                        if d == 0:
                            s.rect(X, Y, cs, 1, wall_c)
                        elif d == 1:
                            s.rect(X + cs - 1, Y, 1, cs, wall_c)
                        elif d == 2:
                            s.rect(X, Y + cs - 1, cs, 1, wall_c)
                        else:
                            s.rect(X, Y, 1, cs, wall_c)
                mark = None
                if sq.get('door') or sq.get('riddle') or sq.get('secret'):
                    mark = ('+', rgb('#e0a040'))
                elif sq.get('shop'):
                    mark = ('$', rgb('#ffd860'))
                elif sq.get('goto'):
                    mark = ('>' if sq.get('stairs') != 'up' else '<',
                            rgb('#80c0ff'))
                elif sq.get('chest') and not g.flag(g.sqkey(x, y, ':chest')):
                    mark = ('c', rgb('#ffd860'))
                elif sq.get('fountain'):
                    mark = ('f', rgb('#60a0ff'))
                elif sq.get('msg'):
                    mark = ('.', rgb('#ffffff'))
                if mark and cs >= 8:
                    s.text(X + cs // 2, Y + (cs - 9) // 2 + 1, mark[0],
                           mark[1], align='center')
                elif mark:
                    s.rect(X + cs // 2 - 1, Y + cs // 2 - 1, 2, 2, mark[1])
        # the party
        X, Y = ox + st.x * cs, oy + st.y * cs
        arrow = [font.UP, font.RIGHT, font.DOWN, font.LEFT][st.facing]
        s.rect(X + 1, Y + 1, cs - 2, cs - 2, rgb('#801010'))
        if cs >= 8:
            s.text(X + cs // 2, Y + (cs - 9) // 2 + 1, arrow,
                   rgb('#ffffff'), align='center')
        lines = [('The Map', INK_TITLE), ('', None),
                 (L.name, INK), ('', None),
                 ('You are facing %s.' % ['north', 'east', 'south',
                                          'west'][st.facing], INK), ('', None),
                 ('+ door    $ shop', INK_DIM), ('< > stairs   c chest', INK_DIM),
                 ('f fountain   . writing', INK_DIM), ('', None),
                 ('Press any key.', INK_DIM)]
        y = TY
        for t, c in lines:
            if t:
                s.text(TX, y, t, c)
            y += font.LINE

    def key(self, g, k):
        g.pop(self)

    def click(self, g, x, y):
        g.pop(self)


# ----------------------------------------------------------- character sheet

class SheetMode(Mode):
    """A character's sheet over the view and the scroll."""
    full = True

    def __init__(self, i):
        self.i = i
        self.sel = 0
        self.rows = []

    @property
    def roster_sel(self):
        return self.i

    def entries(self, c):
        out = [('equip', s) for s in SLOTS]
        out += [('pack', j) for j in range(len(c.pack))]
        return out

    def draw(self, g, s):
        c = g.party[self.i]
        x0, y0, ww, hh = 8, 8, 624, 266
        s.rect(x0, y0, ww, hh, rgb('#1e1a16'))
        s.bevel(x0, y0, ww, hh, rgb('#8a7a5a'), rgb('#0a0806'), 2)
        s.frame(x0 + 4, y0 + 4, ww - 8, hh - 8, rgb('#4a3e2a'))
        gold = rgb('#ffd860')
        txt = rgb('#e8dcc0')
        dim = rgb('#9a8e78')
        x = x0 + 14
        y = y0 + 12
        s.text(x, y, c.name, gold, scale=2)
        y += 22
        s.text(x, y, 'Level %d %s %s' % (c.level, c.race, c.cls), txt)
        y += font.LINE
        nxt = xp_for(c.level + 1)
        s.text(x, y, 'Experience %d (next level %d)' % (c.xp, nxt), dim)
        y += font.LINE + 6
        for k in STATS:
            v = getattr(c, k)
            s.text(x, y, STAT_NAMES[k], txt)
            s.text(x + 110, y, str(v), gold, align='right')
            b = bonus(v)
            if b:
                s.text(x + 118, y, '%+d' % b, dim)
            y += font.LINE
        y += 6
        weapon = c.item('weapon') or {}
        hit = c.to_hit() + (bonus(c.dx) - bonus(c.st)
                            if weapon.get('range') else 0)
        info = [('Hit points', '%d/%d' % (c.hp, c.maxhp)),
                (w('Points'), '%d/%d' % (c.sp, c.maxsp)),
                (w('armour_class'), str(c.ac())),
                ('To hit', '%+d' % hit),
                ('Damage', c.damage_dice() + ('%+d' % bonus(c.st)
                                              if bonus(c.st) and not
                                              weapon.get('range') else '')),
                ('Attacks', str(c.attacks())),
                ('Condition', c.status.capitalize())]
        if weapon.get('ammo'):
            info.insert(5, (weapon['ammo'].capitalize(),
                            str(g.st.supplies.get(weapon['ammo'], 0))))
        for a, b in info:
            s.text(x, y, a, txt)
            s.text(x + 150, y, b, gold, align='right')
            y += font.LINE
        # spells
        sx = x0 + 186
        y = y0 + 34
        spells = c.spells()
        if spells:
            s.text(sx, y, w('Magic'), gold)
            y += font.LINE + 2
            for sid in spells:
                sp = SPELLS[sid]
                s.text(sx, y, '%s' % sp['name'], txt)
                s.text(sx + 120, y, '%d' % sp['sp'], dim, align='right')
                y += font.LINE
        # equipment and pack
        ex = x0 + 340
        y = y0 + 12
        s.text(ex, y, 'Equipment', gold)
        y += font.LINE + 2
        ents = self.entries(c)
        self.sel = min(self.sel, len(ents) - 1)
        self.rows = []
        for n, (kind, v) in enumerate(ents):
            if kind == 'pack' and v == 0:
                y += 6
                s.text(ex, y, 'Pack (%d/%d)' % (len(c.pack), PACK), gold)
                y += font.LINE + 2
            if n == self.sel:
                s.rect(ex - 4, y - 1, 270, font.LINE, rgb('#4a3c26'))
            if kind == 'equip':
                iid = c.equip.get(v)
                s.text(ex, y, w('Armour') if v == 'armor' else v.capitalize(),
                       dim)
                s.text(ex + 56, y, ITEMS[iid]['name'] if iid else '-',
                       txt if iid else dim)
            else:
                iid = c.pack[v]
                it = ITEMS[iid]
                ok = can_use(c.cls, it) or it['kind'] not in (
                    'weapon', 'armor', 'shield', 'helm', 'gloves', 'ring')
                s.text(ex, y, it['name'], txt if ok else rgb('#c07060'))
            self.rows.append((n, y))
            y += font.LINE
        if not c.pack:
            y += 6
            s.text(ex, y, 'Pack (empty)', gold)
        # what the selected thing is
        kind, v = ents[self.sel]
        iid = c.equip.get(v) if kind == 'equip' else c.pack[v]
        y = y0 + hh - 38
        if iid:
            it = ITEMS[iid]
            desc = describe(it)
            if not can_use(c.cls, it) and it['kind'] in (
                    'weapon', 'armor', 'shield', 'helm', 'gloves', 'ring'):
                desc += '  (%s cannot use this)' % c.cls
            s.text(ex - 4, y - 14, desc[:52], dim)
        s.text(x0 + 14, y0 + hh - 18,
               'Enter: equip/use/remove   T: trade   D: drop   '
               '<- ->: next character   Esc: back', dim)

    def key(self, g, k):
        c = g.party[self.i]
        ents = self.entries(c)
        self.sel = max(0, min(self.sel, len(ents) - 1))
        if k == 'esc':
            g.pop(self)
            return
        if k in ('up', 'w'):
            self.sel = (self.sel - 1) % len(ents)
        elif k in ('down', 's'):
            self.sel = (self.sel + 1) % len(ents)
        elif k in ('left', 'a'):
            self.i = (self.i - 1) % len(g.party)
            self.sel = 0
        elif k in ('right', 'd'):
            self.i = (self.i + 1) % len(g.party)
            self.sel = 0
        elif k in '123456' and len(k) == 1 and int(k) <= len(g.party):
            self.i = int(k) - 1
            self.sel = 0
        elif k in ('enter', 'space', 'e', 'u'):
            kind, v = ents[self.sel]
            if not c.alive:
                g.say('%s is in no state to do that.' % c.name)
                return
            if kind == 'equip':
                err = c.unequip(v)
                if err:
                    g.say(err)
            else:
                it = ITEMS[c.pack[v]]
                if it['kind'] in ('weapon', 'armor', 'shield', 'helm',
                                  'gloves', 'ring'):
                    err = c.equip_item(v)
                    if err:
                        g.say(err)
                    else:
                        g.sound.play('menu')
                elif it.get('use'):
                    g.use_item(self.i, v)
                else:
                    g.say('%s looks at the %s.' % (c.name, it['name']))
        elif k == 'd':
            kind, v = ents[self.sel]
            if kind == 'pack':
                iid = c.pack[v]
                if ITEMS[iid].get('kind') == 'quest':
                    g.say("You'd better keep that.")
                    return
                g.yesno('Drop the %s? It will be gone for good.'
                        % ITEMS[iid]['name'],
                        lambda: (c.pack.remove(iid),
                                 g.say('%s drops the %s.' % (c.name,
                                                            ITEMS[iid]['name']))))
        elif k == 't':
            kind, v = ents[self.sel]
            if kind != 'pack':
                g.say('Take it off first.')
                return
            iid = c.pack[v]

            def give(j):
                o = g.party[j]
                if o.give(iid):
                    c.pack.remove(iid)
                    g.say('%s gives the %s to %s.' % (c.name,
                                                      ITEMS[iid]['name'],
                                                      o.name))
                else:
                    g.say("%s's pack is full." % o.name)
            g.ask('Give the %s to?' % ITEMS[iid]['name'],
                  [(o.name, j, j != self.i) for j, o in enumerate(g.party)],
                  give, on_cancel=lambda: None)

    def click(self, g, x, y):
        if RY <= y < RY + RH:
            i = (y - RY - 19) // 15
            if 0 <= i < len(g.party):
                self.i = i
            return
        for (n, ry) in self.rows:
            if ry - 1 <= y < ry + font.LINE - 1 and x > 340:
                if self.sel == n:
                    self.key(g, 'enter')
                self.sel = n
                return
        if y > 240:
            g.pop(self)


def describe(it):
    k = it['kind']
    if k == 'weapon':
        d = 'Weapon, %s damage' % it['dmg']
        if it.get('hit'):
            d += ', %+d to hit' % it['hit']
        if it.get('range'):
            d += ", range %d'" % it['range']
    elif k in ('armor', 'shield', 'helm', 'gloves', 'ring'):
        d = '%s, armour %+d' % ({'armor': 'Armour', 'shield': 'Shield',
                                 'helm': 'Helm', 'gloves': 'Gloves',
                                 'ring': 'Ring'}[k], it.get('ac', 0))
    elif it.get('use') == 'heal':
        d = 'Restores hit points (Enter)'
    elif it.get('use') == 'cure':
        d = 'Cures poison and paralysis (Enter)'
    elif it.get('use') == 'spell':
        d = '%s (Enter)' % SPELLS[it['spell']]['name']
    elif it.get('use') == 'light':
        d = 'Light in the dark (Enter)'
    elif k == 'ammo':
        d = 'Ammunition'
    elif k == 'key':
        d = 'A key. It opens something.'
    else:
        d = it.get('text', 'Something important.')
    if it.get('text') and k != 'quest':
        d = it['text']
    if it.get('price'):
        d += '  Worth %d %s' % (it['price'] // 2, w('money'))
    return d


# ------------------------------------------------------------- the end

class GameOverMode(Mode):
    place = 'Your party has fallen'

    def draw(self, g, s):
        g.draw_scene(s, dim=0.3)
        img = art.get('bones')
        big = img.scaled(img.w * 2, img.h * 2)
        s.blit(big, VX + VW // 2 - big.w // 2, VY + VH - big.h - 20)
        y = TY
        s.text(TX + TW // 2, y, 'Alas!', INK_HI, scale=2, align='center')
        y += 26
        for line in font.wrap(getattr(g.d, 'DEATH', 'Your party has '
                                      'perished in the dark. Their bones '
                                      'will join the others.'), TW):
            s.text(TX, y, line, INK)
            y += font.LINE
        y += 10
        s.text(TX + TW // 2, y, 'Press a key.', INK_DIM, align='center')

    def key(self, g, k):
        g.replace_all(TitleMode())


class EndMode(Mode):
    place = ''

    def __init__(self, pages):
        self.pages = pages
        self.i = 0

    def draw(self, g, s):
        page = self.pages[self.i]
        pic = page.get('art')
        if pic:
            s.rect(VX, VY, VW, VH, rgb(page.get('bg', '#000000')))
            img = art.get(pic)
            s.blit(img, VX + VW // 2 - img.w // 2, VY + VH - img.h)
        else:
            g.draw_scene(s)
        y = TY
        if page.get('title'):
            s.text(TX + TW // 2, y, page['title'], INK_TITLE, align='center')
            y += font.LINE + 6
        for line in font.wrap(page['text'], TW):
            s.text(TX, y, line, INK)
            y += font.LINE
        s.text(TX + TW // 2, TY + TH - 10, '(press a key)', INK_DIM,
               align='center')

    def key(self, g, k):
        self.i += 1
        if self.i >= len(self.pages):
            g.pop(self)

    def click(self, g, x, y):
        self.key(g, 'enter')

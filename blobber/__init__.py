"""Blobber: an engine for first-person, party-based dungeon crawlers in the
style of the 1980s ("blobbers"), in pure Python with Tk.

A game is a module that defines its levels, party, story and so on (see
the sample game, ashencrypt) and calls blobber.run(module).
"""

import os
import random
import sys

__version__ = '0.1'


def home_dir():
    """Where saves and the sound cache go: your home folder, or, if that
    can't be written to (as in an Android app), the app's own folder."""
    import tempfile
    home = os.path.expanduser('~')
    if home != '~' and os.access(home, os.W_OK):
        return home
    for d in (os.environ.get('ANDROID_PRIVATE'), os.getcwd(),
              tempfile.gettempdir()):
        if d and os.access(d, os.W_OK):
            return d
    return home


def run(gdef, argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--build-app' in argv:
        from .build import build_app
        i = argv.index('--build-app')
        dest = argv[i + 1] if i + 1 < len(argv) and \
            not argv[i + 1].startswith('--') else \
            os.path.dirname(os.path.realpath(gdef.__file__))
        print(build_app(gdef, os.path.expanduser(dest)))
        return
    if '--build-android' in argv:
        from .build import build_android
        i = argv.index('--build-android')
        if i + 1 >= len(argv):
            sys.exit('--build-android needs a folder to write the project '
                     'to')
        dest = build_android(gdef, os.path.expanduser(argv[i + 1]))
        print('%s: build the app with %s/build.sh (Docker), or buildozer '
              'android debug' % (dest, dest))
        return
    if '--icon-png' in argv:
        from .build import icon_png
        i = argv.index('--icon-png')
        size = int(argv[i + 1])
        out = argv[i + 2] if i + 2 < len(argv) else '%s-%d.png' % (gdef.ID,
                                                                   size)
        with open(out, 'wb') as fh:
            fh.write(icon_png(gdef, size))
        print(out)
        return
    if '--selftest' in argv:
        sys.exit(selftest(gdef))
    if '--balance' in argv:
        from .balance import report
        i = argv.index('--balance')
        runs = int(argv[i + 1]) if i + 1 < len(argv) and \
            argv[i + 1].isdigit() else 20
        report(gdef, runs)
        return
    if '--shot' in argv:
        i = argv.index('--shot')
        path = argv[i + 1]
        keys = []
        if '--keys' in argv:
            keys = argv[argv.index('--keys') + 1].split(',')
        shot(gdef, path, keys, seed='--seed' in argv and
             int(argv[argv.index('--seed') + 1]))
        return
    from .sound import Sound
    from .game import Game
    try:
        import tkinter                                  # noqa: F401
        have_tk = True
    except ImportError:
        have_tk = False
    use_kivy = '--kivy' in argv or os.environ.get('BLOBBER_UI') == 'kivy' \
        or not have_tk
    scale = None
    if '--scale' in argv:
        scale = float(argv[argv.index('--scale') + 1])
    snd = Sound(gdef.ID)
    if '--mute' in argv:
        snd.on = False
    if '--nomusic' in argv:
        snd.music_on = False
    snd.prepare()
    g = Game(gdef, snd)
    if snd.on and snd.music_on:
        snd.prepare_music(g.tunes, first=('title', 'town'))
    try:
        if use_kivy:
            from .kivyshell import KivyShell
            KivyShell(g).run()
        else:
            from .tkshell import TkShell
            TkShell(g, scale).run()
    finally:
        snd.music(None)
        snd.stop_music()


class _Silent:
    on = False
    available = False

    def play(self, name):
        pass


def shot(gdef, path, keys, seed=None):
    """Play a list of keys without a window and save the screen as a PNG.
    A key 'wait:N' runs N seconds of game time; 'new' starts a new game;
    'save:FILE' saves an extra picture there."""
    from .game import Game
    from .png import save_surface
    import tempfile
    sp = os.path.join(tempfile.gettempdir(), 'blobber-shot.json')
    if os.path.exists(sp) and '--keep' not in sys.argv:
        os.remove(sp)
    g = Game(gdef, _Silent(), save_path=sp)
    if seed:
        g.rng.seed(seed)
    for k in keys:
        if k.startswith('wait:'):
            t = float(k[5:])
            while t > 0:
                g.update(0.05)
                t -= 0.05
        elif k.startswith('save:'):
            save_surface(g.render(), k[5:], 2)
        elif k == 'comma':
            g.key(',')
        else:
            g.key(k)
    save_surface(g.render(), path, 2)


def selftest(gdef):
    """Check the game's maps and draw everything once.  Returns an exit
    status."""
    from .game import Game
    from .world import DIRS
    from . import art, textures
    from .rules import ITEMS, MONSTERS, SPELLS
    import tempfile
    problems = []
    g = Game(gdef, _Silent(), save_path=os.path.join(tempfile.gettempdir(),
                                                     'blobber-test.json'))
    for lid, L in g.levels.items():
        for y in range(L.h):
            for x in range(L.w):
                ch = L.char(x, y)
                if ch not in L.legend:
                    problems.append('%s: no legend for %r at %d,%d'
                                    % (lid, ch, x, y))
                    continue
                sq = L.legend[ch]
                for key in ('wall', 'floor', 'ceil'):
                    t = sq.get(key)
                    for name in (t if isinstance(t, list) else [t]):
                        if name and name != '@stairs' and \
                                name not in textures.names():
                            problems.append('%s: no texture %r' % (lid, name))
                if sq.get('sprite') and sq['sprite'] not in art.names():
                    problems.append('%s: no picture %r' % (lid, sq['sprite']))
                if sq.get('goto'):
                    tl, tx, ty, tf = sq['goto']
                    if tl not in g.levels:
                        problems.append('%s %d,%d: goto unknown level %s'
                                        % (lid, x, y, tl))
                    elif g.levels[tl].sq(tx, ty).get('solid'):
                        problems.append('%s %d,%d: goto lands in a wall'
                                        % (lid, x, y))
                for kind, n in sq.get('fight', []):
                    if kind not in MONSTERS:
                        problems.append('%s: no monster %r' % (lid, kind))
                for iid in sq.get('chest', {}).get('items', []) + \
                        ([sq['item']] if sq.get('item') else []) + \
                        sq.get('stock', []):
                    if iid not in ITEMS:
                        problems.append('%s: no item %r' % (lid, iid))
                if sq.get('talk'):
                    from .talk import check as check_talk
                    problems += ['%s: %s' % (lid, p) for p in
                                 check_talk(sq['talk'], art.names(), ITEMS)]
                if sq.get('key') and sq['key'] not in ITEMS:
                    problems.append('%s: no key item %r' % (lid, sq['key']))
        for w, groups in L.encounters:
            for kind, lo, hi in groups:
                if kind not in MONSTERS:
                    problems.append('%s: no monster %r' % (lid, kind))
        for name in [L.theme.get(k) for k in ('wall', 'door', 'locked',
                                              'floor', 'ceil', 'stairs')] + \
                [v for v, _ in L.theme.get('variants', [])]:
            if name and name not in textures.names():
                problems.append('%s theme: no texture %r' % (lid, name))
        # every open square reachable from somewhere that leads here
        start = None
        if gdef.START[0] == lid:
            start = gdef.START[1:3]
        else:
            for ol in g.levels.values():
                for row in ol.legend.values():
                    if row.get('goto') and row['goto'][0] == lid:
                        start = tuple(row['goto'][1:3])
        if start:
            seen = {start}
            todo = [start]
            while todo:
                x, y = todo.pop()
                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    sq = L.sq(nx, ny)
                    if sq.get('block'):
                        continue
                    if not sq.get('solid'):
                        if (nx, ny) not in seen:
                            seen.add((nx, ny))
                            todo.append((nx, ny))
                    elif sq.get('door') or sq.get('secret') or sq.get('riddle'):
                        bx, by = nx + dx, ny + dy
                        if not L.sq(bx, by).get('solid') and \
                                (bx, by) not in seen:
                            seen.add((bx, by))
                            todo.append((bx, by))
                for (tx, ty, tf) in [L.sq(x, y)['teleport']] \
                        if L.sq(x, y).get('teleport') else []:
                    if (tx, ty) not in seen:
                        seen.add((tx, ty))
                        todo.append((tx, ty))
            for y in range(L.h):
                for x in range(L.w):
                    sq = L.sq(x, y)
                    if not sq.get('solid') and (x, y) not in seen and \
                            L.char(x, y) != ' ' and not sq.get('block'):
                        problems.append('%s: %d,%d (%r) cannot be reached'
                                        % (lid, x, y, L.char(x, y)))
    from . import music
    for name, tune in g.tunes.items():
        try:
            music.check(tune)
        except (ValueError, KeyError, IndexError) as e:
            problems.append('tune %s: %s' % (name, e))
    for lid, L in g.levels.items():
        t = L.spec.get('music')
        if t and t not in g.tunes:
            problems.append('%s: no tune %r' % (lid, t))
    for n in art.names():
        art.get(n)
    for n in textures.names():
        textures.get(n)
    g.new_game()
    for lid, L in g.levels.items():
        g.st.level = lid
        g.render()
    # a few rounds of a fight
    from .combat import CombatMode
    g.st.level = gdef.START[0]
    kinds = [k for L in g.levels.values() for _, grp in L.encounters
             for (k, lo, hi) in grp] or list(MONSTERS)
    g.start_combat([(kinds[0], 3), (kinds[-1], 2)])
    for _ in range(200):
        g.key('enter')
        g.update(1.0)
        if not any(isinstance(m, CombatMode) for m in g.modes):
            break
    g.render()
    for p in problems:
        print(p)
    print('%s: %d levels, %d problems' % (gdef.TITLE, len(g.levels),
                                          len(problems)))
    return 1 if problems else 0

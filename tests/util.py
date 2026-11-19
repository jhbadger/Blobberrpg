"""Helpers for the tests: finding and loading the games, and playing them
without a window."""

import glob
import importlib.machinery
import importlib.util
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from blobber import _Silent                             # noqa: E402
from blobber.game import Game                           # noqa: E402
from blobber.combat import CombatMode                   # noqa: E402


def games():
    """The names of the game scripts in the repository: executable files
    that hand themselves to blobber.run()."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, '*'))):
        if os.path.isfile(path) and os.access(path, os.X_OK) and \
                '.' not in os.path.basename(path):
            with open(path, errors='replace') as fh:
                if 'blobber.run(' in fh.read():
                    out.append(os.path.basename(path))
    return out


_loaded = {}


def load(name):
    """A game script, loaded as a module (once: it changes the engine's
    rules tables, so two games mustn't be mixed in one process; the tests
    for each game run in a fresh interpreter, see run_tests.py)."""
    if name not in _loaded:
        loader = importlib.machinery.SourceFileLoader(
            name, os.path.join(ROOT, name))
        spec = importlib.util.spec_from_loader(name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        _loaded[name] = mod
    return _loaded[name]


def new_game(gd, seed=1, strong=False):
    """A game in progress, with no window and no sound, saving to a
    temporary file."""
    path = os.path.join(tempfile.mkdtemp(prefix='blobber-test-'),
                        'save.json')
    g = Game(gd, _Silent(), save_path=path)
    g.rng.seed(seed)
    g.new_game()
    g.modes = g.modes[:1]
    if strong:
        for c in g.party:
            c.level = 12
            c.maxhp = c.hp = 300
            c.maxsp = c.sp = 80
    return g


def in_combat(g):
    return any(isinstance(m, CombatMode) for m in g.modes)


def fight_out(g, limit=3000):
    """Play a fight to its end by always choosing the first option."""
    g.key('enter')                  # past the guardian's speech
    n = 0
    while in_combat(g) and n < limit:
        m = g.mode
        g.key('1' if type(m).__name__ == 'Menu' and
              m.title.startswith('Fight') else 'enter')
        n += 1
    for _ in range(5):
        g.key('enter')
    g.modes = g.modes[:1]


def fuzz(g, rng, steps):
    """Random keys and taps, as a careless player."""
    keys = (['up'] * 12 + ['left', 'right', 'down', 'q', 'e'] * 2 +
            ['enter', 'space', 'esc', '1', '2', '3', '4', '5', '6', 'c', 'm',
             'f', 'y', 'n', 'a', 'b', 't', 'd', 'backspace', '?', 'w', 's',
             'x', 'z', '0', '9', '8', '7'])
    for i in range(steps):
        if rng.random() < 0.35:
            fr = g.frame() if rng.random() < 0.2 else None
            fw, fh = (fr.w, fr.h) if fr else (640, 400)
            g.tap(rng.randrange(fw), rng.randrange(fh))
        else:
            k = rng.choice(keys)
            if k == 'esc' and rng.random() < 0.7:
                k = 'enter'
            g.key(k)
        if rng.random() < 0.3:
            g.update(0.8)
        if rng.random() < 0.02:
            g.portrait = not g.portrait
        if g.quit:
            g.quit = False
        if i % 50 == 0:
            g.frame()

"""The front ends: the Tk window (skipped where there's no Tk or no
display) and the Kivy one (skipped where Kivy isn't installed).  Each
opens a real window for a few seconds, so set BLOBBER_NO_GUI=1 to skip
them."""

import os
import subprocess
import sys
import unittest

import util

NAME = os.environ.get('BLOBBER_GAME') or util.games()[0]
NO_GUI = bool(os.environ.get('BLOBBER_NO_GUI'))

# Driving a window needs its main loop, so each check runs as a little
# script of its own.
TK = r'''
import sys
sys.path.insert(0, %(tests)r)
import util
from blobber.tkshell import TkShell
from blobber import layout
g = util.new_game(util.load(%(game)r))
sh = TkShell(g)
errors = []
sh.root.report_callback_exception = lambda *a: errors.append(a)
out = []
def wide():
    sh.draw()
    out.append(sh.fsize)
    sh.root.geometry('420x780')
    sh.root.after(400, upright)
def upright():
    sh.draw()
    out.append(sh.fsize)
    r = [r for r in g.mode.rects if r[4] == 'm'][0]
    x = (r[0] + r[2]) // 2 - 364 + layout.PAPER_AT[0]
    y = (r[1] + r[3]) // 2 - 8 + layout.PAPER_AT[1]
    a, b = sh.zoom
    sh.canvas.event_generate('<Button-1>', x=sh.ox + x * a // b,
                             y=sh.oy + y * a // b)
    sh.root.after(200, done)
def done():
    out.append(type(g.mode).__name__)
    sh.root.destroy()
sh.root.after(600, wide)
sh.run()
print(out, len(errors))
'''

KIVY = r'''
import sys
sys.path.insert(0, %(tests)r)
import util
from blobber.kivyshell import KivyShell
g = util.new_game(util.load(%(game)r))
sh = KivyShell(g, 450, 850)
out = []
class T:
    def __init__(self, x, y): self.x, self.y = x, y
def go(dt):
    sh.draw()
    out.append(sh.fsize)
    sh.key_down(None, 109, 0, 'm', [])
    out.append(type(g.mode).__name__)
    sh.root.on_touch_down(T(sh.ox + 100 * sh.scale,
                            sh.oy + (sh.fsize[1] - 100) * sh.scale))
    out.append(type(g.mode).__name__)
    sh.Clock.schedule_once(lambda dt: sh.close(), 0.2)
sh.Clock.schedule_once(go, 1.0)
sh.run()
print(out)
'''


def run(script, python=sys.executable):
    p = subprocess.run([python, '-c', script % {
        'tests': os.path.dirname(os.path.abspath(__file__)), 'game': NAME}],
        capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout.strip().splitlines()[-1:] or [''], p.stderr


def has(module, python=sys.executable):
    return subprocess.run([python, '-c', 'import ' + module],
                          capture_output=True).returncode == 0


class Shells(unittest.TestCase):
    @unittest.skipIf(NO_GUI or not has('tkinter'), 'no Tk, or GUI tests off')
    def test_tk(self):
        code, last, err = run(TK)
        self.assertEqual(code, 0, err)
        self.assertEqual(last[0], "[(640, 400), (360, 676), 'MapMode'] 0", err)

    @unittest.skipIf(NO_GUI or not has('kivy',
                                       os.environ.get('KIVY_PYTHON',
                                                      sys.executable)),
                     'no Kivy (set KIVY_PYTHON to a Python that has it)')
    def test_kivy(self):
        code, last, err = run(KIVY, os.environ.get('KIVY_PYTHON',
                                                  sys.executable))
        self.assertEqual(code, 0, err)
        self.assertEqual(last[0], "[(360, 676), 'MapMode', 'ExploreMode']",
                         err[-2000:])


if __name__ == '__main__':
    unittest.main()

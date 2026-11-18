"""Synthesized sound effects, written once as small WAV files and played
with whatever the system has (afplay on macOS, paplay or aplay on Linux,
winsound on Windows).  With none of these the game is silent."""

import math
import os
import random
import shutil
import struct
import subprocess
import sys
import wave

RATE = 22050


def _env(n, attack=0.005, release=0.08):
    a = max(1, int(attack * RATE))
    r = max(1, int(release * RATE))
    out = []
    for i in range(n):
        v = 1.0
        if i < a:
            v = i / a
        if i > n - r:
            v = min(v, (n - i) / r)
        out.append(v)
    return out


def tone(freq, dur, wave_='square', vol=0.3, slide=0.0, duty=0.5):
    n = int(dur * RATE)
    env = _env(n)
    out = []
    ph = 0.0
    for i in range(n):
        f = freq + slide * i / n
        ph += f / RATE
        p = ph % 1.0
        if wave_ == 'square':
            v = 1.0 if p < duty else -1.0
        elif wave_ == 'tri':
            v = 4 * abs(p - 0.5) - 1
        elif wave_ == 'saw':
            v = 2 * p - 1
        else:
            v = math.sin(2 * math.pi * p)
        out.append(v * vol * env[i])
    return out


def noise(dur, vol=0.3, decay=6.0, seed=1, lowpass=0.5):
    rng = random.Random(seed)
    n = int(dur * RATE)
    out = []
    last = 0.0
    for i in range(n):
        v = rng.uniform(-1, 1)
        last = last + (v - last) * lowpass
        out.append(last * vol * math.exp(-decay * i / n))
    return out


def seq(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def mixdown(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


EFFECTS = {
    'step':   lambda: noise(0.07, 0.22, 9, 1, 0.15),
    'bump':   lambda: mixdown(tone(70, 0.12, 'sine', 0.5, -30),
                              noise(0.1, 0.25, 8, 2, 0.1)),
    'door':   lambda: seq(tone(160, 0.12, 'saw', 0.12, 80),
                          noise(0.12, 0.3, 6, 3, 0.3)),
    'hit':    lambda: mixdown(noise(0.12, 0.45, 7, 4, 0.6),
                              tone(110, 0.1, 'square', 0.15, -60)),
    'miss':   lambda: noise(0.15, 0.2, 3, 5, 0.25),
    'hurt':   lambda: seq(tone(220, 0.07, 'square', 0.25, -60),
                          tone(140, 0.12, 'square', 0.25, -60)),
    'spell':  lambda: seq(*[tone(440 * 2 ** (k / 12), 0.05, 'tri', 0.25)
                            for k in (0, 4, 7, 12, 16, 19)]),
    'heal':   lambda: seq(*[tone(523 * 2 ** (k / 12), 0.07, 'sine', 0.3)
                            for k in (0, 4, 7, 12)]),
    'die':    lambda: tone(300, 0.6, 'square', 0.2, -260, 0.3),
    'coin':   lambda: seq(tone(988, 0.06, 'square', 0.18),
                          tone(1319, 0.18, 'square', 0.18)),
    'level':  lambda: seq(*[tone(392 * 2 ** (k / 12), 0.09, 'square', 0.2,
                                 duty=0.25) for k in (0, 4, 7, 12, 7, 12, 16)]),
    'fight':  lambda: mixdown(tone(110, 0.5, 'saw', 0.18),
                              tone(116.5, 0.5, 'saw', 0.18),
                              tone(165, 0.5, 'square', 0.1)),
    'stairs': lambda: seq(*[noise(0.06, 0.25, 8, k, 0.2) + [0.0] * 1500
                            for k in range(4)]),
    'win':    lambda: seq(*[tone(523 * 2 ** (k / 12), 0.12, 'square', 0.2,
                                 duty=0.25) for k in (0, 4, 7, 12, 12, 16, 19, 24)]),
    'trap':   lambda: mixdown(noise(0.4, 0.5, 4, 9, 0.4),
                              tone(90, 0.4, 'sine', 0.4, -50)),
    'menu':   lambda: tone(660, 0.03, 'square', 0.1, duty=0.25),
    'magic':  lambda: mixdown(tone(300, 0.5, 'sine', 0.2, 600),
                              tone(450, 0.5, 'tri', 0.15, 500)),
}


def write_wav(path, samples):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, s)) * 32000))
                               for s in samples))


class Sound:
    def __init__(self, game_id):
        self.on = True
        self.dir = os.path.join(os.path.expanduser('~'), '.cache', game_id)
        self.cmd = None
        self.winsound = None
        if sys.platform == 'darwin' and shutil.which('afplay'):
            self.cmd = ['afplay']
        elif sys.platform.startswith('win'):
            try:
                import winsound
                self.winsound = winsound
            except ImportError:
                pass
        else:
            for c in (['paplay'], ['aplay', '-q']):
                if shutil.which(c[0]):
                    self.cmd = c
                    break
        self.ready = set()
        self.last = {}

    @property
    def available(self):
        return bool(self.cmd or self.winsound)

    def path(self, name):
        return os.path.join(self.dir, name + '.wav')

    def prepare(self):
        if not self.available:
            return
        try:
            os.makedirs(self.dir, exist_ok=True)
            for name, fn in EFFECTS.items():
                p = self.path(name)
                if not os.path.exists(p):
                    write_wav(p, fn())
                self.ready.add(name)
        except OSError:
            self.cmd = self.winsound = None

    def play(self, name):
        if not self.on or name not in self.ready:
            return
        p = self.path(name)
        try:
            if self.winsound:
                self.winsound.PlaySound(p, self.winsound.SND_FILENAME |
                                        self.winsound.SND_ASYNC)
            elif self.cmd:
                subprocess.Popen(self.cmd + [p], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except OSError:
            pass

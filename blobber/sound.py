"""Synthesized sound effects and music, written once as WAV files and
played with whatever the system has: afplay on macOS, paplay or aplay on
Linux, Android's MediaPlayer through pyjnius or pygame's mixer (Pydroid),
or winsound on Windows (effects only).  With none of these the game is
silent.  Music is rendered in the background the first time and cached
in ~/.cache/<game>, named by a checksum so an edited tune is rendered
again."""

import json
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import threading
import time
import wave
import zlib

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


ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ROOT' in os.environ


# Players.  Each starts a WAV file and returns a handle that, like a
# subprocess, has poll() (None while it plays) and terminate().

class CommandPlayer:
    """A command-line player: afplay, paplay or aplay."""
    music = True

    def __init__(self, cmd):
        self.cmd = cmd

    def start(self, path):
        return subprocess.Popen(self.cmd + [path], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

    @classmethod
    def find(cls):
        for cmd in (['afplay'], ['paplay'], ['aplay', '-q']):
            if shutil.which(cmd[0]):
                return cls(cmd)
        return None


class MediaPlayer:
    """Android's android.media.MediaPlayer, through pyjnius (pip install
    pyjnius in Pydroid)."""
    music = True

    class Handle:
        def __init__(self, mp):
            self.mp = mp

        def poll(self):
            if self.mp is None:
                return 0
            try:
                if self.mp.isPlaying():
                    return None
            except Exception:
                pass
            self.terminate()
            return 0

        def terminate(self):
            if self.mp is not None:
                try:
                    self.mp.stop()
                except Exception:
                    pass
                self.mp.release()
                self.mp = None

    def __init__(self, cls):
        self.cls = cls

    def start(self, path):
        mp = self.cls()
        try:
            mp.setDataSource(path)
            mp.prepare()
            mp.start()
        except Exception as e:
            mp.release()
            raise OSError(str(e))
        return self.Handle(mp)

    @classmethod
    def find(cls):
        try:
            import importlib
            jnius = importlib.import_module('jnius')
            return cls(jnius.autoclass('android.media.MediaPlayer'))
        except Exception:
            return None


class MixerPlayer:
    """SDL's mixer, through pygame.  Pydroid chooses how to run a script
    from the modules it imports, so the module's name is put together at
    run time: a Tk game must not be started as an SDL one."""
    music = True

    class Handle:
        def __init__(self, channel, snd):
            self.channel, self.snd = channel, snd

        def poll(self):
            ch = self.channel
            if ch and ch.get_busy() and ch.get_sound() is self.snd:
                return None
            return 0

        def terminate(self):
            if self.poll() is None:
                self.channel.stop()

    def __init__(self, mixer):
        self.mixer = mixer
        self.sounds = {}

    def start(self, path):
        snd = self.sounds.get(path)
        if snd is None:
            try:
                snd = self.sounds[path] = self.mixer.Sound(path)
            except Exception as e:
                raise OSError(str(e))
        return self.Handle(snd.play(), snd)

    @classmethod
    def find(cls):
        try:
            import importlib
            os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
            mixer = importlib.import_module('py' + 'game.mixer')
            mixer.init(RATE, -16, 1, 512)
            mixer.set_num_channels(8)
            return cls(mixer)
        except Exception:
            return None


class WinsoundPlayer:
    """Windows' winsound: one sound at a time, so effects only."""
    music = False

    class Handle:
        def poll(self):
            return 0

        def terminate(self):
            pass

    def __init__(self, ws):
        self.ws = ws

    def start(self, path):
        self.ws.PlaySound(path, self.ws.SND_FILENAME | self.ws.SND_ASYNC)
        return self.Handle()

    @classmethod
    def find(cls):
        if not sys.platform.startswith('win'):
            return None
        try:
            import winsound
            return cls(winsound)
        except ImportError:
            return None


def find_player():
    player = CommandPlayer.find()
    if not player and ANDROID:
        player = MediaPlayer.find()
    return player or WinsoundPlayer.find() or MixerPlayer.find()


class Sound:
    def __init__(self, game_id):
        self.on = True
        self.dir = os.path.join(os.path.expanduser('~'), '.cache', game_id)
        self.player = find_player()
        self.procs = []
        self.ready = set()
        self.music_on = True
        self.tunes = {}             # name -> wav path, once rendered
        self.lengths = {}
        self.loops = {}
        self.want = None
        self.playing = None
        self.proc = None
        self.deadline = 0.0

    @property
    def available(self):
        return self.player is not None

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
            self.player = None

    def play(self, name):
        """Play an effect, unless too many are still going: if the system's
        audio is stuck, players never exit, and they must not pile up."""
        if not self.on or name not in self.ready or not self.player:
            return
        self.procs = [h for h in self.procs if h.poll() is None]
        if len(self.procs) >= 4:
            return
        try:
            self.procs.append(self.player.start(self.path(name)))
        except OSError:
            pass

    # ------------------------------------------------------------ music

    def prepare_music(self, tunes, first=('title',)):
        """Render tunes in a background thread, the first ones first."""
        if not self.player or not self.player.music:
            return
        from . import music
        order = sorted(tunes, key=lambda n: (n not in first, n))

        def work():
            for name in order:
                tune = tunes[name]
                try:
                    sig = zlib.crc32(json.dumps([tune, music.RATE],
                                                sort_keys=True).encode())
                    path = os.path.join(self.dir, 'music-%s-%08x.wav'
                                        % (name, sig))
                    if not os.path.exists(path):
                        os.makedirs(self.dir, exist_ok=True)
                        write_wav(path + '.tmp', music.render(tune))
                        os.replace(path + '.tmp', path)
                    with wave.open(path) as w:
                        self.lengths[path] = w.getnframes() / w.getframerate()
                    self.loops[name] = tune.get('loop', True)
                    self.tunes[name] = path
                except (OSError, ValueError, KeyError):
                    pass
        threading.Thread(target=work, daemon=True).start()

    def music(self, name):
        """Ask for a tune (None for silence); tick() makes it so."""
        self.want = name

    def tick(self):
        want = self.want if (self.on and self.music_on) else None
        path = self.tunes.get(want)
        proc = self.proc
        running = proc is not None and proc.poll() is None
        if running and time.monotonic() > self.deadline:
            self.stop_music()           # a stuck player: start over
            running = False
        if want == self.playing and running:
            return
        if want != self.playing:
            self.stop_music()
            self.playing = None
        elif not running and not self.loops.get(want, True):
            return                      # a fanfare plays once
        if path and self.player:
            try:
                self.proc = self.player.start(path)
                self.playing = want
                self.deadline = time.monotonic() + \
                    self.lengths.get(path, 60) + 5
            except OSError:
                self.player = None

    def stop_music(self):
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except OSError:
                pass
        self.proc = None

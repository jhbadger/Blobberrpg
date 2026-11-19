"""Chiptune music, written in the notation the tilerpgs use.

A tune has a chord per bar and a melody of steps (eighth notes): a note
such as "F#4" starts a note, "-" holds it and "." is silence.  Voices
repeat a one-bar pattern over each chord, where R, T and F are the chord's
root, third and fifth with an octave ("R2", "T4").  Drums: k kick, s snare,
h hi-hat.  'loop': False plays a tune once (a fanfare).

The engine plays 'title', 'town' (outdoor levels), 'dungeon' (other
levels), 'combat' and 'victory'.  A level picks another with 'music': name,
and a game adds or replaces tunes with a MUSIC dict.
"""

import math
import random

RATE = 22050
VOLUME = 0.55           # relative to the sound effects

NOTE_STEPS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

TUNES = {
    'title': {      # slow and grave, in D minor
        'tempo': 150, 'bar': 8,
        'chords': 'Dm Dm Bb A  Dm Gm A Dm',
        'lead': ('square', 0.25, 0.06),
        'melody': """
            D4 - - - F4 - A4 -    | D5 - - - C5 - A4 -    |
            Bb4 - - - A4 - G4 -   | A4 - - - - - E4 -     |
            F4 - A4 - D5 - F5 -   | G5 - F5 - D5 - Bb4 -  |
            A4 - C#5 - E5 - G4 -  | D4 - - - - - . .""",
        'voices': [('triangle', 0.5, 0.22, 'R2 - - - F2 - - -'),
                   ('square', 0.125, 0.025, '. . T4 . . . F4 .')],
        'drums': 'k . . . s . . .',
    },
    'town': {       # a market-day jig, in D
        'tempo': 260, 'bar': 8,
        'chords': 'D G D A  D G A D',
        'lead': ('square', 0.25, 0.065),
        'melody': """
            F#4 - A4 - D5 - A4 -  | B4 - D5 - G5 - D5 -   |
            A4 - F#4 - A4 - D5 -  | C#5 - E5 - A4 - - -   |
            D5 - F#5 - A5 - F#5 - | G5 - B4 - D5 - G5 -   |
            E5 - C#5 - A4 - C#5 - | D5 - - - . . . .""",
        'voices': [('triangle', 0.5, 0.2, 'R2 . F2 . R2 . F2 .'),
                   ('square', 0.25, 0.03, '. T4 . F4 . T4 . F4')],
        'drums': 'k . h . s . h .',
    },
    'dungeon': {    # sparse and uneasy, in A minor
        'tempo': 140, 'bar': 8,
        'chords': 'Am Am F E  Am Dm E Am',
        'lead': ('triangle', 0.5, 0.09),
        'melody': """
            A3 - - - . . E4 -     | C4 - - - B3 - A3 -    |
            F3 - - - . . A3 -     | G#3 - - - - - . .     |
            E4 - - - D4 - C4 -    | F4 - - - E4 - D4 -    |
            B3 - G#3 - E3 - - -   | A3 - - - . . . .""",
        'voices': [('triangle', 0.5, 0.16, 'R2 - - - - - - -'),
                   ('square', 0.125, 0.02, '. . . F3 . . . T3')],
        'drums': 'k . . . . . . .',
    },
    'halls': {      # a deeper dark with a pulse, in D minor
        'tempo': 180, 'bar': 8,
        'chords': 'Dm Bb Gm A  Dm Bb A A',
        'lead': ('square', 0.125, 0.06),
        'melody': """
            D4 - E4 - F4 - E4 -   | D4 - - - Bb3 - - -    |
            G3 - A3 - Bb3 - D4 -  | C#4 - - - A3 - - -    |
            F4 - G4 - A4 - G4 -   | F4 - - - D4 - - -     |
            E4 - F4 - E4 - C#4 -  | A3 - - - . . . .""",
        'voices': [('triangle', 0.5, 0.2, 'R2 R2 . R2 R2 . R2 .'),
                   ('square', 0.125, 0.025, '. . F3 . . T3 . .')],
        'drums': 'k . s . k k s .',
    },
    'combat': {     # urgent, in E minor
        'tempo': 300, 'bar': 8,
        'chords': 'Em Em C D  Em Em C B',
        'lead': ('square', 0.25, 0.06),
        'melody': """
            E4 E4 G4 E4 B4 E4 G4 E4   | E5 - D5 - B4 - G4 -     |
            C5 - E5 - G5 - E5 -       | D5 - F#5 - A5 - F#5 -   |
            E4 E4 G4 E4 B4 E4 G4 E4   | G5 - F#5 - E5 - B4 -    |
            C5 - B4 - A4 - G4 -       | F#4 - - - D#4 - - -""",
        'voices': [('triangle', 0.5, 0.22, 'R2 R3 R2 R3 R2 R3 R2 R3'),
                   ('square', 0.125, 0.025, 'T4 . F4 . T4 . F4 .')],
        'drums': 'k h s h k k s h',
    },
    'victory': {    # a fanfare, played once
        'tempo': 240, 'bar': 8, 'loop': False,
        'chords': 'C F G C',
        'lead': ('square', 0.25, 0.07),
        'melody': """
            C5 - E5 - G5 - C6 -   | A5 - - - F5 - A5 -    |
            G5 - B5 - D6 - B5 -   | C6 - - - - - . .""",
        'voices': [('triangle', 0.5, 0.22, 'R2 - R2 - R2 - R2 -'),
                   ('square', 0.25, 0.03, 'T4 . F4 . T4 . F4 .')],
        'drums': 'k . s . k . s .',
    },
}


def note_number(name):
    """MIDI note number of a name such as 'C#4' or 'Bb3'."""
    n = NOTE_STEPS[name[0]] + 12 * (int(name[-1]) + 1)
    return n + name[1:-1].count('#') - name[1:-1].count('b')


def freq_of(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def chord_note(chord, token):
    """Pitch of pattern token R/T/F<octave> over a chord such as 'F#m'."""
    minor = chord.endswith('m')
    root = note_number((chord[:-1] if minor else chord) + token[1])
    return root + {'R': 0, 'T': 3 if minor else 4, 'F': 7}[token[0]]


def check(tune):
    """Raise ValueError if a tune's parts don't fit its chords."""
    bar = tune['bar']
    chords = tune['chords'].split()
    steps = len(tune['melody'].replace('|', ' ').split())
    if steps != len(chords) * bar:
        raise ValueError('melody has %d steps, not %d' % (steps,
                                                          len(chords) * bar))
    for t in tune['melody'].replace('|', ' ').split():
        if t not in '.-':
            note_number(t)
    for _, _, _, pattern in tune['voices']:
        if len(pattern.split()) != bar:
            raise ValueError('voice pattern %r is not %d steps' % (pattern,
                                                                    bar))
        for t in pattern.split():
            if t not in '.-':
                for ch in chords:
                    chord_note(ch, t)
    if len(tune['drums'].split()) != bar:
        raise ValueError('drum pattern is not %d steps' % bar)


def synth_note(buf, start, n, freq, wave, duty, gain):
    att = int(0.004 * RATE)
    rel = max(1, min(int(0.025 * RATE), n // 3))
    step = freq / RATE
    for k in range(min(n, len(buf) - start)):
        ph = (k * step) % 1.0
        if wave == 'square':
            v = 1.0 if ph < duty else -1.0
        else:
            v = 4 * ph - 1 if ph < 0.5 else 3 - 4 * ph
        env = gain * (1 - 0.3 * k / n)
        if k < att:
            env *= k / att
        elif k > n - rel:
            env *= (n - k) / rel
        buf[start + k] += v * env


def synth_drum(buf, start, kind, rng):
    if kind == 'k':                                  # falling sine thump
        n = int(0.12 * RATE)
        for k in range(min(n, len(buf) - start)):
            t = k / RATE
            buf[start + k] += 0.35 * (1 - k / n) ** 2 * math.sin(
                2 * math.pi * (110 * t - 160 * t * t))
        return
    n, gain, a = ((int(0.11 * RATE), 0.12, 0.75) if kind == 's'
                  else (int(0.03 * RATE), 0.06, 0.95))
    y = x_prev = 0.0
    for k in range(min(n, len(buf) - start)):
        x = rng.uniform(-1, 1)
        y = a * (y + x - x_prev)                     # high-passed noise
        x_prev = x
        buf[start + k] += y * gain * (1 - k / n) ** 2


def render(tune):
    """The samples of a tune, in [-1, 1]."""
    check(tune)
    step = int(RATE * 60 / tune['tempo'])
    chords = tune['chords'].split()
    bar = tune['bar']
    nsteps = len(chords) * bar
    tail = 0 if tune.get('loop', True) else RATE // 2
    buf = [0.0] * (nsteps * step + tail)

    def play(tokens, wave, duty, gain, pitch):
        i = 0
        while i < len(tokens):
            j = i + 1
            while j < len(tokens) and tokens[j] == '-':
                j += 1
            if tokens[i] not in '.-':
                synth_note(buf, i * step, (j - i) * step,
                           freq_of(pitch(i, tokens[i])), wave, duty, gain)
            i = j

    melody = tune['melody'].replace('|', ' ').split()
    wave, duty, gain = tune['lead']
    play(melody, wave, duty, gain, lambda i, t: note_number(t))
    for wave, duty, gain, pattern in tune['voices']:
        play(pattern.split() * len(chords), wave, duty, gain,
             lambda i, t: chord_note(chords[i // bar], t))
    rng = random.Random(1)
    for i, t in enumerate(tune['drums'].split() * len(chords)):
        if t != '.':
            synth_drum(buf, i * step, t, rng)
    return [v * VOLUME for v in buf]

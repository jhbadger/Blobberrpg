"""The rules: dice, races, classes, items, spells, monsters and the
characters of the party.

Everything here is the engine's standard fantasy ruleset.  A game adds to
or replaces any table (ITEMS.update({...}) and so on) before play starts.
"""

import random
import re

# ------------------------------------------------------------------- dice

_DICE = re.compile(r'^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$')


def roll(expr, rng=random):
    """'3d6+2', '1d4', '7' -> an int."""
    if isinstance(expr, int):
        return expr
    m = _DICE.match(expr)
    if not m:
        return int(expr)
    n = int(m.group(1) or 1)
    s = int(m.group(2))
    k = int((m.group(3) or '0').replace(' ', ''))
    return sum(rng.randint(1, s) for _ in range(n)) + k


def dice_max(expr):
    if isinstance(expr, int):
        return expr
    m = _DICE.match(expr)
    if not m:
        return int(expr)
    return int(m.group(1) or 1) * int(m.group(2)) + \
        int((m.group(3) or '0').replace(' ', ''))


def bonus(stat):
    """The bonus a stat from 3 to 18 gives: -2 to +3."""
    return max(-2, min(3, (stat - 10) // 2 - (1 if stat < 10 else 0)))


STATS = ('st', 'iq', 'dx', 'cn', 'lk')
STAT_NAMES = {'st': 'Strength', 'iq': 'Intellect', 'dx': 'Dexterity',
              'cn': 'Constitution', 'lk': 'Luck'}

# ------------------------------------------------------------ races, classes

RACES = {
    'Human':    dict(st=0, iq=0, dx=0, cn=0, lk=1,
                     text='Steady and adaptable, a little luckier than most.'),
    'Elf':      dict(st=-1, iq=2, dx=1, cn=-1, lk=0,
                     text='Quick and clever, but slight.'),
    'Dwarf':    dict(st=1, iq=-1, dx=-1, cn=2, lk=0,
                     text='Tough as the stone they mine.'),
    'Halfling': dict(st=-2, iq=0, dx=2, cn=0, lk=2,
                     text='Small, nimble and outrageously lucky.'),
}

CLASSES = {
    'Fighter': dict(abbr='FI', hd=10, atk=1.0, magic=None, every=5,
                    gear={'all'},
                    text='Master of every weapon and armour. Gains an extra '
                         'attack every five levels.'),
    'Paladin': dict(abbr='PA', hd=9, atk=1.0, magic='priest', magic_from=3,
                    every=7, gear={'all'},
                    text='A holy warrior: fights nearly as well as a fighter '
                         'and learns priest prayers from third level.'),
    'Rogue':   dict(abbr='RO', hd=6, atk=0.75, magic=None, every=0,
                    gear={'blade', 'blunt', 'light'},
                    text='Picks locks, disarms traps on chests, and strikes '
                         'hard from behind the front line.'),
    'Priest':  dict(abbr='PR', hd=8, atk=0.67, magic='priest', every=0,
                    gear={'blunt', 'hammer', 'light', 'medium'},
                    text='Heals the party, cures poison, turns the undead '
                         'and raises the fallen.'),
    'Mage':    dict(abbr='MA', hd=4, atk=0.5, magic='mage', every=0,
                    gear=set(),
                    text='Weak in body, mighty in spells: fire, frost, '
                         'light and the secrets of the maze.'),
}

XP_TABLE = [0, 0, 120, 300, 600, 1000, 1600, 2500, 3800, 5600, 8000, 11000,
            15000, 20000]
MAX_LEVEL = len(XP_TABLE) - 1


def xp_for(level):
    if level < len(XP_TABLE):
        return XP_TABLE[level]
    return XP_TABLE[-1] + (level - len(XP_TABLE) + 1) * 6000


# ------------------------------------------------------------------- items
#
# kind: weapon armor shield helm gloves ring potion scroll torch key quest
# gear: see can_use().

ITEMS = {
    'dagger':     dict(name='Dagger', kind='weapon', dmg='1d4', price=6),
    'staff':      dict(name='Quarterstaff', kind='weapon', dmg='1d6',
                       price=5),
    'club':       dict(name='Club', kind='weapon', dmg='1d6', price=4,
                       gear='blunt'),
    'mace':       dict(name='Mace', kind='weapon', dmg='1d6+1', price=18,
                       gear='blunt'),
    'shortsword': dict(name='Short Sword', kind='weapon', dmg='1d6',
                       hit=1, price=22, gear='blade'),
    'longsword':  dict(name='Long Sword', kind='weapon', dmg='1d8', hit=1,
                       price=45, gear='heavy'),
    'warhammer':  dict(name='War Hammer', kind='weapon', dmg='1d8+1',
                       price=60, gear='hammer'),
    'battleaxe':  dict(name='Battle Axe', kind='weapon', dmg='1d10', price=70,
                       gear='heavy'),
    'robes':      dict(name='Robes', kind='armor', ac=1, price=6),
    'leather':    dict(name='Leather Armour', kind='armor', ac=2, price=30,
                       gear='light'),
    'chain':      dict(name='Chain Mail', kind='armor', ac=4, price=110,
                       gear='medium'),
    'plate':      dict(name='Plate Armour', kind='armor', ac=6, price=320,
                       gear='plate'),
    'buckler':    dict(name='Buckler', kind='shield', ac=1, price=16,
                       gear='light'),
    'kite':       dict(name='Kite Shield', kind='shield', ac=2, price=60,
                       gear='medium'),
    'cap':        dict(name='Leather Cap', kind='helm', ac=1, price=14,
                       gear='light'),
    'helm':       dict(name='Iron Helm', kind='helm', ac=2, price=70,
                       gear='plate'),
    'gauntlets':  dict(name='Gauntlets', kind='gloves', ac=1, price=40,
                       gear='medium'),
    'potion':     dict(name='Healing Potion', kind='potion', use='heal',
                       amount='3d8+2', price=35),
    'antidote':   dict(name='Antidote', kind='potion', use='cure', price=20),
    'torch':      dict(name='Torch', kind='torch', use='light', light=3.2,
                       turns=160, price=4),
    'firescroll': dict(name='Scroll of Flame', kind='scroll', use='spell',
                       spell='FLAM', price=60),
    'returnscroll': dict(name='Scroll of Return', kind='scroll', use='spell',
                         spell='HOME', price=120),
}


def can_use(cls, item):
    """Whether a class may wield or wear an item.  An item's gear group is
    'any' (the default), 'blade', 'blunt', 'heavy', 'hammer', 'light',
    'medium' or 'plate'; a class lists the groups it may use, or 'all'."""
    groups = CLASSES[cls]['gear']
    g = item.get('gear', 'any')
    return g == 'any' or 'all' in groups or g in groups


SLOTS = ('weapon', 'armor', 'shield', 'helm', 'gloves', 'ring')
SLOT_OF = {'weapon': 'weapon', 'armor': 'armor', 'shield': 'shield',
           'helm': 'helm', 'gloves': 'gloves', 'ring': 'ring',
           'amulet': 'ring'}
PACK = 8

# ------------------------------------------------------------------ spells
#
# target: 'none' 'ally' 'party' 'group' 'foes' 'foe'
# effect: what Game.cast does with it.

SPELLS = {
    # mage
    'ARBO': dict(name='Arc Bolt', school='mage', level=1, sp=3,
                 target='foe', effect='damage', dice='2d6', per=1,
                 combat=True, text='A crackling bolt for one foe.'),
    'GLIM': dict(name='Glimmer', school='mage', level=1, sp=2,
                 target='none', effect='light', light=5.0, turns=300,
                 combat=False, text='Magical light: see far down the halls.'),
    'FLAM': dict(name='Flame Fan', school='mage', level=2, sp=6,
                 target='group', effect='damage', dice='2d6', per=1,
                 combat=True, text='Fire washes over a group of foes.'),
    'SEEK': dict(name='Seeker', school='mage', level=2, sp=4,
                 target='none', effect='locate', combat=False,
                 text='Tells where you stand and maps the halls nearby.'),
    'WARD': dict(name='Mystic Ward', school='mage', level=3, sp=5,
                 target='party', effect='ward', amount=2, combat=True,
                 text='The whole party is harder to hit this fight.'),
    'DOZE': dict(name='Slumber', school='mage', level=3, sp=6,
                 target='group', effect='sleep', combat=True,
                 text='Puts a group of the living to sleep.'),
    'FROS': dict(name='Frost Storm', school='mage', level=4, sp=11,
                 target='foes', effect='damage', dice='3d6', per=1,
                 combat=True, text='Ice storms every foe within 30 feet.'),
    'PASS': dict(name='Passwall', school='mage', level=4, sp=9,
                 target='none', effect='phase', combat=False,
                 text='Walk through the wall in front of you.'),
    'DOOM': dict(name='Doom Bolt', school='mage', level=5, sp=16,
                 target='foe', effect='damage', dice='8d8', per=2,
                 combat=True, text='Terrible black fire for one foe.'),
    'HOME': dict(name='Homeward', school='mage', level=5, sp=14,
                 target='none', effect='recall', combat=False,
                 text='Carries the party back to town.'),
    # priest
    'MEND': dict(name='Mend Wounds', school='priest', level=1, sp=2,
                 target='ally', effect='heal', dice='2d6', per=1,
                 combat=True, text='Heals one companion.'),
    'BLES': dict(name='Blessing', school='priest', level=1, sp=3,
                 target='party', effect='bless', amount=2, combat=True,
                 text='The party strikes truer this fight.'),
    'CURE': dict(name='Purify', school='priest', level=2, sp=4,
                 target='ally', effect='cure', combat=True,
                 text='Cures poison and paralysis.'),
    'TURN': dict(name='Turn Undead', school='priest', level=2, sp=5,
                 target='group', effect='turn', combat=True,
                 text='Holy power destroys a group of the undead.'),
    'SIGH': dict(name='Truesight', school='priest', level=3, sp=5,
                 target='none', effect='sight', turns=200, combat=False,
                 text='Reveals hidden doors as you walk.'),
    'HEAL': dict(name='Healing Light', school='priest', level=3, sp=9,
                 target='party', effect='heal', dice='2d8', per=1,
                 combat=True, text='Heals the whole party.'),
    'SMIT': dict(name='Smite', school='priest', level=4, sp=8,
                 target='foe', effect='smite', dice='4d8', per=1,
                 combat=True, text='Holy wrath on one foe, doubled '
                                   'against the undead.'),
    'RAIS': dict(name='Raise Dead', school='priest', level=5, sp=20,
                 target='ally', effect='raise', combat=False,
                 text='Returns a fallen companion to life.'),
}


def spell_level_cap(cls, level):
    """The highest spell level a class knows at a character level."""
    c = CLASSES[cls]
    if not c.get('magic'):
        return 0
    start = c.get('magic_from', 1)
    if level < start:
        return 0
    lv = level - start + 1
    return min(5, (lv + 1) // 2)


def known_spells(cls, level):
    cap = spell_level_cap(cls, level)
    school = CLASSES[cls].get('magic')
    return [k for k, s in SPELLS.items()
            if s['school'] == school and s['level'] <= cap]


# ---------------------------------------------------------------- monsters
#
# hp: dice; ac: lower is harder to hit (10 = none); hits: attacks per round
# special: list of 'poison', 'paralyze', 'drain', 'breath:3d6',
# 'cast:FLAM' ...; undead: Turn Undead works; range: attacks from 20'+
# group: (min, max) when met at random.

MONSTERS = {
    'rat':      dict(name='Giant Rat', plural='Giant Rats', art='rat',
                     level=1, hp='2d4', ac=8, hits=1, dmg='1d3', xp=8,
                     gold='1d4', group=(2, 5), special=['poison:10']),
    'bat':      dict(name='Cave Bat', plural='Cave Bats', art='bat',
                     level=1, hp='1d6', ac=6, hits=1, dmg='1d3', xp=6,
                     gold='0', group=(3, 6)),
    'kobold':   dict(name='Kobold', plural='Kobolds', art='kobold',
                     level=1, hp='1d8+1', ac=7, hits=1, dmg='1d6', xp=12,
                     gold='2d6', group=(2, 5)),
    'slime':    dict(name='Green Slime', plural='Green Slimes', art='slime',
                     level=2, hp='3d8', ac=9, hits=1, dmg='1d6',
                     xp=20, gold='2d8', group=(1, 2), special=['poison:30']),
    'skeleton': dict(name='Skeleton', plural='Skeletons', art='skeleton',
                     level=2, hp='2d8', ac=6, hits=1, dmg='1d6+1', xp=22,
                     gold='2d6', group=(2, 4), undead=True),
    'zombie':   dict(name='Zombie', plural='Zombies', art='zombie',
                     level=3, hp='3d8+3', ac=8, hits=1, dmg='1d8+1',
                     xp=30, gold='2d8', group=(2, 4), undead=True),
    'spider':   dict(name='Giant Spider', plural='Giant Spiders',
                     art='spider', level=3, hp='3d8', ac=5, hits=1,
                     dmg='1d6', xp=40, gold='3d6', group=(1, 3),
                     special=['poison:35']),
    'ghoul':    dict(name='Ghoul', plural='Ghouls', art='ghoul', level=4,
                     hp='4d8', ac=5, hits=2, dmg='1d4+1', xp=55,
                     gold='3d10', group=(1, 4), undead=True,
                     special=['paralyze:12']),
    'cultist':  dict(name='Ash Cultist', plural='Ash Cultists',
                     art='cultist', level=4, hp='4d6', ac=7, hits=1,
                     dmg='1d6', xp=60, gold='4d10', group=(1, 3), range=True,
                     special=['cast:ARBO:35']),
    'wraith':   dict(name='Wraith', plural='Wraiths', art='wraith', level=6,
                     hp='5d8', ac=3, hits=1, dmg='1d8', xp=110, gold='4d12',
                     group=(1, 3), undead=True, special=['drain:15']),
    'orc':      dict(name='Orc Brute', plural='Orc Brutes', art='orc',
                     level=5, hp='5d10', ac=5, hits=1, dmg='2d6', xp=80,
                     gold='5d10', group=(2, 4)),
    'imp':      dict(name='Fire Imp', plural='Fire Imps', art='imp',
                     level=5, hp='4d8', ac=3, hits=1, dmg='1d6', xp=90,
                     gold='4d10', group=(1, 3), range=True,
                     special=['breath:2d6:30']),
    'thief':    dict(name='Grave Robber', plural='Grave Robbers',
                     art='rogue', level=2, hp='2d8', ac=7, hits=1,
                     dmg='1d6', xp=25, gold='4d10', group=(2, 4)),
    'deathknight': dict(name='Death Knight', plural='Death Knights',
                        art='deathknight', level=8, hp='9d10', ac=0, hits=2,
                        dmg='1d10+2', xp=400, gold='8d20', group=(1, 2),
                        undead=True),
}

# --------------------------------------------------------------- characters


class Character:
    """One member of the party."""

    def __init__(self, name='', race='Human', cls='Fighter'):
        self.name = name
        self.race = race
        self.cls = cls
        self.level = 1
        self.xp = 0
        self.st = self.iq = self.dx = self.cn = self.lk = 10
        self.hp = self.maxhp = 1
        self.sp = self.maxsp = 0
        self.status = 'ok'      # ok poisoned paralyzed asleep dead stoned
        self.equip = {s: None for s in SLOTS}
        self.pack = []

    # Saving.

    def to_dict(self):
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d):
        c = cls()
        c.__dict__.update(d)
        for s in SLOTS:
            c.equip.setdefault(s, None)
        return c

    # Making one.

    @classmethod
    def roll_new(cls, name, race, klass, rng=random):
        c = cls(name, race, klass)
        c.reroll(rng)
        return c

    def reroll(self, rng=random):
        mods = RACES[self.race]
        for s in STATS:
            v = sum(sorted(rng.randint(1, 6) for _ in range(4))[1:])
            setattr(self, s, max(3, min(18, v + mods.get(s, 0))))
        c = CLASSES[self.cls]
        self.maxhp = max(4, c['hd'] + bonus(self.cn) * 2)
        self.hp = self.maxhp
        self.maxsp = self.sp_for_level(1)
        self.sp = self.maxsp

    def sp_for_level(self, level):
        c = CLASSES[self.cls]
        if not c.get('magic'):
            return 0
        start = c.get('magic_from', 1)
        if level < start:
            return 0
        n = level - start + 1
        return max(2, n * (3 + bonus(self.iq)) + 2)

    # Derived values.

    @property
    def abbr(self):
        return CLASSES[self.cls]['abbr']

    def item(self, slot):
        iid = self.equip.get(slot)
        return ITEMS.get(iid) if iid else None

    def ac(self, extra=0):
        a = 10 - bonus(self.dx)
        for s in SLOTS:
            it = self.item(s)
            if it:
                a -= it.get('ac', 0)
        return a - extra

    def to_hit(self):
        c = CLASSES[self.cls]
        w = self.item('weapon')
        return int(self.level * c['atk']) + bonus(self.st) + \
            (w.get('hit', 0) if w else 0)

    def damage_dice(self):
        w = self.item('weapon')
        return w['dmg'] if w else '1d2'

    def attacks(self):
        c = CLASSES[self.cls]
        every = c.get('every', 0)
        return 1 + (self.level // every if every else 0)

    @property
    def alive(self):
        return self.status not in ('dead', 'stoned')

    @property
    def able(self):
        """Can act this round."""
        return self.status in ('ok', 'poisoned')

    def spells(self):
        return known_spells(self.cls, self.level)

    def can_level(self):
        return self.level < MAX_LEVEL and self.xp >= xp_for(self.level + 1)

    def level_up(self, rng=random):
        """Raise one level; returns a description of the gains."""
        c = CLASSES[self.cls]
        self.level += 1
        gain = max(1, rng.randint(1, c['hd']) + bonus(self.cn))
        self.maxhp += gain
        self.hp += gain
        old = self.maxsp
        self.maxsp = self.sp_for_level(self.level)
        self.sp += self.maxsp - old
        notes = ['+%d hit points' % gain]
        if self.maxsp > old:
            notes.append('+%d spell points' % (self.maxsp - old))
        st = rng.choice(STATS)
        if getattr(self, st) < 18 and rng.random() < 0.5:
            setattr(self, st, getattr(self, st) + 1)
            notes.append('+1 ' + STAT_NAMES[st])
        newspells = [s for s in known_spells(self.cls, self.level)
                     if s not in known_spells(self.cls, self.level - 1)]
        if newspells:
            notes.append('new spells: ' +
                         ', '.join(SPELLS[s]['name'] for s in newspells))
        return notes

    def give(self, iid):
        if len(self.pack) >= PACK:
            return False
        self.pack.append(iid)
        return True

    def equip_item(self, idx):
        """Wear or wield pack item idx; returns an error or None."""
        iid = self.pack[idx]
        it = ITEMS[iid]
        slot = SLOT_OF.get(it['kind'])
        if not slot:
            return "That isn't something to wear or wield."
        if not can_use(self.cls, it):
            return 'A %s cannot use that.' % self.cls.lower()
        self.pack.pop(idx)
        old = self.equip.get(slot)
        self.equip[slot] = iid
        if old:
            self.pack.append(old)
        return None

    def unequip(self, slot):
        iid = self.equip.get(slot)
        if not iid:
            return None
        if len(self.pack) >= PACK:
            return 'No room in the pack.'
        self.equip[slot] = None
        self.pack.append(iid)
        return None


# ------------------------------------------------------------- monster groups


class Foe:
    """A monster in a fight."""
    __slots__ = ('kind', 'hp', 'maxhp', 'asleep', 'held')

    def __init__(self, kind, rng=random):
        self.kind = kind
        self.hp = self.maxhp = max(1, roll(MONSTERS[kind]['hp'], rng))
        self.asleep = 0
        self.held = 0


class Group:
    """A group of the same monster, some distance away."""

    def __init__(self, kind, n, dist=10, rng=random):
        self.kind = kind
        self.m = MONSTERS[kind]
        self.foes = [Foe(kind, rng) for _ in range(n)]
        self.dist = dist

    @property
    def alive(self):
        return [f for f in self.foes if f.hp > 0]

    def label(self):
        n = len(self.alive)
        name = self.m['name'] if n == 1 else self.m['plural']
        return '%d %s (%d\')' % (n, name, self.dist)

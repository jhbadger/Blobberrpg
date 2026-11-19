"""The words the engine itself puts on the screen.

They default to sword-and-sorcery.  A game with another setting gives a
WORDS dict naming only the ones it changes, for example

    WORDS = {'money': 'credits', 'magic': 'psi', 'cast': 'Use psionics'}

Entries with %s or %d are filled in by the engine, in the order shown.
"""

DEFAULTS = {
    # money
    'money':        'gold',             # "120 gold"
    'found_money':  'You find %d gold pieces.',
    'chest_money':  'Inside are %d gold pieces.',
    # magic
    'magic':        'spell',            # "No one can cast a spell now."
    'Magic':        'Spells',           # heading on the character sheet
    'points':       'spell points',
    'Points':       'Spell points',
    'pts':          'Spell Pts',        # roster heading
    'sp':           'SP',
    'cast':         'Cast a spell',     # combat order
    'casts':        'casts',            # "Elowen casts Arc Bolt!"
    'who_casts':    'Who casts?',
    'none_cast':    'No one can cast a spell now.',
    'too_few':      '%s has too few spell points.',
    'fizzle':       'The spell fizzles. Something here smothers magic.',
    'fizzle_fight': 'The spell fizzles into nothing.',
    'help_cast':    'cast a spell',
    # characters
    'race':         'Race',
    'race_pick':    'Choose a race',
    'class':        'Class',
    'class_pick':   'Choose a class',
    'Armour':       'Armour',
    'armour_class': 'Armour class',
    'new_hero':     'A new adventurer',
    'name_hero':    'What is the name of this new adventurer?',
    # fights
    'dies':         'The %s dies!',
    'destroyed':    'The %s is destroyed!',     # for a 'mindless' tag
    'turned':       '%d %s crumble to dust!',
    'turn_fail':    'The %s stand firm.',
    'turn_wrong':   'The %s are unaffected.',
    'breath':       'breathes fire!',
    'shoots':       'shoots at',        # a monster's ranged attack
    'melee_miss':   '%s swings at %s and misses.',
    'shot_miss':    '%s fires at %s and misses.',
    'no_ammo':      '%s is out of %s!',
    'can_train':    '%s can train for a new level at the Guild.',
    # light
    'light_out':    'Your light flickers and goes out.',
    'too_bright':   "It's bright enough out here.",
    # town
    'guild':        'the Guild',
    'Guild':        "Adventurers' Guild",
    'shop':         'The Armoury',
    'temple':       'The Temple',
    'inn':          'The Inn',
    'sage':         "The Sage's Tower",
    'heal_wounds':  'Heal wounds',
    'raise':        'Raise',
    'healed':       'The priestess lays hands on your wounds.',
    'rest':         'Rest the night',
    'rested':       'You sleep soundly. Hit points and spell points are '
                    'restored, and the game is saved.',
    'morning':      'Morning comes. You wake rested and whole.',
    'counsel':      'Ask for counsel',
    'lore':         'Ask about the old days',
}

WORDS = dict(DEFAULTS)


def setup(game_words):
    WORDS.clear()
    WORDS.update(DEFAULTS)
    WORDS.update(game_words or {})


def w(key, *args):
    s = WORDS.get(key, key)
    return s % args if args else s

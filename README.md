# Blobber

An engine for *blobbers*: first-person, party-based dungeon crawlers in
the style of the 1980s, where a party of six moves as one through a maze
of squares, seen through a window on the world, with a scroll of messages
beside it and the party's roster below. It's written in Python and Tk
with nothing to install. Everything is drawn in code, sound and music
included, so there are no image or sound files.

The sample game is **The Ashen Crypt**.

```bash
./ashencrypt
```

If Python reports `No module named '_tkinter'`, install your Python's Tk
package (`brew install python-tk` with Homebrew Python on macOS, or
`sudo apt install python3-tk` on Debian and Ubuntu).

## The Ashen Crypt

Hollowmere is a market town on the edge of the Fenwold. Beneath its ruined
chapel lies Morvane, the Ashen King, and he is waking: the dead walk in
the churchyard, and grey ash falls on the rooftops every night. Take the
party down through three levels (the Undercroft, the Catacombs and the
Ashen Halls), destroy the King, and bring his crown to the temple to be
unmade.

- **Hollowmere** is a little walled town seen in 3D, like the city in the
  classic blobbers. Walk into a shop's door to go in:
  - the Adventurers' Guild trains characters to new levels, creates new
    adventurers, swaps them in and out of the party and changes the
    marching order;
  - Greta's Armoury buys and sells;
  - the Temple heals, cures and raises the dead;
  - the Cracked Bell inn restores hit points and spell points, has gossip,
    and saves the game;
  - Thessaly the Sage gives hints for a price.
- **The party**: Brannoc (fighter), Hild (paladin), Torvald (fighter), Pip
  (rogue, with a bow so he can shoot from the back row), Mother Aveline
  (priest) and Elowen (mage). At the Guild you can roll up others.
- **The dungeon** has doors, locked doors (keys, picking, forcing), hidden
  doors, a riddle door, magical darkness, a spinner, teleport traps, pits,
  a place where magic dies, fountains, chests (some trapped), guardians
  and a final battle.

### Keys

| Key | |
| --- | --- |
| Arrows or W A S D | walk and turn (Q and E step sideways) |
| Enter or Space | deal with what's ahead or here: doors, shops, chests |
| C | cast a spell |
| 1 to 6 | a character's sheet: equip, use, trade and drop items |
| M | the map |
| F | search for hidden doors |
| Esc | the game menu: save, sound, music, fight speed, quit |
| ? | help |

With the mouse, click the left or right third of the view to turn and the
middle to walk. Click a roster line to open that character's sheet, and
click choices on the scroll. F11 toggles full screen. The window scales
to fit whatever size you give it.

In a fight the party chooses to fight or run. Each character then gets an
order (attack, defend, cast or use an item) and the round plays out a line
at a time. Only the first three in the marching order can fight hand to
hand; anyone with a bow or crossbow can shoot from any rank, using up the
party's arrows (the Armoury sells more).

The game saves to `~/.ashencrypt.json` whenever you change level, rest at
the inn, or quit.

## The engine

`blobber/` holds the engine, which knows nothing about any one game:

| Module | What it does |
| --- | --- |
| `gfx.py` | the 640×400 framebuffer, images with transparency, the dithering helpers |
| `font.py` | the bitmap font |
| `view.py` | the 3D view: precomputed slots for every wall, floor and ceiling a square can show, distance shading, sprites, sky |
| `textures.py` | wall, floor and ceiling textures drawn in code (brick, stone blocks, flagstones, cobbles, half-timbered houses, shop fronts, doors) |
| `paint.py` | a painter for pictures: shaded spheres, limbs and polygons, mapped to colour ramps with ordered dithering and outlined |
| `art.py` | monsters, townsfolk and things in squares, painted with `paint.py` |
| `rules.py` | dice, races, classes, items, spells, monsters, characters |
| `world.py` | levels and their legends |
| `game.py` | the party's state, the screen layout, walking, square events, magic, saving, menus |
| `modes.py` | title, exploring, map, character sheet, game over, ending |
| `combat.py` | fights |
| `town.py` | Guild, shop, temple, inn and sage |
| `sound.py` | synthesized sound effects and the music player (afplay, paplay/aplay or winsound) |
| `music.py` | chiptune tunes in the tilerpgs' notation, and their synthesizer |
| `words.py` | every word the engine puts on screen, which a game can change |
| `balance.py` | a simulated player that measures a game's difficulty |
| `tkshell.py` | the Tk window |

The whole screen, text included, is drawn into one framebuffer in pure
Python, and the front end only shows the result. So a Kivy front end (for
Android, like the tilerpgs) only has to blit the same bytes into a
texture.

The view has no raycasting at run time. Since the party always stands in
the middle of a square facing one of four ways, every screen pixel a wall
face, floor or ceiling can cover is worked out once. After that, drawing a
wall is a few cached byte copies, so a step takes about a millisecond.

### Making a game

A game is a script that defines a handful of names and calls
`blobber.run()`. See `ashencrypt` for a complete one.

- `ID`, `TITLE`, `SUBTITLE`, `TITLE_ART`, `INTRO` (pages), `WELCOME`,
  `DEATH`
- `PARTY`: the starting party, `GOLD`, and `START = (level, x, y, facing)`
  (facing is 0 to 3 for north, east, south and west)
- `LEVELS`: each level has a `name`, a `map` (rows of characters), a
  `legend` (what each character means), a `theme` (textures, light, fog),
  random `encounters` and their `rate`, and `outdoor=True` for a level
  under the sky
- `HINTS` for the sage, and `HOOKS` for anything the engine doesn't do
  itself (the sample uses one for its ending)
- `SUPPLIES`: the ammunition the party starts with, such as
  `{'arrows': 40}`
- `WORDS`: the engine's on-screen words this game changes (see below)
- `MUSIC`: tunes to add or replace; a level picks one with `music=`
- changes to the rules tables: `rules.ITEMS.update(...)`,
  `rules.MONSTERS.update(...)`, `rules.XP_TABLE`, `rules.LOOT` and so on

The rules tables are a stock fantasy set. Every entry can be replaced, and
a few fields make them fit other settings:

- items: `verb` ("drinks", "slashes", "fires"), `range` in feet for a
  weapon that works from any rank, and `ammo` naming the supply each shot
  uses. An item of kind `'ammo'` adds `amount` to that supply when bought.
- monsters: `tags` that spells single out (Turn Undead looks for
  `'undead'`; a game could tag `'robot'`), `range` with `shoots` ("hurls
  fire at"), `unique` ("the Ashen King", immune to sleep and turning),
  `acts` (actions a round, for bosses) and `death` (what's said when it
  falls)
- spells: `tag` for a turning spell, `bane` for one that does double
  damage to a tag, `immune` for tags a sleep spell can't touch
- `rules.UNLIVING`: tags whose monsters are "destroyed" rather than killed

### Words

Everything the engine itself says, from "gold" and "spell points" to "Cast
a spell", "Raise" and "the Guild", is in `blobber/words.py`. A game with
another setting names only the ones it changes:

```python
WORDS = {'money': 'credits', 'points': 'psi points', 'Points': 'Psi points',
         'pts': 'Psi Pts', 'sp': 'PP', 'cast': 'Use psionics',
         'guild': 'Command', 'raise': 'Revive'}
```

### Music

Tunes are written as in the tilerpgs: a chord per bar, a melody of eighth
notes (`F#4` starts a note, `-` holds it, `.` rests), voices that repeat a
one-bar pattern of chord tones (`R2`, `T4`, `F3`) and a drum pattern
(`k s h`). The engine plays `title`, `town`, `dungeon`, `combat` and
`victory` (once) when they suit, and the sample adds `halls` for its last
level. Tunes render in the background on the first run and are cached in
`~/.cache/<game>`.

A legend entry is a dict. The keys, all documented in `world.py`, include
`solid`, `wall`, `floor`, `ceil`, `sprite`, `door` (`True` or
`'locked'`) with `key`, `secret`, `riddle`, `goto` (stairs and portals),
`msg`, `fight`, `chest`, `item`, `fountain`, `trap`, `spin`, `teleport`,
`dark`, `antimagic`, `shop`, `hook`, `requires` and `unless` (switch a
square on or off by a flag).

New textures and pictures are functions registered with
`@textures.texture('name')` and `@art.picture('name', w, h, height)`.

### Checking a game

```bash
./ashencrypt --selftest
```

This checks every level: legend characters, textures, pictures, items,
monsters, stairs that land in walls, and squares that can't be reached.
It also draws every texture and picture once and plays a fight.

```bash
./ashencrypt --shot out.png --keys "enter,enter,enter,enter,up,left"
```

This plays a list of keys without a window and saves the screen as a PNG.

```bash
./ashencrypt --balance 20
```

This plays the game's fights with a simulated player over 20 campaigns.
The player heals the hurt, casts its best spells when a fight is worth it,
goes back to town to rest, train and buy better gear, and dives deeper as
the party grows. The report gives the number of random fights to reach
each level, then each fixed fight's chance of winning (and rounds taken,
and hit points left) for the parties those campaigns had at each level. A
real player is less tidy than the simulated one, so aim for fights the
simulation wins comfortably at the level a player arrives.

Other flags are `--mute`, `--nomusic`, and `--scale 2` to choose the
window's size.

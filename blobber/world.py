"""Maps.

A level is drawn as rows of characters, one per square.  Every character
means something through the level's legend, which starts from BASE_LEGEND
and adds the level's own.  A legend entry is a dict:

  solid      a wall you can't walk into (bumping it may still do things)
  wall       texture (or list of textures, chosen per square) for a solid
  floor/ceil textures for an open square ('@stairs' = the theme's stairs)
  sprite     a picture standing in the square (see art.py)
  door       True for a door, 'locked' for a locked one
  key        the item that opens a locked door ('' = none: it can only
             be picked or forced)
  secret     looks like wall but you can walk through it
  riddle     {'q': question, 'a': [answers], 'flag': name} a door that
             opens when answered
  goto       [level, x, y, facing] where stairs or a portal lead
  stairs     'up' or 'down' (only for the wording)
  msg        text shown when you step here ('once': only the first time;
             'flag': a flag it sets, for something learned by reading)
  fight      [(monster, count), ...] fought on arrival until won
  chest      {'gold': dice, 'items': [...], 'trap': 'poison'|'blast'}
  fountain   'heal' | 'mana' | 'poison' | 'cure'
  trap       {'dmg': dice, 'kind': 'pit'|'darts', 'msg': ...}
  spin       True: turns the party round at random
  teleport   [x, y, facing] (same level)
  dark       magical darkness: no light works here
  rad        radiation of this class: each step costs everyone that
             many d6 (half on a save); 'rad_msg' the first time
  antimagic  spells fail here
  shop       'guild' | 'shop' | 'temple' | 'inn' | 'sage' (bump to enter)
  hook       name of a function in the game's HOOKS
  unless     a flag: the square does nothing once it is set
  name       what to call the place on the nameplate (shops)
"""

DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))
DIR_NAMES = ('north', 'east', 'south', 'west')
DIR_LETTERS = 'NESW'

BASE_LEGEND = {
    '#': dict(solid=True),
    '.': dict(),
    ' ': dict(),
    '+': dict(solid=True, door=True),
    '=': dict(solid=True, door='locked', key=''),
    'S': dict(solid=True, secret=True),
    ':': dict(dark=True),
}


class Level:
    def __init__(self, lid, spec):
        self.id = lid
        self.spec = spec
        self.name = spec.get('name', lid)
        self.rows = [r for r in spec['map']]
        self.h = len(self.rows)
        self.w = max(len(r) for r in self.rows)
        self.rows = [r.ljust(self.w, '#') for r in self.rows]
        self.theme = dict(spec.get('theme', {}))
        self.legend = dict(BASE_LEGEND)
        self.legend.update(spec.get('legend', {}))
        self.outdoor = spec.get('outdoor', False)
        self.encounters = spec.get('encounters', [])
        self.rate = spec.get('rate', 0.0)
        self.depth = spec.get('depth', 0)

    def char(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.rows[y][x]
        return '#'

    def sq(self, x, y):
        return self.legend.get(self.char(x, y), BASE_LEGEND['#'])

    def find(self, ch):
        for y, r in enumerate(self.rows):
            x = r.find(ch)
            if x >= 0:
                return x, y
        return None

    def wall_texture(self, x, y, sq):
        """The texture for a solid square, with the theme's variety."""
        w = sq.get('wall')
        if isinstance(w, (list, tuple)):
            return w[(x * 7 + y * 13 + (x * y) % 5) % len(w)]
        if w:
            return w
        t = self.theme
        variants = t.get('variants', ())
        if variants:
            h = ((x * 73856093) ^ (y * 19349663) ^ 0x5bd1e995) & 0xffff
            r = h % 1000
            acc = 0
            for name, per in variants:
                acc += int(per * 1000)
                if r < acc:
                    return name
        return t.get('wall', 'plain')

    def passable(self, x, y):
        sq = self.sq(x, y)
        return not sq.get('solid') or sq.get('door') or sq.get('secret')

"""People to talk to.

A legend entry with 'talk' is someone standing in the square (with a
'sprite', and 'block': True so the party can't walk through them).  Walk
into them, or press Act facing them, to talk.  'talk' is a dict:

  id        a name for remembering what has been said (required)
  name      what they're called on the scroll
  art       their portrait (a picture from art.py)
  backdrop  a texture to show behind them (default: the level's view)
  greeting  what they say first
  topics    {keyword: answer}; an answer is text, or a dict of
              text     what they say
              needs    a flag or item the party must have first; until
                       then they say 'refuse'
              cost     gold they want for the answer (each time); without
                       it they say 'poor'
              takes    an item they take from the party (a quest's end)
              gives    an item they hand over (once)
              gold     gold they hand over (once)
              flag     a flag to set
              heal     True to heal the party
  unknown   what they say to a word they don't know
  bye       what they say when you leave

NAME and JOB are always offered.  A word in CAPITALS in anything they say
that is one of their topics is added to the list of things to ask about;
anything else can be typed.
"""

import re

from .game import TextInput, INK_HI
from .modes import scene_with, picture_view
from .rules import ITEMS
from .words import w

CAPS = re.compile(r"\b[A-Z][A-Z'-]{2,}\b")


def topics(npc):
    return {k.lower(): v for k, v in npc.get('topics', {}).items()}


def known(g, npc):
    k = g.flag('talk:%s' % npc['id'])
    return list(k) if k else []


def learn(g, npc, text):
    """Add the topics a reply mentions in CAPITALS."""
    ts = topics(npc)
    have = known(g, npc)
    for word in CAPS.findall(text):
        k = word.lower()
        if k in ts and k not in have and k not in ('name', 'job'):
            have.append(k)
    g.set_flag('talk:%s' % npc['id'], have)


def has(g, what):
    return bool(g.flag(what) or g.has_item(what))


def answer(g, npc, key):
    """What they say to a keyword, doing whatever it does."""
    ts = topics(npc)
    t = ts.get(key)
    if t is None:
        return npc.get('unknown', '"I can\'t help you with that."')
    if isinstance(t, str):
        return t
    if t.get('needs') and not has(g, t['needs']):
        return t.get('refuse', npc.get('unknown',
                                       '"I can\'t help you with that."'))
    once = 'talk:%s:%s' % (npc['id'], key)
    text = t.get('text', '')
    extra = []
    if t.get('cost'):
        if g.st.gold < t['cost']:
            return t.get('poor', '"Come back when you can pay %d %s."'
                         % (t['cost'], w('money')))
        g.st.gold -= t['cost']
        extra.append('You pay %d %s.' % (t['cost'], w('money')))
    if t.get('takes'):
        iid = t['takes']
        if not g.take_item(iid):
            for c in g.party:          # it may be worn or wielded
                for slot, eq in c.equip.items():
                    if eq == iid:
                        c.equip[slot] = None
                        break
        extra.append('You hand over the %s.' % g.item_name(iid))
    if not g.flag(once):
        if t.get('gives'):
            who = g.give_party(t['gives'])
            if who:
                extra.append('%s takes the %s.' % (who.name,
                                                   g.item_name(t['gives'])))
                g.set_flag(once)
            else:
                extra.append('(No one has room to carry the %s.)'
                             % g.item_name(t['gives']))
        if t.get('gold'):
            g.st.gold += t['gold']
            extra.append('You receive %d %s.' % (t['gold'], w('money')))
            g.set_flag(once)
        if extra:
            g.sound.play('coin')
    if t.get('flag'):
        g.set_flag(t['flag'])
    if t.get('heal'):
        for c in g.party:
            if c.alive:
                c.hp = c.maxhp
        g.sound.play('heal')
    for e in extra:
        g.say(e)
    return text + ('\n\n' + '\n'.join(extra) if extra else '')


def talk(g, sq, done=None):
    """Talk to whoever stands in a square."""
    npc = sq['talk']
    done = done or (lambda: None)
    name = npc.get('name', 'A stranger')
    if npc.get('backdrop'):
        view = picture_view(npc.get('art', 'unknown'),
                            texture=npc['backdrop'])
    else:
        view = scene_with(npc.get('art', 'unknown'), dim=0.4)

    def show(text):
        learn(g, npc, text)
        ts = topics(npc)
        opts = []
        for k in ['name', 'job'] + known(g, npc):
            if k in ts or k in ('name', 'job'):
                opts.append((k.upper(), k))
        opts.append(('Ask about something else...', '?ask'))
        opts.append(('Goodbye', '?bye'))
        g.ask(name, opts, pick, text, on_cancel=bye, view=view, place=name)

    def pick(k):
        if k == '?bye':
            bye()
        elif k == '?ask':
            g.push(TextInput(name, 'What do you ask about?',
                             lambda word: show(answer(
                                 g, npc, word.strip().lower())),
                             maxlen=16, on_cancel=lambda: show(
                                 npc.get('greeting', '')), view=view,
                             upper=True))
        else:
            show(answer(g, npc, k))

    def bye():
        text = npc.get('bye')
        if text:
            g.say('%s: %s' % (name, text))
        done()

    g.sound.play('menu')
    show(npc.get('greeting', '"Well met."'))


def check(npc, art_names, items):
    """Problems with a talk entry, for the self-test."""
    out = []
    if not npc.get('id'):
        out.append('a talk entry has no id')
    if npc.get('art') and npc['art'] not in art_names:
        out.append('talk %s: no picture %r' % (npc.get('id'), npc['art']))
    for k, t in npc.get('topics', {}).items():
        if isinstance(t, dict):
            for key in ('gives', 'takes'):
                if t.get(key) and t[key] not in items:
                    out.append('talk %s/%s: no item %r' % (npc.get('id'), k,
                                                          t[key]))
    return out

"""The Tk front end: a window showing the game's framebuffer, scaled to
fit, and the keyboard and mouse passed through to the game."""

import sys
import time
import tkinter as tk

from .game import Game, W, H
from . import art

KEYS = {
    'Up': 'up', 'Down': 'down', 'Left': 'left', 'Right': 'right',
    'Return': 'enter', 'KP_Enter': 'enter', 'Escape': 'esc',
    'BackSpace': 'backspace', 'Delete': 'backspace', 'Tab': 'tab',
    'space': 'space', 'F1': 'f1', 'question': '?',
    'KP_Up': 'up', 'KP_Down': 'down', 'KP_Left': 'left', 'KP_Right': 'right',
}
IGNORE = {'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
          'Meta_L', 'Meta_R', 'Super_L', 'Super_R', 'Caps_Lock'}

# zoom / subsample pairs Tk can scale an image by, smallest first
SCALES = [(1, 1), (3, 2), (2, 1), (5, 2), (3, 1), (7, 2), (4, 1), (5, 1)]


class TkShell:
    def __init__(self, game, scale=None):
        self.g = game
        self.root = tk.Tk()
        self.root.title(game.title)
        self.root.configure(bg='black')
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        z = 1
        for (a, b) in SCALES:
            if W * a / b <= sw * 0.92 and H * a / b <= sh * 0.85:
                z = (a, b)
        if scale:
            z = (int(scale * 2), 2)
        self.zoom = z
        ww, wh = W * z[0] // z[1], H * z[0] // z[1]
        self.root.geometry('%dx%d' % (ww, wh))
        self.root.minsize(W, H)
        self.canvas = tk.Canvas(self.root, width=ww, height=wh, bg='black',
                                highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.item = self.canvas.create_image(0, 0, anchor='nw')
        self.img = None
        self.ox = self.oy = 0
        self.root.bind('<Key>', self.on_key)
        self.canvas.bind('<Button-1>', self.on_click)
        self.root.bind('<Configure>', self.on_resize)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.full = False
        self.last = time.time()
        self.set_icon()

    def set_icon(self):
        try:
            img = art.get('icon')
            px = img.pixels()
            ph = tk.PhotoImage(width=img.w, height=img.h)
            rows = []
            for y in range(img.h):
                rows.append('{' + ' '.join(
                    '#%02x%02x%02x' % (px[y * img.w + x] or (0, 0, 0))
                    for x in range(img.w)) + '}')
            ph.put(' '.join(rows))
            self.root.iconphoto(True, ph)
            self._icon = ph
        except tk.TclError:
            pass

    def toggle_fullscreen(self, e=None):
        self.full = not self.full
        self.root.attributes('-fullscreen', self.full)

    def on_resize(self, e):
        if e.widget is not self.root:
            return
        best = (1, 1)
        for (a, b) in SCALES:
            if W * a / b <= e.width and H * a / b <= e.height:
                best = (a, b)
        if best != self.zoom:
            self.zoom = best
        self.ox = max(0, (e.width - W * self.zoom[0] // self.zoom[1]) // 2)
        self.oy = max(0, (e.height - H * self.zoom[0] // self.zoom[1]) // 2)
        self.canvas.coords(self.item, self.ox, self.oy)
        self.g.dirty = True

    def on_key(self, e):
        ks = e.keysym
        if ks in IGNORE:
            return
        k = KEYS.get(ks)
        if k is None:
            if e.char and e.char.isprintable():
                k = e.char
            else:
                k = ks.lower()
        if k and len(k) == 1 and k.isalpha() and not self.typing():
            k = k.lower()
        self.g.key(k)
        self.after_input()

    def typing(self):
        from .game import TextInput
        return isinstance(self.g.mode, TextInput)

    def on_click(self, e):
        a, b = self.zoom
        x = (e.x - self.ox) * b // a
        y = (e.y - self.oy) * b // a
        if 0 <= x < W and 0 <= y < H:
            self.g.click(x, y)
            self.after_input()

    def after_input(self):
        if self.g.quit:
            self.on_close()
            return
        self.draw()

    def on_close(self):
        try:
            if self.g.st and not self.g.quit:
                self.g.save()
        finally:
            if hasattr(self.g.sound, 'stop_music'):
                self.g.sound.music(None)
                self.g.sound.stop_music()
            self.root.destroy()

    def draw(self):
        s = self.g.render()
        img = tk.PhotoImage(data=s.ppm(), format='PPM')
        a, b = self.zoom
        if a != 1:
            img = img.zoom(a)
        if b != 1:
            img = img.subsample(b)
        self.img = img
        self.canvas.itemconfig(self.item, image=img)

    def tick(self):
        now = time.time()
        dt = now - self.last
        self.last = now
        self.g.update(dt)
        if self.g.quit:
            self.on_close()
            return
        if self.g.dirty:
            self.draw()
        self.root.after(33, self.tick)

    def run(self):
        self.draw()
        self.root.after(33, self.tick)
        self.root.mainloop()

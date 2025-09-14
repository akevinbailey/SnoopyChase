#  Copyright (c) 2025. Andrew Kevin Bailey
#  This code, firmware, and software is released under the MIT License (http://opensource.org/licenses/MIT).
#
#  The MIT License (MIT)
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
#  documentation files (the "Software"), to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or significant portions of
#  the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#  BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

# snoopy_chase.py
# Requirements: Python 3.8+, Tkinter (bundled), Pillow (pip install Pillow)

import os
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, Image as PILImage

# ---------- Config ----------
IMAGE_CHOICES = [
    ("Snoopy (flying)", "snoopy-flying.png"),
    ("Snoopy (grabbing)", "snoopy-grabbing.png"),
]
WINDOW_SIZE = (900, 600)
BG_COLOR = "#c0c0c0"
TARGET_EASING: float = 0.15  # 0..1; higher = snappier
MAX_SPEED = 18               # pixels per frame cap
FPS = 60
SPRITE_SCALE: float = 0.45   # scale your image if it's large
CURSOR_NORMAL = "arrow"      # pick "crosshair" if you prefer
POINTER_PADDING = 2          # small fudge factor (pixels) around the sprite
# ----------------------------

class ImageChoiceDialog(tk.Toplevel):
    def __init__(self, parent, choices):
        super().__init__(parent)
        self.title("Choose a Snoopy image")
        self.transient(parent)
        self.resizable(False, False)
        self.grab_set()  # modal

        self.var = tk.StringVar(value=choices[0][1])

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Which Snoopy image should chase the mouse?").pack(anchor="w", pady=(0,8))
        for label, path in choices:
            ttk.Radiobutton(frm, text=label, value=path, variable=self.var).pack(anchor="w")

        # Optional: a "Browse..." button in case the default names aren’t found
        ttk.Button(frm, text="Browse…", command=self.on_browse).pack(anchor="w", pady=(8,0))

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(12,0))
        ttk.Button(btns, text="OK", command=self.on_ok).pack(side="right", padx=(8,0))
        ttk.Button(btns, text="Cancel", command=self.on_cancel).pack(side="right")

        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())

        # Center on screen (root may be at (0,0) or hidden briefly)
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = self.winfo_width(), self.winfo_height()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    def on_browse(self):
        path = filedialog.askopenfilename(
            title="Select a Snoopy PNG",
            filetypes=[("PNG Images", "*.png"), ("All files", "*.*")]
        )
        if path:
            self.var.set(path)

    def on_ok(self):
        self.result = self.var.get()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

class ChaserApp:
    def __init__(self, root, image_path):
        self.root = root
        self.root.title("Snoopy Chases the Mouse 🐾")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        self.root.minsize(480, 360)

        # Canvas
        self.canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0, cursor=CURSOR_NORMAL)
        self.canvas.pack(fill="both", expand=True)

        # Load sprite (with robust error handling)
        pil = self.load_sprite_image(image_path)
        if pil is None:
            # If we cannot load, stop cleanly but keep the window so the user sees the error
            ttk.Label(self.canvas, text="Could not load image.", foreground="white", background=BG_COLOR).pack()
            return

        if SPRITE_SCALE != 1.0:
            w, h = pil.size
            pil = pil.resize((int(w * SPRITE_SCALE), int(h * SPRITE_SCALE)), PILImage.Resampling.LANCZOS)

        # Important: keep a strong reference to PhotoImage
        self.sprite_img = ImageTk.PhotoImage(pil)
        self.sprite = self.canvas.create_image(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2, image=self.sprite_img)

        self.sprite_w = self.sprite_img.width()
        self.sprite_h = self.sprite_img.height()

        # Track target (mouse) and current velocity
        self.target = (WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2)
        self.vel = [0.0, 0.0]

        # Bindings
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Enter>", lambda e: self.canvas.config(cursor=CURSOR_NORMAL))
        self.canvas.bind("<Leave>", lambda e: self.canvas.config(cursor="arrow"))
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self._cursor_hidden = False   # track the current cursor state
        self._running = True
        self.loop()

    @staticmethod
    def load_sprite_image(path):
        """Try to open the image; if missing, offer a file picker. Return PIL image or None."""
        # If the provided path doesn't exist, try to browse
        candidate = path
        if not os.path.exists(candidate):
            alt = filedialog.askopenfilename(
                title=f"'{os.path.basename(path)}' not found. Pick an image:",
                filetypes=[("PNG Images", "*.png"), ("All files", "*.*")]
            )
            if not alt:
                messagebox.showerror("Image missing", f"Could not find or open '{path}'.")
                return None
            candidate = alt
        try:
            return Image.open(candidate).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Image error", f"Failed to open image:\n{e}")
            return None

    # ---- Helpers to reduce duplication ----
    def clamp_to_canvas(self, x: float, y: float):
        half_w, half_h = self.sprite_w / 2, self.sprite_h / 2
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        nx = min(max(x, half_w), max(half_w, w - half_w))
        ny = min(max(y, half_h), max(half_h, h - half_h))
        return nx, ny

    # ---- Event handlers & loop ----
    def on_mouse_move(self, event):
        self.target = (event.x, event.y)

    # noinspection PyUnusedLocal
    def on_resize(self, event):
        x, y = self.canvas.coords(self.sprite)
        nx, ny = self.clamp_to_canvas(x, y)
        if (nx, ny) != (x, y):
            self.canvas.coords(self.sprite, nx, ny)

    # --- Pointer-over-sprite test (rectangle-based, fast & simple) ---
    def pointer_over_sprite(self) -> bool:
        if not self.canvas.find_withtag(self.sprite):
            return False
        sx, sy = self.canvas.coords(self.sprite)   # sprite center
        half_w, half_h = self.sprite_w / 2, self.sprite_h / 2
        x0 = sx - half_w - POINTER_PADDING
        y0 = sy - half_h - POINTER_PADDING
        x1 = sx + half_w + POINTER_PADDING
        y1 = sy + half_h + POINTER_PADDING

        mx, my = self.target  # latest mouse position from <Motion>
        return (x0 <= mx <= x1) and (y0 <= my <= y1)

    def loop(self):
        if not self._running or not self.canvas.find_withtag(self.sprite):
            return

        x, y = self.canvas.coords(self.sprite)
        tx, ty = self.target
        dx, dy = tx - x, ty - y

        desired_vx = dx * TARGET_EASING
        desired_vy = dy * TARGET_EASING

        speed = math.hypot(desired_vx, desired_vy)
        if speed > MAX_SPEED:
            s = MAX_SPEED / max(speed, 1e-6)
            desired_vx *= s
            desired_vy *= s

        nx, ny = self.clamp_to_canvas(x + desired_vx, y + desired_vy)
        self.canvas.coords(self.sprite, nx, ny)

        if self.pointer_over_sprite():
            if not self._cursor_hidden:
                self.canvas.config(cursor="none")
                self._cursor_hidden = True
        else:
            if self._cursor_hidden:
                self.canvas.config(cursor=CURSOR_NORMAL)
                self._cursor_hidden = False

        self.root.after(int(1000 / FPS), self.loop)

def choose_image_path(root):
    while True:
        dlg = ImageChoiceDialog(root, IMAGE_CHOICES)
        root.wait_window(dlg)
        if dlg.result is None:
            # User canceled
            return None
        # If the result exists or the user browsed, return it;
        # missing images will be handled (with browse) inside ChaserApp too.
        return dlg.result

def main():
    root = tk.Tk()
    root.title("Snoopy Chases the Mouse 🐾")
    root.configure(bg=BG_COLOR)
    root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
    root.update_idletasks()

    choice = choose_image_path(root)
    if not choice:
        root.destroy()
        return

    ChaserApp(root, choice)
    root.mainloop()

if __name__ == "__main__":
    main()

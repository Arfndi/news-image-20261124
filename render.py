"""Fresh render engine for the news-image-20261124 front page.

Stdlib only. Draws a 1024x1024 newsprint front page into a bytearray
raster and encodes it as a PNG with zlib/struct. No font files, no PIL,
no network. Every glyph below is a hand-written 5x7 bitmap drawn in
code; every pictogram is built from the primitives in this file.

Determinism: the only randomness is a fixed-seed generator used for
newsprint grain, so the same code always writes the same bytes.
"""

import random
import struct
import zlib

W, H = 1024, 1024

# ---- palette ----
PAPER = (243, 238, 226)      # warm newsprint
PAPER_DK = (232, 226, 210)   # slightly darker paper
INK = (22, 22, 24)           # near-black text
RED = (176, 32, 26)          # headline red
RED_DK = (140, 24, 20)
NAVY = (18, 38, 70)          # night sky / numbers band
NAVY_LT = (38, 64, 108)
TEAL = (14, 92, 96)          # sea green
TEAL_DK = (9, 62, 66)
SKY_NIGHT = (24, 22, 52)     # hero night sky
DUSK = (196, 94, 42)         # Sudan dusk orange
SAND = (206, 186, 148)       # map land
SEA = (196, 216, 222)        # map sea
SEA_DK = (168, 196, 206)
GOLD = (214, 164, 48)        # star / sun
GREY = (120, 118, 110)
GREY_LT = (200, 196, 184)
WHITE = (250, 248, 242)
GREEN = (28, 120, 70)        # chart bars
SMOKE = (150, 146, 136)


class Canvas:
    """A plain RGB raster with drawing primitives."""

    def __init__(self, w=W, h=H, bg=PAPER):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            return (self.px[i], self.px[i + 1], self.px[i + 2])
        return None

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            span = (x1 - x0) * 3
            self.px[base:base + span] = bytes((r, g, b)) * (x1 - x0)

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set(x, y, color)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, fill=True):
        if fill:
            for dy in range(-r, r + 1):
                half = int((r * r - dy * dy) ** 0.5)
                self.fill_rect(cx - half, cy + dy, half * 2 + 1, 1, color)
        else:
            steps = max(24, int(2 * 3.14159 * r))
            for k in range(steps):
                a = 2 * 3.14159 * k / steps
                self.set(cx + int(r * _cos(a)), cy + int(r * _sin(a)), color)

    def ellipse(self, cx, cy, rx, ry, color, fill=True):
        if fill:
            for dy in range(-ry, ry + 1):
                f = 1.0 - (dy * dy) / float(ry * ry)
                half = int(rx * (f ** 0.5)) if f > 0 else 0
                self.fill_rect(cx - half, cy + dy, half * 2 + 1, 1, color)
        else:
            steps = max(32, int(3.14159 * (rx + ry)))
            for k in range(steps):
                a = 2 * 3.14159 * k / steps
                self.set(cx + int(rx * _cos(a)), cy + int(ry * _sin(a)), color)

    def triangle(self, p0, p1, p2, color):
        pts = sorted([p0, p1, p2], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        for y in range(ay, cy + 1):
            if y < by:
                t1 = (y - ay) / float(by - ay) if by != ay else 0.0
                xa = ax + (bx - ax) * t1
                xb = ax + (cx - ax) * ((y - ay) / float(cy - ay))
            else:
                t2 = (y - by) / float(cy - by) if cy != by else 0.0
                xa = bx + (cx - bx) * t2
                xb = ax + (cx - ax) * ((y - ay) / float(cy - ay))
            x0, x1 = int(min(xa, xb)), int(max(xa, xb))
            self.fill_rect(x0, y, x1 - x0 + 1, 1, color)

    def fill_poly(self, pts, color):
        """Scanline fill for a simple polygon (list of (x, y))."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / float(y1 - y0)
                    xs.append(x0 + (x1 - x0) * t)
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa, xb = int(xs[k]), int(xs[k + 1])
                self.fill_rect(xa, y, xb - xa + 1, 1, color)

    def poly_outline(self, pts, color):
        n = len(pts)
        for i in range(n):
            self.line(pts[i][0], pts[i][1], pts[(i + 1) % n][0],
                      pts[(i + 1) % n][1], color)

    def to_png(self):
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)
            raw += self.px[y * stride:(y + 1) * stride]
        comp = zlib.compress(bytes(raw), 6)

        def chunk(tag, data):
            out = struct.pack(">I", len(data)) + tag + data
            return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", ihdr)
        png += chunk(b"IDAT", comp)
        png += chunk(b"IEND", b"")
        return png

    def save(self, path):
        with open(path, "wb") as f:
            f.write(self.to_png())


def _sin(a):
    return _SIN_TABLE[int((a % 6.283185307) / 6.283185307 * 256) % 256]


def _cos(a):
    return _SIN_TABLE[int(((a + 1.570796327) % 6.283185307) / 6.283185307 * 256) % 256]


_SIN_TABLE = [0.0] * 256
for _i in range(256):
    import math as _math
    _SIN_TABLE[_i] = _math.sin(2 * _math.pi * _i / 256.0)


# ---- 5x7 bitmap font (hand-written, one tuple of 7 rows per glyph) ----
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01111"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "–": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "—": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "•": ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    "·": ("00000", "00000", "00000", "01100", "00000", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    "~": ("00000", "00000", "01101", "10110", "00000", "00000", "00000"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
}

# Curly quotes / dashes normalize to the ASCII glyphs above.
_NORMALIZE = {
    "’": "'", "‘": "'", "“": '"', "”": '"', "‚": ",",
    "…": ".", "×": "x", "÷": "/", "°": "o", "£": "L",
}


def _norm(ch):
    return _NORMALIZE.get(ch, ch)


def char_advance(scale):
    return 6 * scale


def text_width(s, scale):
    return sum(char_advance(scale) for _ in s) - scale


def line_height(scale):
    return 8 * scale


def draw_char(cv, x, y, ch, scale, color, bold=False):
    rows = FONT.get(_norm(ch))
    if rows is None:
        rows = FONT["?"]
    for ry, row in enumerate(rows):
        for rx, bit in enumerate(row):
            if bit == "1":
                if scale == 1:
                    cv.set(x + rx, y + ry, color)
                    if bold:
                        cv.set(x + rx + 1, y + ry, color)
                else:
                    cv.fill_rect(x + rx * scale, y + ry * scale,
                                 scale, scale, color)
                    if bold:
                        cv.fill_rect(x + rx * scale + 1, y + ry * scale,
                                     scale, scale, color)


def draw_text(cv, x, y, s, scale, color, bold=False, align="left"):
    w = text_width(s, scale)
    if align == "center":
        x = x - w // 2
    elif align == "right":
        x = x - w
    cx = x
    for ch in s:
        draw_char(cv, cx, y, ch, scale, color, bold=bold)
        cx += char_advance(scale)
    return w


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w px."""
    words = s.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text_block(cv, x, y, s, scale, color, max_w, bold=False,
                    max_lines=None, align="left"):
    """Draw wrapped text; returns the y just below the last line.
    Raises ValueError if the text needs more lines than max_lines,
    so a layout overflow fails loudly instead of silently clipping."""
    lines = wrap_text(s, scale, max_w)
    if max_lines is not None and len(lines) > max_lines:
        raise ValueError("text overflow: %d lines > %d for %r"
                         % (len(lines), max_lines, s[:40]))
    lh = line_height(scale)
    for i, ln in enumerate(lines):
        if align == "center":
            draw_text(cv, x + max_w // 2, y + i * lh, ln, scale, color,
                      bold=bold, align="center")
        elif align == "right":
            draw_text(cv, x + max_w, y + i * lh, ln, scale, color,
                      bold=bold, align="right")
        else:
            draw_text(cv, x, y + i * lh, ln, scale, color, bold=bold)
    return y + len(lines) * lh


def grain(cv, seed=20261124, amount=12):
    """Seeded newsprint grain: deterministic per-pixel speckle."""
    rng = random.Random(seed)
    w, h = cv.w, cv.h
    for _ in range(w * h // 32):
        x = rng.randrange(w)
        y = rng.randrange(h)
        d = rng.randint(-amount, amount)
        i = (y * w + x) * 3
        for k in range(3):
            v = cv.px[i + k] + d
            cv.px[i + k] = 0 if v < 0 else (255 if v > 255 else v)


def double_rule(cv, x, y, w, color=INK, gap=3):
    cv.hline(x, y, w, color)
    cv.fill_rect(x, y + gap, w, 2, color)


def chip(cv, x, y, label, bg, fg=WHITE, scale=1):
    """Small filled tag chip with white caps text; returns chip width."""
    pad = 4
    w = text_width(label, scale) + pad * 2
    h = line_height(scale) + 4
    cv.fill_rect(x, y, w, h, bg)
    draw_text(cv, x + pad, y + 2, label, scale, fg, bold=True)
    return w


def star(cv, cx, cy, r, color):
    """Four-point sparkle: a diamond with a bright core."""
    cv.triangle((cx, cy - r), (cx + r // 3, cy), (cx, cy + r), color)
    cv.triangle((cx - r, cy), (cx - r // 3, cy), (cx, cy), color)
    cv.triangle((cx, cy - r), (cx + r // 3, cy), (cx, cy), color)
    cv.triangle((cx - r, cy), (cx, cy), (cx, cy + r), color)
    cv.circle(cx, cy, max(1, r // 4), WHITE, fill=True)


def number_pin(cv, cx, cy, n, r=9):
    """Red map pin: filled circle, white ring, number in the middle."""
    cv.circle(cx, cy, r, RED, fill=True)
    cv.circle(cx, cy, r, WHITE, fill=False)
    draw_text(cv, cx, cy - 4, str(n), 1, WHITE, bold=True, align="center")


def _skyline(cv, x, y, w, h, color, seed, lit=0.25):
    """Deterministic city silhouette with a few lit windows."""
    rng = random.Random(seed)
    bx = x
    while bx < x + w - 8:
        bw = rng.randint(10, 26)
        bh = rng.randint(h // 3, h)
        cv.fill_rect(bx, y + h - bh, bw, bh, color)
        for _ in range(int(bw * bh * lit / 40)):
            wx = rng.randrange(bx + 2, bx + bw - 1)
            wy = rng.randrange(y + h - bh + 2, y + h - 2)
            cv.set(wx, wy, GOLD)
        bx += bw + rng.randint(1, 4)


def art_tanker(cv, x, y, w, h):
    """Hero 1: a tanker under a warning sky in a blocked strait."""
    cv.fill_rect(x, y, w, h, SKY_NIGHT)
    rng = random.Random(11)
    for _ in range(26):
        cv.set(x + rng.randrange(w), y + rng.randrange(h // 2),
               (220, 220, 200))
    cv.circle(x + int(w * 0.82), y + int(h * 0.30), 16, GOLD, fill=True)
    cv.circle(x + int(w * 0.82), y + int(h * 0.30), 20, GOLD, fill=False)
    sea_y = y + int(h * 0.62)
    cv.fill_rect(x, sea_y, w, h - int(h * 0.62), (14, 44, 74))
    for k in range(0, w, 26):
        cv.fill_rect(x + k, sea_y + 10 + (k // 26 % 3) * 8, 14, 2,
                     (90, 140, 180))
    # tanker hull and containers
    hx, hy = x + int(w * 0.10), sea_y - 26
    cv.fill_rect(hx, hy, int(w * 0.62), 22, (12, 12, 16))
    cv.triangle((hx - 16, hy + 22), (hx, hy), (hx, hy + 22), (12, 12, 16))
    cols = [(150, 60, 40), (40, 90, 120), (180, 140, 50), (90, 110, 60)]
    for i, c in enumerate(cols):
        cv.fill_rect(hx + 8 + i * 34, hy - 16, 30, 16, c)
    cv.fill_rect(hx + int(w * 0.52), hy - 34, 12, 34, (200, 60, 40))
    for k in range(5):
        cv.circle(hx + int(w * 0.52) + 6 + k * 3,
                  hy - 38 - k * 4, 3, SMOKE, fill=True)
    # dashed red blockade line across the strait
    for k in range(0, w, 18):
        cv.fill_rect(x + k, sea_y + 26, 10, 3, RED)
    draw_text(cv, x + 8, sea_y + 34, "BLOCKADE", 1, RED, bold=True)


def art_drone_night(cv, x, y, w, h):
    """Hero 2: a drone over a night skyline, radar watching."""
    cv.fill_rect(x, y, w, h, (30, 20, 58))
    rng = random.Random(23)
    for _ in range(30):
        cv.set(x + rng.randrange(w), y + rng.randrange(h // 2),
               (210, 210, 190))
    star(cv, x + int(w * 0.80), y + int(h * 0.26), 18, GOLD)
    _skyline(cv, x, y + int(h * 0.45), w, h - int(h * 0.45),
             (10, 10, 18), 7)
    # radar arcs from the right edge
    for r in (22, 38, 54):
        cv.circle(x + w - 8, y + int(h * 0.55), r, (90, 200, 120),
                  fill=False)
    # drone: body, arms, rotors, lights
    dx, dy = x + int(w * 0.42), y + int(h * 0.30)
    cv.fill_rect(dx - 16, dy - 3, 32, 7, (200, 200, 205))
    cv.fill_rect(dx - 4, dy - 8, 8, 18, (160, 160, 165))
    for ox in (-20, 20):
        cv.fill_rect(dx + ox - 8, dy - 10, 16, 3, (220, 220, 225))
        cv.circle(dx + ox, dy - 12, 3, WHITE, fill=True)
    cv.circle(dx - 16, dy, 3, RED, fill=True)
    cv.circle(dx + 16, dy, 3, (80, 220, 100), fill=True)
    cv.line(dx + 22, dy + 4, dx + 60, dy + 22, (200, 200, 200))
    cv.line(dx + 60, dy + 22, dx + 92, dy + 12, (200, 200, 200))


def art_grid(cv, x, y, w, h):
    """Hero 3: pylons and a drone over a blacked-out city at dusk."""
    cv.fill_rect(x, y, w, h, (64, 38, 30))
    cv.fill_rect(x, y + int(h * 0.55), w, h - int(h * 0.55), (40, 22, 18))
    cv.circle(x + int(w * 0.78), y + int(h * 0.24), 14, (232, 150, 70),
              fill=True)
    # pylons with sagging lines
    for px in (int(w * 0.22), int(w * 0.58)):
        bx = x + px
        cv.fill_rect(bx - 2, y + 18, 4, int(h * 0.62), INK)
        cv.fill_rect(bx - 22, y + 26, 44, 4, INK)
        cv.fill_rect(bx - 16, y + 40, 32, 4, INK)
        cv.line(bx - 22, y + 30, bx - 10, y + 52, INK)
        cv.line(bx + 22, y + 30, bx + 10, y + 52, INK)
    cv.line(x + int(w * 0.22) - 22, y + 30, x + int(w * 0.58) - 22,
            y + 30, INK)
    cv.line(x + int(w * 0.22) - 22, y + 44, x + int(w * 0.58) - 22,
            y + 44, INK)
    # blackout city with a handful of lit windows
    _skyline(cv, x, y + int(h * 0.62), w, h - int(h * 0.62),
             (16, 12, 14), 31, lit=0.06)
    # drone + sparks near the far pylon
    dx, dy = x + int(w * 0.58), y + 16
    cv.fill_rect(dx - 10, dy - 2, 20, 5, (210, 210, 215))
    cv.circle(dx - 12, dy, 2, RED, fill=True)
    cv.circle(dx + 12, dy, 2, (80, 220, 100), fill=True)
    for sx, sy in ((dx + 26, dy + 26), (dx + 30, dy + 30),
                   (dx + 22, dy + 32)):
        cv.set(sx, sy, GOLD)
        cv.set(sx + 1, sy, GOLD)


def art_chart(cv, x, y, w, h):
    """Mini: rising bars with a red trend arrow."""
    cv.fill_rect(x, y, w, h, (226, 234, 226))
    bars = [12, 18, 15, 24, 22, 32, 30, 40]
    bw = w // len(bars)
    base = y + h - 8
    for i, v in enumerate(bars):
        cv.fill_rect(x + i * bw + 2, base - v, bw - 4, v, GREEN)
    cv.line(x + 4, base - 44, x + w - 6, base - 48, RED)
    cv.line(x + w - 6, base - 48, x + w - 14, base - 48, RED)
    cv.line(x + w - 6, base - 48, x + w - 6, base - 40, RED)
    cv.hline(x, base, w, INK)


def art_plane(cv, x, y, w, h):
    """Mini: a jet over the runway with a control tower."""
    cv.fill_rect(x, y, w, h, (158, 196, 222))
    rng = random.Random(41)
    for _ in range(4):
        cx = x + rng.randrange(w - 40)
        cy = y + rng.randrange(h // 3)
        cv.ellipse(cx, cy, 18, 6, WHITE, fill=True)
        cv.ellipse(cx + 12, cy + 3, 14, 5, WHITE, fill=True)
    # runway
    cv.fill_rect(x, y + h - 16, w, 16, (60, 60, 64))
    for k in range(0, w, 22):
        cv.fill_rect(x + k, y + h - 9, 12, 2, WHITE)
    # tower
    cv.fill_rect(x + w - 26, y + h - 52, 6, 36, (90, 90, 94))
    cv.fill_rect(x + w - 32, y + h - 60, 18, 9, (90, 90, 94))
    # plane
    px, py = x + int(w * 0.30), y + int(h * 0.42)
    cv.ellipse(px, py, 34, 7, (30, 30, 34), fill=True)
    cv.triangle((px + 26, py - 2), (px + 44, py - 2), (px + 30, py + 4),
                (30, 30, 34))
    cv.triangle((px - 6, py - 2), (px + 6, py - 16), (px + 14, py - 2),
                (30, 30, 34))
    cv.triangle((px - 6, py + 2), (px + 4, py + 12), (px + 12, py + 2),
                (30, 30, 34))


def art_island(cv, x, y, w, h):
    """Mini: a Pacific island with a palm and a flag."""
    cv.fill_rect(x, y, w, h, (52, 164, 180))
    cv.circle(x + int(w * 0.80), y + 14, 11, GOLD, fill=True)
    for k in range(0, w, 30):
        cv.fill_rect(x + k, y + h - 18 + (k // 30 % 2) * 6, 16, 2,
                     (220, 240, 244))
    # sand island
    cv.ellipse(x + int(w * 0.42), y + h - 16, int(w * 0.36), 14,
               (232, 208, 150), fill=True)
    cv.fill_rect(x + int(w * 0.42), y + h - 34, 22, 18, (120, 170, 90))
    # palm
    tx, ty = x + int(w * 0.42), y + h - 34
    cv.line(tx + 4, ty, tx + 6, ty - 22, (90, 60, 30))
    for dx, dy in ((-12, -24), (14, -26), (-8, -30), (10, -32)):
        cv.line(tx + 6, ty - 22, tx + 6 + dx, ty - 22 + dy // 2,
                (40, 120, 60))
    # flag pole + flag
    cv.vline(tx + 26, ty - 26, 26, INK)
    cv.triangle((tx + 26, ty - 26), (tx + 44, ty - 20), (tx + 26, ty - 14),
                RED)


def art_haze(cv, x, y, w, h):
    """Mini: a hazy skyline with smoking stacks and a dim sun."""
    cv.fill_rect(x, y, w, h, (186, 168, 138))
    cv.circle(x + int(w * 0.76), y + 16, 12, (214, 180, 110), fill=True)
    _skyline(cv, x, y + int(h * 0.30), w, h - int(h * 0.30),
             (70, 62, 52), 53, lit=0.05)
    # two smokestacks with plumes
    for sx in (int(w * 0.24), int(w * 0.62)):
        cv.fill_rect(x + sx, y + 8, 8, int(h * 0.45), (52, 46, 40))
        for k in range(4):
            cv.circle(x + sx + 4 + k * 4, y + 4 - k * 3, 4, SMOKE,
                      fill=True)
    # AQI arc gauge, bottom right
    gx, gy = x + w - 26, y + h - 26
    for a in range(0, 181, 6):
        import math as _m
        px = gx + int(16 * _m.cos(_m.radians(180 + a)))
        py = gy - int(16 * _m.sin(_m.radians(180 + a)))
        cv.set(px, py, RED)
    draw_text(cv, gx - 12, gy - 6, "500+", 1, RED, bold=True)


def draw_map(cv, x, y, w, h, pins):
    """Simplified world map: sea, land blobs, ocean labels, pins."""
    cv.fill_rect(x, y, w, h, SEA)
    # graticule: faint latitude + longitude ticks
    for ly in (y + h // 4, y + h // 2, y + 3 * h // 4):
        for kx in range(x, x + w, 12):
            cv.set(kx, ly, SEA_DK)
    for lx in range(x + w // 6, x + w, w // 6):
        for ky in range(y, y + h, 12):
            cv.set(lx, ky, SEA_DK)
    # landmasses: filled polygons per continent, normalized to the map
    # rect, with a darker outline so the shapes read at small size.
    polys = [
        # North America
        [(0.06, 0.30), (0.09, 0.14), (0.18, 0.09), (0.27, 0.14),
         (0.30, 0.24), (0.27, 0.33), (0.23, 0.42), (0.19, 0.38),
         (0.12, 0.38)],
        # Greenland
        [(0.34, 0.07), (0.38, 0.05), (0.40, 0.10), (0.36, 0.13)],
        # South America
        [(0.27, 0.48), (0.33, 0.45), (0.36, 0.53), (0.34, 0.66),
         (0.30, 0.76), (0.28, 0.62)],
        # Europe
        [(0.47, 0.16), (0.52, 0.12), (0.56, 0.17), (0.55, 0.24),
         (0.49, 0.23)],
        # Africa
        [(0.48, 0.35), (0.54, 0.32), (0.58, 0.37), (0.57, 0.49),
         (0.54, 0.60), (0.51, 0.52), (0.48, 0.44)],
        # Asia
        [(0.57, 0.15), (0.70, 0.08), (0.85, 0.11), (0.90, 0.20),
         (0.85, 0.28), (0.78, 0.33), (0.72, 0.38), (0.66, 0.36),
         (0.60, 0.28), (0.56, 0.20)],
        # India taper
        [(0.65, 0.34), (0.68, 0.32), (0.67, 0.42), (0.65, 0.40)],
        # SE Asia
        [(0.78, 0.33), (0.82, 0.32), (0.83, 0.39), (0.79, 0.41)],
        # Australia
        [(0.83, 0.58), (0.89, 0.56), (0.91, 0.61), (0.87, 0.66),
         (0.83, 0.63)],
        # New Zealand
        [(0.93, 0.71), (0.95, 0.70), (0.95, 0.76), (0.93, 0.77)],
    ]
    for poly in polys:
        px = [(x + int(nx * w), y + int(ny * h)) for nx, ny in poly]
        cv.fill_poly(px, SAND)
        cv.poly_outline(px, (190, 170, 130))
    # stippled land texture
    rng = random.Random(99)
    for _ in range(w * h // 220):
        px = x + rng.randrange(w)
        py = y + rng.randrange(h)
        if cv.get(px, py) == SAND:
            cv.set(px, py, (190, 170, 130))
    draw_text(cv, x + int(w * 0.06), y + int(h * 0.52), "PACIFIC", 1,
              (110, 140, 150), bold=True)
    draw_text(cv, x + int(w * 0.40), y + int(h * 0.42), "ATLANTIC", 1,
              (110, 140, 150), bold=True)
    draw_text(cv, x + int(w * 0.74), y + int(h * 0.58), "INDIAN", 1,
              (110, 140, 150), bold=True)
    draw_text(cv, x + w - 52, y + 6, "EQUATOR", 1, (110, 140, 150))
    # compass
    ccx, ccy = x + w - 18, y + h - 18
    cv.line(ccx, ccy - 10, ccx, ccy + 10, INK)
    cv.line(ccx - 10, ccy, ccx + 10, ccy, INK)
    cv.triangle((ccx, ccy - 12), (ccx - 3, ccy - 4), (ccx + 3, ccy - 4),
                RED)
    draw_text(cv, ccx - 3, ccy - 22, "N", 1, INK, bold=True)
    for nx, ny, n in pins:
        number_pin(cv, x + int(nx * w), y + int(ny * h), n)

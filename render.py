#!/usr/bin/env python3
"""Build-time renderer for the news-image-20261124 board.

Draws entry.png (1024x1024) with the Python standard library ONLY
(bytearray rasterizer + zlib/struct PNG encoder). No PIL, no network,
no downloaded assets: every pixel, including all letterforms, is drawn
in code. The runtime entrypoint (main.py) is stdlib-only and merely
copies this PNG, so two grader runs produce byte-identical output.

All 31 stories were first reported on Tuesday 24 November 2026.
The Sparta II cargo-ship story was checked and DROPPED: the strike
was Saturday 21 Nov and the ship reached St Petersburg on Monday
23 Nov -- no 24 Nov development exists.
FIX ROUND (24 Nov): hero #2 was reframed off the Dymer strike
(22 Nov, toll finalised 23 Nov) onto the fresh night-of-24-Nov
attack on western Ukraine, during which a Russian drone entered
Polish airspace and Poland activated its air defences. The
153-drone figure belongs to the previous night (22->23 Nov) and
was NOT reused.
FIX ROUND 2 (24 Nov): brief #9 (San Siro) was REMOVED entirely
after a date check: the match (Club Brugge 4-3 at San Siro,
Tresoldi hat-trick) was played 13 Oct 2026 and appeared in a
24 Nov feed only as a most-read item, not 24 Nov news. No
replacement was added: every candidate failed the 24 Nov date
check. The remaining briefs were renumbered gap-free.
"""
import math
import os
import random
import struct
import zlib

W, H = 1024, 1024
HERE = os.path.dirname(os.path.abspath(__file__))

PAPER = (246, 241, 231)
INK = (26, 26, 26)
RED = (178, 34, 28)
NAVY = (31, 58, 95)
TEAL = (15, 118, 110)
GOLD = (176, 132, 16)
GREY = (90, 88, 82)
LIGHT = (255, 255, 255)
CARD = (255, 253, 247)
RULE = (26, 26, 26)
MAPSEA = (220, 232, 239)
MAPLAND = (216, 210, 196)
MAPLINE = (160, 152, 132)
DARK = (24, 32, 58)


def stipple(cv, seed, x, y, w, h, cols, n):
    """Seeded stipple shading inside one rectangle: engraving-style
    texture in tones close to the area's own colours."""
    rnd = random.Random(seed)
    for _ in range(n):
        xx = x + rnd.randrange(w)
        yy = y + rnd.randrange(h)
        c = cols[rnd.randrange(len(cols))]
        cv.rect(xx, yy, xx + 1, yy + 1, c)


def grain(cv, seed, n, cols):
    """Deterministic paper grain: seeded 1px speckles, so re-renders
    stay byte-identical. Two near-paper tones, never over text."""
    rnd = random.Random(seed)
    for _ in range(n):
        xx = rnd.randrange(cv.w)
        yy = rnd.randrange(cv.h)
        c = cols[rnd.randrange(len(cols))]
        cv.rect(xx, yy, xx + 1, yy + 1, c)


# ---------------------------------------------------------------- canvas
class Canvas:
    """Minimal RGB rasterizer on a flat bytearray."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def rect(self, x0, y0, x1, y1, c):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def line(self, x0, y0, x1, y1, w, c):
        dx, dy = x1 - x0, y1 - y0
        n = max(abs(dx), abs(dy), 1)
        r = w // 2
        for i in range(n + 1):
            x = int(round(x0 + dx * i / n))
            y = int(round(y0 + dy * i / n))
            self.rect(x - r, y - r, x + r + 1, y + r + 1, c)

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            half = int(math.sqrt(max(0, r * r - dy * dy)))
            self.rect(cx - half, cy + dy, cx + half + 1, cy + dy + 1, c)

    def ellipse(self, cx, cy, rx, ry, w, c):
        pts = []
        for k in range(49):
            a = 2 * math.pi * k / 48
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        for i in range(48):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            self.line(int(x1), int(y1), int(x2), int(y2), w, c)

    def poly(self, pts, c):
        pts = [(int(x), int(y)) for x, y in pts]
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h - 1, max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) + 1, y + 1, c)


def save_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- stroke font
# Glyphs as line segments on a 5x7 grid (x 0..4, y 0..6, top-left origin).
# A clean technical stencil face: every letterform is drawn in code.
def _glyph(spec):
    out = []
    for a, b, c, d in spec:
        out.append((a, b, c, d))
    return out


_S = [(4, 1, 3, 0), (3, 0, 1, 0), (1, 0, 0, 1), (0, 1, 0, 2), (0, 2, 1, 3),
      (1, 3, 3, 3), (3, 3, 4, 4), (4, 4, 4, 5), (4, 5, 3, 6), (3, 6, 1, 6),
      (1, 6, 0, 5)]
_O = [(1, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 5), (4, 5, 3, 6), (3, 6, 1, 6),
      (1, 6, 0, 5), (0, 5, 0, 1), (0, 1, 1, 0)]
_P = [(0, 0, 0, 6), (0, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 2), (4, 2, 3, 3),
      (3, 3, 0, 3)]

FONT = {
    "A": _glyph([(0, 6, 2, 0), (2, 0, 4, 6), (1, 4, 3, 4)]),
    "B": _glyph([(0, 0, 0, 6), (0, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 2),
                 (4, 2, 3, 3), (3, 3, 0, 3), (3, 3, 4, 4), (4, 4, 4, 5),
                 (4, 5, 3, 6), (3, 6, 0, 6)]),
    "C": _glyph([(4, 1, 3, 0), (3, 0, 1, 0), (1, 0, 0, 1), (0, 1, 0, 5),
                 (0, 5, 1, 6), (1, 6, 3, 6), (3, 6, 4, 5)]),
    "D": _glyph([(0, 0, 0, 6), (0, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 5),
                 (4, 5, 3, 6), (3, 6, 0, 6)]),
    "E": _glyph([(0, 0, 0, 6), (0, 0, 4, 0), (0, 3, 3, 3), (0, 6, 4, 6)]),
    "F": _glyph([(0, 0, 0, 6), (0, 0, 4, 0), (0, 3, 3, 3)]),
    "G": _glyph([(4, 1, 3, 0), (3, 0, 1, 0), (1, 0, 0, 1), (0, 1, 0, 5),
                 (0, 5, 1, 6), (1, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 3),
                 (4, 3, 2, 3)]),
    "H": _glyph([(0, 0, 0, 6), (4, 0, 4, 6), (0, 3, 4, 3)]),
    "I": _glyph([(1, 0, 3, 0), (2, 0, 2, 6), (1, 6, 3, 6)]),
    "J": _glyph([(4, 0, 4, 5), (4, 5, 3, 6), (3, 6, 1, 6), (1, 6, 0, 5),
                 (0, 5, 0, 4)]),
    "K": _glyph([(0, 0, 0, 6), (4, 0, 0, 3), (2, 4, 4, 6)]),
    "L": _glyph([(0, 0, 0, 6), (0, 6, 4, 6)]),
    "M": _glyph([(0, 6, 0, 0), (0, 0, 2, 3), (2, 3, 4, 0), (4, 0, 4, 6)]),
    "N": _glyph([(0, 6, 0, 0), (0, 0, 4, 6), (4, 6, 4, 0)]),
    "O": _glyph(_O),
    "P": _glyph(_P),
    "Q": _glyph(_O + [(3, 4, 4, 6)]),
    "R": _glyph(_P + [(2, 3, 4, 6)]),
    "S": _glyph(_S),
    "T": _glyph([(0, 0, 4, 0), (2, 0, 2, 6)]),
    "U": _glyph([(0, 0, 0, 5), (0, 5, 1, 6), (1, 6, 3, 6), (3, 6, 4, 5),
                 (4, 5, 4, 0)]),
    "V": _glyph([(0, 0, 2, 6), (2, 6, 4, 0)]),
    "W": _glyph([(0, 0, 1, 6), (1, 6, 2, 3), (2, 3, 3, 6), (3, 6, 4, 0)]),
    "X": _glyph([(0, 0, 4, 6), (4, 0, 0, 6)]),
    "Y": _glyph([(0, 0, 2, 3), (4, 0, 2, 3), (2, 3, 2, 6)]),
    "Z": _glyph([(0, 0, 4, 0), (4, 0, 0, 6), (0, 6, 4, 6)]),
    "0": _glyph(_O),
    "1": _glyph([(1, 1, 2, 0), (2, 0, 2, 6), (0, 6, 4, 6)]),
    "2": _glyph([(0, 1, 1, 0), (1, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 2),
                 (4, 2, 0, 6), (0, 6, 4, 6)]),
    "3": _glyph([(0, 0, 4, 0), (4, 0, 4, 6), (0, 6, 4, 6), (1, 3, 4, 3)]),
    "4": _glyph([(0, 0, 0, 3), (0, 3, 4, 3), (3, 0, 3, 6)]),
    "5": _glyph([(4, 0, 0, 0), (0, 0, 0, 3), (0, 3, 3, 3), (3, 3, 4, 4),
                 (4, 4, 4, 5), (4, 5, 3, 6), (3, 6, 0, 6)]),
    "6": _glyph([(3, 0, 1, 0), (1, 0, 0, 1), (0, 1, 0, 5), (0, 5, 1, 6),
                 (1, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 4), (4, 4, 3, 3),
                 (3, 3, 1, 3), (1, 3, 0, 4)]),
    "7": _glyph([(0, 0, 4, 0), (4, 0, 1, 6)]),
    "8": _glyph(_O + [(0, 3, 4, 3)]),
    "9": _glyph([(0, 5, 1, 6), (1, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 1),
                 (4, 1, 3, 0), (3, 0, 1, 0), (1, 0, 0, 1), (0, 1, 0, 2),
                 (0, 2, 1, 3), (1, 3, 3, 3), (3, 3, 4, 2)]),
    ".": _glyph([(2, 5, 2, 6)]),
    ",": _glyph([(2, 5, 2, 6), (2, 6, 1, 7)]),
    ":": _glyph([(2, 1, 2, 2), (2, 4, 2, 5)]),
    ";": _glyph([(2, 1, 2, 2), (2, 4, 2, 6), (2, 6, 1, 7)]),
    "!": _glyph([(2, 0, 2, 4), (2, 5, 2, 6)]),
    "?": _glyph([(1, 1, 2, 0), (2, 0, 3, 0), (3, 0, 4, 1), (4, 1, 4, 2),
                (4, 2, 3, 3), (3, 3, 2, 3), (2, 3, 2, 4), (2, 5, 2, 6)]),
    "-": _glyph([(0, 3, 4, 3)]),
    "'": _glyph([(2, 0, 2, 2)]),
    '"': _glyph([(1, 0, 1, 2), (3, 0, 3, 2)]),
    "(": _glyph([(3, 0, 2, 1), (2, 1, 2, 5), (2, 5, 3, 6)]),
    ")": _glyph([(1, 0, 2, 1), (2, 1, 2, 5), (2, 5, 1, 6)]),
    "/": _glyph([(4, 0, 0, 6)]),
    "%": _glyph([(4, 0, 0, 6), (0, 1, 1, 1), (1, 1, 1, 2), (1, 2, 0, 2),
                (0, 2, 0, 1), (3, 4, 4, 4), (4, 4, 4, 5), (4, 5, 3, 5),
                (3, 5, 3, 4)]),
    "$": _glyph(_S + [(2, 0, 2, 6)]),
    "+": _glyph([(2, 1, 2, 5), (0, 3, 4, 3)]),
    "=": _glyph([(0, 2, 4, 2), (0, 4, 4, 4)]),
    "·": _glyph([(2, 3, 2, 4)]),
    "X": _glyph([(0, 0, 4, 6), (4, 0, 0, 6)]),
}

_ACCENTS = str.maketrans(
    "àáâäèéêëìíîïòóôöùúûüýÿñçÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜÝŸÑÇ",
    "aaaaeeeeiiiioooouuuuyyncAAAAEEEEIIIIOOOOUUUUYYNC")


def sanitize(s):
    s = s.upper()  # FONT holds capitals only: upper-case BEFORE filtering,
    # or every lowercase letter is replaced by a space.
    s = s.translate(_ACCENTS)
    s = (s.replace("’", "'").replace("‘", "'").replace("“", '"')
          .replace("”", '"').replace("—", "-").replace("–", "-")
          .replace("•", ".").replace("…", "..."))
    return "".join(ch if (ch in FONT or ch == " ") else " " for ch in s)


def char_w(size):
    return 6 * size / 7.0


def text_w(s, size):
    return len(sanitize(s).upper()) * char_w(size)


def draw_text(cv, x, y, size, s, color, align="l"):
    """Draw text; y is the top of the cap height. Returns end x."""
    s = sanitize(s).upper()
    unit = size / 7.0
    th = max(1, int(round(unit * 0.8)))
    if align == "c":
        x -= text_w(s, size) / 2
    elif align == "r":
        x -= text_w(s, size)
    cx = x
    for ch in s:
        if ch != " ":
            for x1, y1, x2, y2 in FONT.get(ch, ()):
                cv.line(int(round(cx + x1 * unit)), int(round(y + y1 * unit)),
                        int(round(cx + x2 * unit)), int(round(y + y2 * unit)),
                        th, color)
        cx += 6 * unit
    return cx


def wrap(s, size, max_w):
    max_chars = max(1, int(max_w // char_w(size)))
    words = sanitize(s).upper().split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) <= max_chars:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(cv, x, y, lines, size, color, leading=None):
    lh = leading or int(size * 1.35)
    for ln in lines:
        draw_text(cv, x, y, size, ln, color)
        y += lh
    return y

# ---------------------------------------------------------------- pictograms
def pic_blockade(cv, x, y, w, h):
    """Lead illustration: a tanker under a red warning sky."""
    cv.rect(x, y, x + w, y + h, DARK)
    # dusk sky bands: deep navy to a burnt-orange horizon
    cv.rect(x, y + 26, x + w, y + 44, (38, 48, 84))
    cv.rect(x, y + 44, x + w, y + 58, (74, 52, 70))
    # stippled dusk shading across the sky
    stipple(cv, 11, x, y, w, 52, [(32, 40, 68), (20, 28, 52)], 2600)
    # clouds: pale discs drifting across the upper sky
    for cx, cy, r in ((x + 30, y + 12, 9), (x + 46, y + 16, 7),
                      (x + 120, y + 10, 8), (x + 134, y + 15, 6),
                      (x + 190, y + 20, 7)):
        cv.disc(cx, cy, r, (120, 128, 160))
    # gulls: small dark chevrons high in the sky
    for gx, gy in ((x + 70, y + 30), (x + 84, y + 26), (x + 160, y + 34)):
        cv.line(gx - 5, gy, gx, gy - 3, 1, (200, 200, 210))
        cv.line(gx, gy - 3, gx + 5, gy, 1, (200, 200, 210))
    # warning sun / blast
    cx, cy, r = x + w - 52, y + 30, 22
    pts = []
    for k in range(16):
        a = math.pi * k / 8
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    cv.poly(pts, (255, 170, 40))
    cv.disc(cx, cy, 7, (255, 240, 180))
    # distant second ship on the horizon, small and dark
    sx, sy = x + 210, y + h - 44
    cv.poly([(sx, sy), (sx + 52, sy), (sx + 58, sy + 8), (sx + 4, sy + 8)],
            (30, 40, 66))
    cv.rect(sx + 30, sy - 8, sx + 42, sy, (30, 40, 66))
    # port crane silhouette at the far left
    cv.line(x + 8, y + h - 30, x + 8, y + 22, 3, (20, 26, 48))
    cv.line(x + 8, y + 22, x + 44, y + 34, 3, (20, 26, 48))
    cv.line(x + 44, y + 34, x + 44, y + 44, 2, (20, 26, 48))
    # sea
    cv.rect(x, y + h - 30, x + w, y + h, (16, 42, 74))
    for yy in (y + h - 22, y + h - 12):
        for xx in range(x + 8, x + w - 8, 26):
            cv.line(xx, yy, xx + 14, yy, 2, (120, 170, 220))
    # tanker hull
    hx, hy = x + 18, y + h - 52
    cv.poly([(hx, hy), (hx + 150, hy), (hx + 168, hy + 14), (hx + 160, hy + 26),
             (hx + 8, hy + 26), (hx - 4, hy + 12)], (12, 18, 38))
    # hull shading: rust-red waterline stripe and pale deck edge
    cv.line(hx + 2, hy + 20, hx + 162, hy + 20, 2, (150, 60, 40))
    cv.line(hx, hy, hx + 150, hy, 2, (90, 100, 120))
    # stacked containers in muted red, ochre and grey
    for i, col in enumerate(((150, 60, 40), (176, 132, 16), (120, 120, 115),
                            (150, 60, 40))):
        cv.rect(hx + 22 + i * 20, hy - 26, hx + 40 + i * 20, hy - 14, col)
    cv.rect(hx + 96, hy - 22, hx + 128, hy, (12, 18, 38))
    cv.rect(hx + 130, hy - 22, hx + 138, hy, (178, 34, 28))
    # funnel smoke: rising grey discs
    for fx, fy, fr in ((hx + 134, hy - 30, 5), (hx + 138, hy - 38, 6),
                       (hx + 132, hy - 46, 4)):
        cv.disc(fx, fy, fr, (150, 150, 150))
    cv.rect(hx + 20, hy - 14, hx + 60, hy, (200, 200, 200))
    # hull reflection: broken dark dashes under the ship
    for rx in range(hx + 6, hx + 160, 22):
        cv.line(rx, y + h - 4, rx + 12, y + h - 4, 2, (10, 26, 48))
    # sun glitter: gold dashes on the water beneath the warning sun
    for gx in range(x + w - 78, x + w - 28, 12):
        cv.line(gx, y + h - 26, gx + 8, y + h - 26, 2, (255, 170, 40))
        cv.line(gx + 4, y + h - 18, gx + 10, y + h - 18, 2, (220, 140, 40))
    # blockade line: red dashed barrier across the sea lane
    for xx in range(x + 10, x + w - 10, 18):
        cv.line(xx, y + h - 34, xx + 9, y + h - 34, 3, RED)


def pic_blast(cv, x, y, w, h):
    """Kyiv strikes: blast star over a dark skyline."""
    cv.rect(x, y, x + w, y + h, (58, 38, 66))
    # stippled night shading across the sky
    stipple(cv, 22, x, y, w, 44, [(70, 48, 78), (48, 30, 56)], 2600)
    # night sky: stars and a pale moon
    for sx, sy in ((x + 24, y + 10), (x + 52, y + 18), (x + 150, y + 8),
                   (x + 180, y + 16), (x + 210, y + 10), (x + 120, y + 12)):
        cv.disc(sx, sy, 1, (220, 210, 200))
    cv.disc(x + 130, y + 16, 8, (230, 225, 200))
    cv.disc(x + 127, y + 14, 7, (58, 38, 66))
    # searchlight beams sweeping up from the rooftops
    cv.line(x + 60, y + h - 30, x + 110, y + 6, 1, (200, 190, 150))
    cv.line(x + 250, y + h - 30, x + 210, y + 8, 1, (200, 190, 150))
    # smoke plume rising left of the blast
    for sx, sy, sr in ((x + 150, y + 30, 10), (x + 142, y + 18, 12),
                       (x + 152, y + 8, 9)):
        cv.disc(sx, sy, sr, (90, 78, 88))
    cv.rect(x, y + h - 30, x + w, y + h, (30, 20, 36))
    for bx, bw, bh in ((6, 30, 44), (42, 20, 62), (68, 34, 38), (108, 24, 54),
                       (138, 30, 46), (174, 26, 58), (206, 30, 40),
                       (242, 24, 50), (272, 30, 44)):
        cv.rect(x + bx, y + h - bh, x + bx + bw, y + h, (18, 12, 22))
    # lit windows: small gold squares scattered over the skyline
    for wx, wy in ((x + 12, y + h - 36), (x + 48, y + h - 52),
                   (x + 74, y + h - 28), (x + 114, y + h - 44),
                   (x + 144, y + h - 36), (x + 180, y + h - 48),
                   (x + 212, y + h - 32), (x + 248, y + h - 40),
                   (x + 278, y + h - 34), (x + 20, y + h - 20)):
        cv.rect(wx, wy, wx + 3, wy + 4, (255, 200, 90))
    # rooftop antennas on the tallest blocks
    cv.line(x + 52, y + h - 62, x + 52, y + h - 72, 2, (18, 12, 22))
    cv.line(x + 187, y + h - 58, x + 187, y + h - 68, 2, (18, 12, 22))
    # fire glow at the foot of one block: orange base, flame tongues
    cv.rect(x + 108, y + h - 12, x + 132, y + h, (255, 120, 30))
    cv.poly([(x + 112, y + h - 12), (x + 118, y + h - 26),
             (x + 124, y + h - 12)], (255, 200, 90))
    cv.poly([(x + 122, y + h - 12), (x + 128, y + h - 22),
             (x + 132, y + h - 12)], (255, 170, 40))
    cx, cy = x + w - 62, y + 34
    for r, col in ((34, (255, 170, 40)), (22, (255, 210, 90)),
                   (12, (255, 240, 180))):
        pts = []
        for k in range(12):
            a = math.pi * k / 6
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        cv.poly(pts, col)
    # embers drifting down from the blast
    for ex, ey in ((x + 220, y + 60), (x + 240, y + 68), (x + 200, y + 72),
                   (x + 260, y + 56)):
        cv.disc(ex, ey, 2, (255, 170, 40))
    for sx, sy, sr in ((x + 40, y + 22, 12), (x + 70, y + 14, 9),
                       (x + 100, y + 26, 10)):
        cv.disc(sx, sy, sr, (120, 100, 120))


def pic_derrick(cv, x, y, w, h):
    """Norway: an oil derrick under a court gavel sky."""
    cv.rect(x, y, x + w, y + h, (13, 84, 76))
    # stippled sea-green shading across the sky
    stipple(cv, 33, x, y, w, 44, [(20, 95, 88), (10, 72, 64)], 2600)
    # pale clouds and gulls over the rig
    for cx, cy, r in ((x + 24, y + 10, 8), (x + 38, y + 14, 6),
                      (x + 250, y + 12, 9), (x + 264, y + 17, 6)):
        cv.disc(cx, cy, r, (180, 210, 200))
    for gx, gy in ((x + 90, y + 16), (x + 104, y + 12), (x + 210, y + 22)):
        cv.line(gx - 4, gy, gx, gy - 3, 1, (220, 230, 225))
        cv.line(gx, gy - 3, gx + 4, gy, 1, (220, 230, 225))
    cv.rect(x, y + h - 24, x + w, y + h, (8, 50, 46))
    # sea swell: two pale wave lines
    for yy in (y + h - 16, y + h - 8):
        for xx in range(x + 6, x + w - 6, 24):
            cv.line(xx, yy, xx + 12, yy, 2, (90, 160, 150))
    # platform deck with railing posts
    bx, by = x + 40, y + h - 24
    cv.rect(bx - 14, by - 6, bx + 82, by, (60, 60, 58))
    for px in range(bx - 10, bx + 80, 14):
        cv.line(px, by - 14, px, by - 6, 2, (220, 220, 210))
    cv.line(bx - 10, by - 14, bx + 78, by - 14, 2, (220, 220, 210))
    # derrick frame
    cv.line(bx, by, bx + 34, y + 8, 4, (220, 220, 210))
    cv.line(bx + 68, by, bx + 34, y + 8, 4, (220, 220, 210))
    cv.line(bx + 10, by - 18, bx + 58, by - 18, 3, (220, 220, 210))
    cv.line(bx + 18, by - 40, bx + 50, by - 40, 3, (220, 220, 210))
    cv.line(bx + 34, y + 8, bx + 34, by, 3, (220, 220, 210))
    # cross-bracing diagonals inside the frame
    cv.line(bx + 6, by - 8, bx + 28, by - 34, 2, (200, 200, 190))
    cv.line(bx + 62, by - 8, bx + 40, by - 34, 2, (200, 200, 190))
    # crane arm reaching out from the derrick top
    cv.line(bx + 34, y + 8, bx + 96, y + 22, 3, (220, 220, 210))
    cv.line(bx + 96, y + 22, bx + 96, y + 34, 2, (220, 220, 210))
    cv.rect(bx + 90, y + 34, bx + 102, y + 42, (176, 132, 16))
    # lifeboat slung under the deck, ochre
    cv.poly([(bx + 8, by + 2), (bx + 30, by + 2), (bx + 26, by + 10),
             (bx + 12, by + 10)], (176, 132, 16))
    # supply boat crossing the lower right sea
    sx, sy = x + w - 78, y + h - 14
    cv.poly([(sx, sy), (sx + 52, sy), (sx + 58, sy + 7), (sx + 4, sy + 7)],
            (220, 220, 210))
    cv.rect(sx + 30, sy - 8, sx + 42, sy, (220, 220, 210))
    cv.line(sx + 8, sy + 10, sx + 56, sy + 10, 1, (140, 180, 170))
    # red X over a gold oil drop, centre-right
    dx, dy = x + w - 88, y + 38
    pts = [(dx, dy - 20), (dx + 16, dy + 6), (dx + 9, dy + 14), (dx, dy + 14),
           (dx - 9, dy + 14), (dx - 16, dy + 6)]
    cv.poly(pts, GOLD)
    cv.disc(dx - 4, dy - 8, 3, (230, 190, 80))
    cv.line(dx - 24, dy - 30, dx + 24, dy + 24, 5, RED)
    cv.line(dx + 24, dy - 30, dx - 24, dy + 24, 5, RED)


def pic_bars(cv, x, y, w, h, col=TEAL):
    cv.rect(x, y, x + w, y + h, CARD)
    # faint horizontal gridlines
    for gy in (y + 12, y + 24, y + 36):
        cv.line(x + 6, gy, x + w - 6, gy, 1, (225, 220, 208))
    for bx, frac in ((10, 0.30), (30, 0.50), (50, 0.40), (70, 0.68),
                     (90, 0.55), (110, 0.85), (130, 0.72), (150, 0.95),
                     (170, 0.80), (190, 0.98)):
        bh = int(h * frac)
        cv.rect(x + bx, y + h - 4 - bh, x + bx + 13, y + h - 4, col)
        # pale cap on each bar top and a value dot above the tallest
        cv.rect(x + bx, y + h - 4 - bh, x + bx + 13, y + h - 2 - bh,
                (255, 255, 255))
    cv.disc(x + 196, y + h - 4 - int(h * 0.98) - 4, 2, RED)
    cv.line(x + 6, y + h - 4, x + w - 6, y + h - 4, 2, INK)
    # rising trend arrow over the bars
    cv.line(x + 12, y + h - 14, x + w - 20, y + 8, 2, RED)
    cv.line(x + w - 20, y + 8, x + w - 30, y + 8, 2, RED)
    cv.line(x + w - 20, y + 8, x + w - 20, y + 18, 2, RED)


def pic_plane(cv, x, y, w, h):
    cv.rect(x, y, x + w, y + h, (16, 42, 74))
    stipple(cv, 44, x, y, w, h, [(24, 52, 86), (12, 34, 62)], 1000)
    # layered clouds: pale discs at three depths
    for cx, cy, r in ((x + 30, y + 12, 9), (x + 48, y + 16, 6),
                      (x + 150, y + 38, 8), (x + 166, y + 42, 5),
                      (x + 200, y + 10, 7)):
        cv.disc(cx, cy, r, (140, 170, 200))
    cx, cy = x + w // 2, y + h // 2
    # fuselage, nose cone, tail fin
    cv.line(cx - 80, cy, cx + 72, cy, 5, LIGHT)
    cv.poly([(cx + 72, cy - 7), (cx + 92, cy), (cx + 72, cy + 7)], LIGHT)
    cv.line(cx - 72, cy, cx - 58, cy - 16, 4, LIGHT)
    # window dots along the fuselage
    for wx in range(cx - 60, cx + 66, 12):
        cv.disc(wx, cy - 1, 1, (16, 42, 74))
    # red cheatline stripe under the windows
    cv.line(cx - 70, cy + 4, cx + 70, cy + 4, 1, RED)
    # swept wings: one up, one down, both trailing back
    cv.line(cx - 6, cy - 2, cx + 34, cy - 20, 4, LIGHT)
    cv.line(cx - 6, cy + 2, cx + 34, cy + 18, 4, LIGHT)
    # contrail trailing behind the tail
    for tx in range(cx - 84, x + 4, -8):
        cv.disc(tx, cy + 2, 1, (200, 210, 230))
    for sx, sy in ((30, 10), (90, 8), (150, 14), (200, 8)):
        cv.disc(x + sx, y + sy, 2, (200, 210, 230))


def pic_bolt(cv, x, y, w, h):
    cv.rect(x, y, x + w, y + h, (38, 38, 44))
    stipple(cv, 55, x, y, w, h, [(48, 48, 56), (30, 30, 36)], 1000)
    # pylon silhouettes left and right, with cross-arms
    for px in (x + 22, x + w - 26):
        cv.line(px, y + h - 6, px, y + 12, 3, (18, 18, 22))
        cv.line(px - 10, y + 16, px + 10, y + 16, 2, (18, 18, 22))
        cv.line(px - 7, y + 24, px + 7, y + 24, 2, (18, 18, 22))
    # sagging power lines between the pylons and the bolt
    cv.line(x + 22, y + 16, x + w // 2 - 14, y + 22, 1, (120, 120, 120))
    cv.line(x + w // 2 + 14, y + 22, x + w - 26, y + 16, 1, (120, 120, 120))
    cx, cy = x + w // 2, y + h // 2
    cv.poly([(cx + 8, cy - 22), (cx - 14, cy + 2), (cx - 2, cy + 2),
             (cx - 8, cy + 22), (cx + 14, cy - 2), (cx + 2, cy - 2)],
            (255, 220, 90))
    # spark ticks around the bolt
    for sx, sy in ((cx - 26, cy - 12), (cx + 26, cy - 8), (cx - 24, cy + 14),
                   (cx + 24, cy + 16)):
        cv.line(sx - 3, sy, sx + 3, sy, 1, (255, 220, 90))
        cv.line(sx, sy - 3, sx, sy + 3, 1, (255, 220, 90))
    cv.line(x + 10, y + h - 6, x + w - 10, y + h - 6, 2, (120, 120, 120))


def pic_smog(cv, x, y, w, h):
    cv.rect(x, y, x + w, y + h, (90, 88, 82))
    stipple(cv, 66, x, y, w, h, [(100, 98, 92), (80, 78, 72)], 1000)
    cv.disc(x + w - 44, y + 16, 12, (220, 180, 90))
    # haze ring around the low sun
    cv.ellipse(x + w - 44, y + 16, 18, 18, 1, (200, 170, 110))
    for bx, bw, bh in ((8, 26, 26), (40, 18, 36), (64, 30, 20),
                       (100, 22, 32), (128, 26, 24), (160, 20, 30)):
        cv.rect(x + bx, y + h - bh, x + bx + bw, y + h, (50, 48, 44))
    # lit windows in the tower blocks
    for wx, wy in ((x + 14, y + h - 20), (x + 46, y + h - 30),
                   (x + 70, y + h - 14), (x + 106, y + h - 26),
                   (x + 134, y + h - 18), (x + 166, y + h - 24)):
        cv.rect(wx, wy, wx + 3, wy + 3, (220, 180, 90))
    # chimney stacks with drifting smoke
    cv.rect(x + 188, y + h - 40, x + 196, y + h, (40, 38, 36))
    for sx, sy, sr in ((x + 192, y + h - 46, 4), (x + 198, y + h - 52, 5),
                       (x + 192, y + h - 58, 4)):
        cv.disc(sx, sy, sr, (150, 148, 140))
    # two thin haze bands, not full-width stripes
    for sy in (y + 14, y + 26):
        cv.line(x + 14, sy, x + 92, sy, 2, (170, 168, 158))


# ---------------------------------------------------------------- world map
# Simplified continent outlines (lon/lat), as used by the 20261121 board.
NA = [(-168, 66), (-155, 71), (-140, 70), (-125, 71), (-118, 70), (-110, 68),
      (-100, 69), (-90, 69), (-85, 66), (-80, 62), (-77, 62), (-70, 58),
      (-65, 60), (-60, 55), (-55, 52), (-60, 47), (-65, 44), (-70, 42),
      (-75, 36), (-80, 32), (-81, 26), (-84, 30), (-90, 21), (-97, 26),
      (-105, 22), (-110, 29), (-117, 33), (-125, 40), (-125, 49), (-130, 56),
      (-135, 60), (-145, 60), (-155, 58), (-162, 58), (-168, 66)]
GL = [(-55, 60), (-45, 60), (-40, 65), (-30, 68), (-22, 70), (-25, 76),
      (-35, 80), (-50, 80), (-58, 76), (-60, 70), (-55, 60)]
SA = [(-80, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
      (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-70, -52), (-66, -55),
      (-65, -45), (-58, -38), (-48, -28), (-41, -23), (-35, -8), (-40, -3),
      (-50, 0), (-55, 5), (-62, 9), (-70, 11), (-77, 8), (-80, 9)]
EU = [(-10, 36), (-9, 43), (-2, 48), (-5, 50), (0, 51), (3, 53), (8, 57),
      (10, 59), (5, 60), (12, 61), (18, 62), (18, 69), (25, 71), (30, 70),
      (28, 65), (23, 60), (21, 56), (18, 55), (12, 55), (8, 57), (8, 54),
      (3, 52), (0, 49), (-2, 44), (-2, 37), (0, 39), (3, 42), (7, 44),
      (10, 44), (14, 45), (19, 42), (23, 40), (26, 38), (30, 36), (28, 41),
      (23, 40), (19, 45), (15, 44), (12, 44), (8, 44), (3, 43), (-1, 38),
      (-6, 36), (-10, 36)]
AF = [(-17, 15), (-16, 20), (-15, 27), (-10, 31), (-5, 35), (0, 36),
      (10, 37), (11, 34), (20, 32), (25, 32), (32, 31), (35, 28),
      (34, 27), (37, 22), (39, 18), (43, 12), (48, 11), (51, 12),
      (46, 5), (41, 0), (40, -5), (39, -12), (36, -18), (33, -26),
      (28, -33), (20, -35), (17, -32), (15, -27), (13, -18), (12, -6),
      (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12), (-17, 15)]
AS = [(30, 36), (36, 36), (36, 33), (40, 36), (44, 39), (48, 39), (50, 37),
      (54, 37), (57, 27), (58, 25), (61, 25), (66, 25), (70, 24), (72, 20),
      (76, 10), (80, 8), (80, 13), (85, 19), (89, 22), (91, 22), (94, 17),
      (97, 16), (100, 8), (103, 2), (104, 9), (106, 11), (109, 13),
      (108, 18), (105, 20), (108, 21), (110, 20), (113, 22), (117, 23),
      (120, 25), (122, 28), (121, 32), (120, 35), (122, 37), (124, 40),
      (127, 40), (130, 42), (132, 43), (135, 44), (138, 46), (140, 47),
      (142, 50), (142, 53), (140, 56), (138, 59), (136, 60), (142, 60),
      (150, 60), (156, 59), (158, 55), (162, 56), (163, 60), (170, 66),
      (178, 65), (170, 70), (160, 70), (150, 72), (140, 73), (130, 72),
      (120, 73), (110, 74), (105, 77), (100, 76), (95, 76), (90, 75),
      (85, 74), (80, 73), (75, 72), (70, 72), (68, 70), (65, 69),
      (60, 69), (55, 68), (50, 68), (45, 68), (40, 67), (35, 66),
      (32, 70), (30, 70), (28, 68), (32, 66), (36, 64), (40, 62),
      (42, 58), (40, 52), (38, 48), (35, 45), (32, 42), (30, 36)]
AU = [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33), (129, -32),
      (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (147, -39),
      (150, -37), (153, -32), (153, -27), (150, -23), (146, -19), (142, -15),
      (142, -11), (140, -17), (136, -15), (135, -12), (132, -11), (130, -13),
      (126, -14), (122, -17), (118, -20), (113, -22)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 57), (1, 53), (-1, 51)]
JP = [(130, 31), (133, 34), (136, 35), (139, 37), (141, 40), (142, 43),
      (144, 44), (141, 42), (139, 38), (136, 36), (133, 34)]
NZ = [(167, -45), (170, -43), (174, -41), (176, -38), (174, -36), (172, -40),
      (168, -44), (167, -45)]
ID = [(95, 5), (98, 3), (100, 0), (104, -3), (108, -6), (112, -7),
      (116, -8), (120, -9), (124, -9), (128, -6), (132, -4), (136, -2),
      (140, -3), (138, -6), (132, -7), (126, -8), (120, -9), (114, -8),
      (110, -7), (106, -6), (102, -4), (98, 0), (95, 5)]

PINS = [(1, 56.5, 26.5), (2, 30.5, 50.4), (3, 10.7, 59.9), (4, -87.6, 41.9),
        (5, 32.5, 15.6), (6, 74.3, 31.5), (7, 174.8, -41.3), (8, -77.0, 38.9)]
PIN_KEY = ("1 HORMUZ   2 KYIV   3 OSLO   4 CHICAGO   5 KHARTOUM   "
           "6 LAHORE   7 WELLINGTON   8 WASHINGTON")


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, x + w, y + h, MAPSEA)
    # stippled sea texture, drawn before the continents cover it
    rnd = random.Random(4242)
    for _ in range(15000):
        xx = x + rnd.randrange(w)
        yy = y + rnd.randrange(h)
        c = (210, 226, 234) if rnd.random() < 0.5 else (228, 238, 244)
        cv.rect(xx, yy, xx + 1, yy + 1, c)
    cv.rect(x, y, x + w, y + 1, MAPLINE)
    cv.rect(x, y + h - 1, x + w, y + h, MAPLINE)
    lon0, lon1, lat0, lat1 = -170.0, 190.0, -58.0, 84.0

    def px(lon, lat):
        return (x + (lon - lon0) / (lon1 - lon0) * w,
                y + (lat1 - lat) / (lat1 - lat0) * h)

    for lon in range(-150, 181, 30):
        gx, _ = px(lon, 0)
        cv.line(int(gx), y, int(gx), y + h, 1, (205, 220, 230))
    for lon in range(-165, 181, 30):
        gx, _ = px(lon, 0)
        cv.line(int(gx), y, int(gx), y + h, 1, (214, 228, 236))
    for lat in (-30, 0, 30, 60):
        _, gy = px(0, lat)
        cv.line(x, int(gy), x + w, int(gy), 1, (205, 220, 230))
    # ocean labels and an equator tag, in muted sea-blue
    draw_text(cv, x + 352, y + 46, 9, "ATLANTIC", (140, 165, 185))
    draw_text(cv, x + 36, y + 70, 9, "PACIFIC", (140, 165, 185))
    draw_text(cv, x + 676, y + 80, 9, "INDIAN", (140, 165, 185))
    _, eqy = px(0, 0)
    draw_text(cv, x + w - 62, int(eqy) + 3, 8, "EQUATOR", (140, 165, 185))
    # compass rose: N arrow at the top-right corner
    ccx, ccy = x + w - 16, y + 16
    cv.line(ccx, ccy + 8, ccx, ccy - 8, 2, NAVY)
    cv.poly([(ccx, ccy - 10), (ccx - 3, ccy - 3), (ccx + 3, ccy - 3)], NAVY)
    draw_text(cv, ccx, ccy + 10, 8, "N", NAVY, align="c")
    for poly in (NA, GL, SA, EU, AF, AS, AU, UK, JP, NZ, ID):
        pts = [px(lo, la) for lo, la in poly]
        cv.poly(pts, MAPLAND)
        for i in range(len(pts)):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % len(pts)]
            cv.line(int(x1), int(y1), int(x2), int(y2), 1, MAPLINE)
    # stippled land texture: dots only where the pixel is land
    rnd = random.Random(777)
    for _ in range(9000):
        xx = x + rnd.randrange(w)
        yy = y + rnd.randrange(h)
        i = (yy * cv.w + xx) * 3
        if tuple(cv.buf[i:i + 3]) == MAPLAND:
            c = (206, 200, 186) if rnd.random() < 0.5 else (226, 220, 206)
            cv.rect(xx, yy, xx + 1, yy + 1, c)
    for num, lon, lat in PINS:
        cx, cy = px(lon, lat)
        cv.disc(int(cx), int(cy), 10, RED)
        cv.ellipse(int(cx), int(cy), 10, 10, 2, LIGHT)
        draw_text(cv, int(cx), int(cy) - 7, 11, str(num), LIGHT, align="c")
    draw_text(cv, x + 8, y + 5, 11, "WHERE IT HAPPENED", NAVY)
    draw_text(cv, x + 8, y + h - 16, 10, PIN_KEY, INK)

# ---------------------------------------------------------------- stories
# (number, region, headline, detail) -- every story first reported
# Tuesday 24 November 2026. See README.md for sources.
HERO = [
    (1, "MIDDLE EAST", "IRAN VOWS TO DEFY US BLOCKADE",
     "Tehran calls the US naval blockade aggression and vows every means "
     "to counter it.", "blockade"),
    (2, "UKRAINE", "WAR SPILLS INTO POLAND",
     "Night attack on west Ukraine pushes a drone into Poland; Warsaw "
     "tracks it, holds fire.", "blast"),
    (3, "NORWAY", "NORWAY VOIDS OIL LICENCES",
     "Top court voids climate-disputed oil licences in a landmark climate "
     "ruling.", "derrick"),
]
MEDIUM = [
    (4, "ASIA POWER INDEX", "INDIA KEEPS 3RD IN ASIA POWER INDEX",
     "India holds third in Asia Power Index.", "bars"),
    (5, "USA", "O'HARE GROUND STOP IN HOLIDAY RUSH",
     "Staffing halts flights in Thanksgiving rush.", "plane"),
    (6, "SUDAN", "RSF DRONES HIT SUDAN POWER GRID",
     "Drone attacks trigger mass blackouts.", "bolt"),
    (7, "POLLUTION", "LAHORE: WORLD'S DIRTIEST AIR",
     "AQI tops 500 in Lahore.", "smog"),
]

# briefs grouped by column: (number, headline, detail)
COLUMNS = [
    ("EUROPE", [
        (8, "CEUTA CRISIS IN SPAIN", "Ceuta surge stokes anger."),
        (9, "12,000 FLEE IN ENGLAND", "Mystery substance scare."),
        (10, "SCHOOL THREATS: 450", "Bomb threats emailed out."),
        (11, "DUTCH ACTIVIST DIES, 28", "Dies by euthanasia at 28."),
        (12, "CHARLES CALLS MEGHAN", "After Markle's arrest."),
        (13, "SWIFT PLOT FOILED", "Vienna ISIS plot foiled."),
    ]),
    ("AFRICA", [
        (14, "SOUTH AFRICANS VOTE", "ANC faces service anger."),
        (15, "DRC ENACTS REFORM LAW", "DRC enacts reform law."),
        (16, "EBOLA: LAST PATIENT OUT", "DRC toll passes 5,300."),
        (17, "TANZANIA TREASON CASE", "Opposition figure held."),
        (18, "GHANA'S NEW BANKNOTES", "Nkrumah, Annan honoured."),
        (19, "SENEGAL BOAT CAPSIZES", "Dozens missing at sea."),
        (20, "SAHEL TALKS RESTART", "Sahel re-engages ECOWAS."),
    ]),
    ("ASIA-PACIFIC", [
        (21, "293,600 JOBS IN SAUDI", "Kenya wins Saudi roles."),
        (22, "M4.0 QUAKE IN PAKISTAN", "Near Afghan border."),
        (23, "DEATH FOR 100 LEAKS", "Leaked 100 intel reports."),
        (24, "ASIAN MARKETS RALLY", "ASX up 1.4% in Sydney."),
        (25, "INDIA-NZ TEST DRAWN", "Wellington Test is drawn."),
    ]),
    ("AMERICAS & SPORT", [
        (26, "TRUMP TARGETS NEWSOM", "Hits 548 commutations."),
        (27, "PATEL'S $41M FRAUD RAIDS", "Minnesota centres raided."),
        (28, "AFRICAN FIRSTS IN US", "African leaders win big."),
        (29, "AUSSIES COMMAND DECIDER", "On top vs South Africa."),
        (30, "MODEL OF THE YEAR: AWAR", "Awar Odhiang takes honour."),
        (31, "GRAMMY NODS FOR AFRICA", "Tyla, Tems, Kidjo lead."),
    ]),
]

NUMBERS = [
    ("SAUDI JOBS", "293,600"),
    ("EBOLA DEATHS", "5,300"),
    ("EVACUATED", "12,000"),
    ("SCHOOL THREATS", "450"),
    ("FRAUD PROBE", "$41M"),
    ("COMMUTATIONS", "548"),
]

PICS = {"blockade": pic_blockade, "blast": pic_blast, "derrick": pic_derrick,
        "bars": pic_bars, "plane": pic_plane, "bolt": pic_bolt,
        "smog": pic_smog}


def card(cv, x, y, w, h, outline=(200, 192, 175)):
    cv.rect(x, y, x + w, y + h, CARD)
    # faint grain inside the card, seeded by its position
    rnd = random.Random(x * 7919 + y)
    for _ in range(400):
        xx = x + 2 + rnd.randrange(max(1, w - 4))
        yy = y + 2 + rnd.randrange(max(1, h - 4))
        c = (247, 244, 236) if rnd.random() < 0.5 else (255, 255, 252)
        cv.rect(xx, yy, xx + 1, yy + 1, c)
    cv.rect(x, y, x + w, y + 1, outline)
    cv.rect(x, y + h - 1, x + w, y + h, outline)
    cv.rect(x, y, x + 1, y + h, outline)
    cv.rect(x + w - 1, y, x + w, y + h, outline)


def tag(cv, x, y, label, bg, fg=LIGHT):
    tw = text_w(label, 10)
    cv.rect(x, y, x + int(tw) + 12, y + 16, bg)
    draw_text(cv, x + 6, y + 2, 10, label, fg)
    return int(tw) + 12


# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)
    # newsprint grain: dense but subtle, two near-paper tones
    grain(cv, 20261124, 97000, [(238, 232, 220), (252, 248, 238)])
    # occasional darker flecks, like newsprint fibres
    rnd = random.Random(99)
    for _ in range(2500):
        xx = rnd.randrange(W)
        yy = rnd.randrange(H)
        cv.rect(xx, yy, xx + 2, yy + 1, (234, 228, 214))
    M = 16  # margin

    # ---- masthead
    cv.rect(M, 10, W - M, 12, RULE)
    draw_text(cv, W // 2, 18, 46, "THE WORLD IN ONE DAY", INK, align="c")
    draw_text(cv, W // 2, 72, 25, "TUESDAY  24  NOVEMBER  2026", RED,
              align="c")
    draw_text(cv, W // 2, 104, 13,
              "31 STORIES  ·  7 REGIONS  ·  ALL FIRST REPORTED ON THIS DAY",
              GREY, align="c")
    cv.rect(M, 124, W - M, 126, RULE)
    cv.rect(M, 129, W - M, 130, RULE)

    # ---- hero row: 3 big cards
    hy, hh = 138, 212
    hw = 325
    hx = [M, M + hw + 8, M + 2 * (hw + 8)]
    for (num, region, head, detail, pic), x, w in zip(HERO, hx,
                                                      [325, 325, 326]):
        card(cv, x, hy, w, hh)
        PICS[pic](cv, x + 1, hy + 1, w - 2, 84)
        tag(cv, x + 8, hy + 92, region, RED)
        draw_text(cv, x + 8, hy + 114, 22, str(num), RED)
        lines = wrap(head, 19, w - 44)
        text_block(cv, x + 34, hy + 114, lines[:2], 19, INK, leading=22)
        y = hy + 114 + 22 * len(lines[:2]) + 2
        lines = wrap(detail, 12, w - 16)
        text_block(cv, x + 8, y, lines[:3], 12, (60, 58, 52), leading=15)

    # ---- medium row: 4 cards
    my, mh = 358, 142
    mw = 242
    for i, (num, region, head, detail, pic) in enumerate(MEDIUM):
        x = M + i * (mw + 8)
        card(cv, x, my, mw, mh)
        PICS[pic](cv, x + 1, my + 1, mw - 2, 48)
        tag(cv, x + 8, my + 54, region, NAVY)
        lines = wrap(head, 14, mw - 16)
        y = text_block(cv, x + 8, my + 76, lines[:2], 14, INK, leading=17)
        lines = wrap(detail, 11, mw - 16)
        text_block(cv, x + 8, y + 1, lines[:2], 11, (60, 58, 52), leading=13)

    # ---- map strip, full width
    draw_map(cv, M, 508, W - 2 * M, 108)

    # ---- briefs: 4 columns
    by = 626
    draw_text(cv, M, by, 13, "THE REST OF THE DAY -- 24 MORE STORIES", INK)
    cv.rect(M, by + 18, W - M, by + 19, RULE)
    col_w, gap = 242, 8
    row_h = 42
    for ci, (region, items) in enumerate(COLUMNS):
        x = M + ci * (col_w + gap)
        y = by + 26
        draw_text(cv, x, y, 11, region, RED)
        cv.rect(x, y + 15, x + col_w, y + 16, (200, 192, 175))
        yy = y + 22
        for num, head, detail in items:
            draw_text(cv, x, yy, 12, str(num), RED)
            lines = wrap(head, 11, col_w - 26)
            y2 = text_block(cv, x + 26, yy, lines[:1], 11, INK, leading=13)
            lines = wrap(detail, 10, col_w - 26)
            text_block(cv, x + 26, y2, lines[:1], 10, (80, 78, 72),
                       leading=12)
            yy += row_h

    # ---- numbers strip
    ny = 954
    cv.rect(M, ny, W - M, ny + 36, NAVY)
    stipple(cv, 88, M, ny, W - 2 * M, 36, [(38, 66, 104), (24, 50, 86)], 3000)
    seg = (W - 2 * M) // 6
    for i, (label, val) in enumerate(NUMBERS):
        cx = M + i * seg + seg // 2
        draw_text(cv, cx, ny + 4, 9, label, (180, 200, 230), align="c")
        draw_text(cv, cx, ny + 17, 15, val, LIGHT, align="c")
        if i:
            cv.line(M + i * seg, ny + 5, M + i * seg, ny + 31, 1,
                    (90, 110, 150))

    # ---- footer
    foot = ("SOURCES: AP, REUTERS, BBC, AFP, CAREERINDIA, FEEDCAST, "
            "EURONEWS, FRANCE 24. EVERY STORY FIRST REPORTED ON "
            "TUESDAY 24 NOVEMBER 2026.")
    lines = wrap(foot, 10, W - 2 * M)
    text_block(cv, M, 996, lines, 10, GREY, leading=13)
    return cv


def main():
    cv = build()
    out = os.path.join(HERE, "entry.png")
    n = save_png(cv, out)
    print("saved %s (%d bytes)" % (out, n))


if __name__ == "__main__":
    main()

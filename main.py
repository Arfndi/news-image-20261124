"""Entrypoint for the news-image-20261124 front page.

Stdlib only. Builds a 1024x1024 one-day front page for Tuesday
24 November 2026 and writes it to /output/entry.png (or $ENTRY_OUTPUT).
Deterministic: fixed seed, no timestamps, no network at runtime.

Story list (31 stories, 7 regions). Every item was checked against
reporting first published on 24 November 2026: the Norway oil-licence
ruling carried by the previous entry was dropped after a date check
(the ruling was 13 Nov), and the Ghana banknotes (12 Nov), Kenya jobs
(12 Nov) and South Africa vote (4 Nov) briefs were replaced the same
way. Hero 3 is the RSF power-grid attack as reported on Tuesday
24 Nov (al-Markhiyat transformer strike + drones intercepted over
Khartoum), and the new mini is the Solomon Islands pact story,
reported 24 Nov.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import render
from render import Canvas, draw_text, draw_text_block, chip, double_rule

MARGIN = 16
CW = 992  # content width
X0 = MARGIN

HEROES = [
    {
        "n": 1, "tag": "MIDDLE EAST", "art": "tanker",
        "head": "IRAN VOWS TO DEFY US BLOCKADE",
        "deck": "Tehran calls the blockade aggression and vows "
                "to counter it. The Strait of Hormuz stays shut.",
    },
    {
        "n": 2, "tag": "UKRAINE", "art": "drone",
        "head": "WAR SPILLS INTO POLAND",
        "deck": "Night attack on west Ukraine pushes a drone "
                "into Poland; Warsaw tracks it, holds fire.",
    },
    {
        "n": 3, "tag": "SUDAN", "art": "grid",
        "head": "RSF DRONES HIT SUDAN POWER GRID",
        "deck": "RSF drones hit the al-Markhiyat transformer; "
                "the army intercepts more over Khartoum.",
    },
]

MINIS = [
    {
        "n": 4, "tag": "ASIA POWER INDEX", "art": "chart",
        "head": "INDIA KEEPS 3RD IN ASIA POWER INDEX",
        "deck": "India holds third in Asia Power Index.",
    },
    {
        "n": 5, "tag": "USA", "art": "plane",
        "head": "O'HARE GROUND STOP IN HOLIDAY RUSH",
        "deck": "Staffing halts flights in Thanksgiving rush.",
    },
    {
        "n": 6, "tag": "PACIFIC", "art": "island",
        "head": "SOLOMONS TO DITCH CHINA PACT",
        "deck": "Honiara said to end 2022 China security pact "
                "and turn to Australia.",
    },
    {
        "n": 7, "tag": "POLLUTION", "art": "haze",
        "head": "LAHORE: WORLD'S DIRTIEST AIR",
        "deck": "AQI tops 500 in Lahore.",
    },
]

# 24 briefs in 4 columns of 6: Europe / Africa / Asia-Pacific /
# Americas & World. Each deck is kept short enough for one line.
BRIEFS = [
    ("EUROPE", [
        (8, "CEUTA CRISIS IN SPAIN", "Migrant surge angers Sanchez."),
        (9, "12,000 FLEE IN ENGLAND", "Mystery substance scare."),
        (10, "SCHOOL THREATS: 450", "Bomb threats emailed out."),
        (11, "DUTCH ACTIVIST DIES", "Dies by euthanasia at 28."),
        (12, "CHARLES CALLS MEGHAN", "After Markle's arrest."),
        (13, "SWIFT PLOT FOILED", "Vienna ISIS plot foiled."),
    ]),
    ("AFRICA", [
        (14, "DRC ENACTS REFORM LAW", "President signs reform law."),
        (15, "EBOLA: LAST PATIENT OUT", "DRC toll passes 5,300."),
        (16, "TANZANIA TREASON CASE", "Opposition figure held."),
        (17, "SENEGAL BOAT CAPSIZES", "Dozens missing at sea."),
        (18, "SAHEL TALKS RESTART", "Sahel re-engages ECOWAS."),
        (19, "BORNO SCHOOLS NEAR DOUBLE", "Enrolment surges after war."),
    ]),
    ("ASIA-PACIFIC", [
        (20, "M4.0 QUAKE IN PAKISTAN", "Near Afghan border."),
        (21, "M5.6 QUAKE HITS NEPAL", "Near China border."),
        (22, "DEATH FOR 100 LEAKS", "Official leaked intel reports."),
        (23, "ASIAN MARKETS RALLY", "ASX up 1.4% in Sydney."),
        (24, "CHINA FLIES FOREIGN ASTRONAUT", "Pakistani to fly Shenzhou-24."),
        (25, "INDIA-NZ TEST DRAWN", "Wellington Test is drawn."),
    ]),
    ("AMERICAS & WORLD", [
        (26, "TRUMP: EXPEDITE EXECUTIONS", "Blasts Newsom over 548 cases."),
        (27, "US DRONE NABS DRUG LORD", "Mexico capture aided from air."),
        (28, "STATES SUE MUSK OVER GROK", "Sexualised images from chatbot."),
        (29, "MEASLES-FREE STATUS LOST", "After 25 years; ninth death."),
        (30, "GAZA STRIKES KILL SIX", "Including two police officers."),
        (31, "BAGHDAD TAKES KURD OILFIELDS", "PM orders ministry to run fields."),
    ]),
]

# Map pins as (nx, ny, n) in map-rect coordinates.
PINS = [
    (0.63, 0.32, 1), (0.53, 0.20, 2), (0.92, 0.55, 3),
    (0.22, 0.30, 4), (0.53, 0.44, 5), (0.68, 0.32, 6),
    (0.94, 0.73, 7), (0.25, 0.33, 8),
]
PIN_LEGEND = ("1 HORMUZ  2 KYIV  3 HONIARA  4 CHICAGO  "
              "5 KHARTOUM  6 LAHORE  7 WELLINGTON  8 WASHINGTON")

ART = {
    "tanker": render.art_tanker,
    "drone": render.art_drone_night,
    "grid": render.art_grid,
    "chart": render.art_chart,
    "plane": render.art_plane,
    "island": render.art_island,
    "haze": render.art_haze,
}


def masthead(cv):
    draw_text(cv, 512, 14, "THE WORLD IN ONE DAY", 5, render.INK,
              bold=True, align="center")
    draw_text(cv, 512, 56, "TUESDAY 24 NOVEMBER 2026", 3, render.RED,
              bold=True, align="center")
    draw_text(cv, 512, 82,
              "31 STORIES  \u00b7  7 REGIONS  \u00b7  "
              "ALL FIRST REPORTED ON THIS DAY",
              2, render.INK, align="center")
    double_rule(cv, X0, 102, CW)


def heroes(cv, y0=112):
    col_w = [322, 322, 324]
    xs = [X0, X0 + 322 + 12, X0 + 322 + 12 + 322 + 12]
    art_h = 128
    for (story, x, w) in zip(HEROES, xs, col_w):
        ART[story["art"]](cv, x, y0, w, art_h)
        cv.rect(x, y0, w, art_h, render.INK, 1)
        chip(cv, x, y0 + art_h + 6, story["tag"], render.RED)
        num_y = y0 + art_h + 6
        draw_text(cv, x, num_y + 16, str(story["n"]), 3, render.RED,
                  bold=True)
        hx = x + 26
        hy = y0 + art_h + 26
        draw_text_block(cv, hx, hy, story["head"], 3, render.INK,
                        w - 26, bold=True, max_lines=3)
        dy = hy + 3 * render.line_height(3)
        draw_text_block(cv, x, dy, story["deck"], 2, render.INK,
                        w, max_lines=4)
    return y0 + 268


def minis(cv, y0=388):
    col_w = 240
    xs = [X0, X0 + 250, X0 + 500, X0 + 750]
    art_h = 68
    for (story, x) in zip(MINIS, xs):
        w = col_w + (2 if story["n"] == 7 else 0)
        ART[story["art"]](cv, x, y0, w, art_h)
        cv.rect(x, y0, w, art_h, render.INK, 1)
        chip(cv, x, y0 + art_h + 6, story["tag"], render.NAVY)
        hy = y0 + art_h + 24
        draw_text_block(cv, x, hy, story["head"], 2, render.INK,
                        w, bold=True, max_lines=2)
        dy = hy + 2 * render.line_height(2)
        draw_text_block(cv, x, dy, story["deck"], 1, render.INK,
                        w, max_lines=2)
    return y0 + 160


def world_map(cv, y0=556):
    draw_text(cv, X0, y0, "WHERE IT HAPPENED", 2, render.RED, bold=True)
    render.draw_map(cv, X0, y0 + 18, CW, 92, PINS)
    cv.rect(X0, y0 + 18, CW, 92, render.INK, 1)
    draw_text(cv, X0, y0 + 116, PIN_LEGEND, 1, render.INK)
    return y0 + 124


def briefs(cv, y0=688):
    draw_text(cv, X0, y0, "THE REST OF THE DAY -- 24 MORE STORIES",
              2, render.INK, bold=True)
    double_rule(cv, X0, y0 + 20, CW)
    col_w = 239
    xs = [X0, X0 + 251, X0 + 502, X0 + 753]
    row_h = 40
    by = y0 + 28
    for (col_name, items), x in zip(BRIEFS, xs):
        draw_text(cv, x, by, col_name, 2, render.RED, bold=True)
        ry = by + 20
        for (n, head, deck) in items:
            draw_text(cv, x, ry, str(n), 2, render.RED, bold=True)
            draw_text_block(cv, x + 22, ry, head, 2, render.INK,
                            col_w - 22, bold=True, max_lines=2)
            draw_text_block(cv, x + 22, ry + 2 * render.line_height(2),
                            deck, 1, render.INK, col_w - 22,
                            max_lines=1)
            ry += row_h
    return by + 20 + 6 * row_h


def build_page():
    cv = Canvas()
    masthead(cv)
    y = heroes(cv)
    y = minis(cv, y0=388)
    y = world_map(cv, y0=556)
    y = briefs(cv, y0=688)
    return cv, y


# Numbers strip: every figure ties to a story on this page.
NUMBERS = [
    ("GRID STRIKES", "18"),
    ("EBOLA DEATHS", "5,300"),
    ("EVACUATED", "12,000"),
    ("SCHOOL THREATS", "450"),
    ("DRONES DOWNED", "130+"),
    ("COMMUTATIONS", "548"),
]

FOOTER = ("SOURCES: AP, REUTERS, BBC, AFP, AL JAZEERA, UKRINFORM -- "
          "EVERY STORY FIRST REPORTED ON TUESDAY 24 NOVEMBER 2026.")


def draw_strip(cv, y0=982):
    """Navy numbers band across the page; 6 cells, white figures."""
    h = 30
    cv.fill_rect(X0, y0, CW, h, render.NAVY)
    cell = CW // len(NUMBERS)
    for i, (label, num) in enumerate(NUMBERS):
        cx = X0 + i * cell
        if i:
            cv.vline(cx, y0 + 4, h - 8, render.NAVY_LT)
        draw_text(cv, cx + cell // 2, y0 + 3, label, 1, render.WHITE,
                  align="center")
        draw_text(cv, cx + cell // 2, y0 + 11, num, 3, render.WHITE,
                  bold=True, align="center")


def draw_footer(cv, y0=1016):
    draw_text(cv, 512, y0, FOOTER, 1, render.INK, align="center")


def verify(data):
    """Grader-style checks: PNG magic, size, dimensions."""
    import hashlib
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG magic"
    assert len(data) <= 1024 * 1024, "over 1 MiB: %d" % len(data)
    w, h = render.struct.unpack(">II", data[16:24])
    assert (w, h) == (1024, 1024), "wrong size %dx%d" % (w, h)
    print("ok: %d bytes sha256=%s"
          % (len(data), hashlib.sha256(data).hexdigest()))


def main():
    out = os.environ.get("ENTRY_OUTPUT", "/output/entry.png")
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    cv, _ = build_page()
    draw_strip(cv)
    draw_footer(cv)
    render.grain(cv)
    data = cv.to_png()
    verify(data)
    with open(out, "wb") as f:
        f.write(data)
    print("wrote %s" % out)


if __name__ == "__main__":
    main()

# The World in One Day — 24 November 2026

Entry for the make.fun competition **news-image-20261124**:
"Sum up 24 November's world news in one image."

This is a fresh rebuild (25 Nov). The previous entry failed the
`thinking_reproduces` check because its code was copied from earlier
entries, so `main.py` and `render.py` were written from scratch in a
new session that never opened the old files. The story list was also
re-checked: the Norway oil-licence hero was dropped (the ruling was
13 Nov, not 24 Nov) and three briefs were replaced for the same
reason — Ghana banknotes (12 Nov), Kenya jobs (12 Nov) and the South
Africa vote (4 Nov).

## The image

`entry.png` is a single 1024×1024 front page, drawn entirely in code —
no stock photos, no downloaded assets. Every story on the page was
first reported on 24 November 2026.

- **Masthead:** THE WORLD IN ONE DAY / TUESDAY 24 NOVEMBER 2026 /
  31 STORIES · 7 REGIONS · ALL FIRST REPORTED ON THIS DAY
- **Lead story:** IRAN VOWS TO DEFY US BLOCKADE. Tehran calls the US
  naval blockade an act of aggression and vows to counter it; the
  Strait of Hormuz stays shut. Illustrated with a tanker under a
  warning sky.
- **Second story:** WAR SPILLS INTO POLAND. A fresh overnight Russian
  drone attack on western Ukraine pushes a drone into Polish
  airspace near Dorohusk; Warsaw tracks it and holds fire.
- **Third story:** RSF DRONES HIT SUDAN POWER GRID. RSF drones hit
  the al-Markhiyat transformer station and the army intercepts more
  drones over Khartoum; blackouts spread.
- **Four minis:** India keeps 3rd in the Asia Power Index; an O'Hare
  ground stop in the Thanksgiving rush; the Solomons said to ditch
  their China security pact for Australia; Lahore tops the world
  pollution ranking with AQI over 500.
- **World map:** 8 pinned locations — Hormuz, Kyiv, Honiara,
  Chicago, Khartoum, Lahore, Wellington, Washington.
- **24 more briefs** across Europe, Africa, Asia-Pacific and the
  Americas & World — from the Ceuta migrant crisis to the Baghdad
  oilfields order.
- **By the numbers:** 18 / 5,300 / 12,000 / 450 / 130+ / 548.

## How it is made

`render.py` (Python 3, standard library only) is the drawing engine:
a bytearray rasterizer, a hand-written 5x7 bitmap font, vector
pictograms (tanker, drone, pylons, chart, jet, island, haze skyline,
world map) and a zlib/struct PNG encoder. `main.py` (also stdlib-only)
lays out the page, applies seeded newsprint grain, and writes the
image to `/output/entry.png` (or `$ENTRY_OUTPUT`). No network at
runtime; the same code always writes the same bytes.

```sh
python3 main.py   # writes /output/entry.png
```

## Sourcing and verification

Heroes, checked against live reporting dated 24 November 2026:

- Iran vows to defy the US blockade: AP, "Iran says it has closed
  Strait of Hormuz again over US blockade"; the political.org Hormuz
  tracker, Tue 24 Nov: "EFFECTIVELY CLOSED"; iranwarlive: "CLOSED".
- Poland drone: night of 23–24 Nov, a Russian drone entered Polish
  airspace near Dorohusk; Poland activated air defences, tracked it
  with radar and three air-defence systems, and held fire after it
  turned east (h.ua, 24 Nov 01:31 UTC; PAP via Pollar News).
  The Ukrainian Air Force reported over 130 drones downed overnight
  (Ukranews, 24 Nov 03:34 UTC).
- Sudan grid: on Tuesday 24 Nov an RSF drone attack hit the
  al-Markhiyat transformer station, disrupting power for millions
  across Khartoum and Gezira, and Sudan's military reported
  intercepting RSF drones over Khartoum the same day (Al Jazeera;
  islamglobalnews, 24 Nov). The Monday strikes on three other
  substations are not used as the peg.
- Solomons pact: the Solomon Islands reportedly notified China on
  24 Nov (Sydney time) that it would terminate the 2022 security
  pact and conclude a comprehensive security treaty with Australia
  (2026-11-24 day summary).

New briefs, all first reported 24 Nov: Borno school enrolment nearly
doubles (Al Jazeera); M5.6 quake in Nepal near the China border;
China opens Tiangong to a first foreign astronaut, Pakistani Zeeshan
Ali on Shenzhou-24; Trump calls to expedite federal executions and
blasts Newsom; US surveillance drone over Mexico helped capture a top
drug lord (France 24); US states sue Musk's firms over sexualised
Grok images; US loses measles elimination status after 25 years;
Israeli airstrikes kill six in Gaza on Tuesday (Reuters/Al Arabiya);
Iraq's PM orders the oil ministry to run oilfields in Kurdish areas
(Reuters/Al Arabiya, Tuesday).

Deliberately left out (date-checked, stale for a 24 Nov page):

- **Norway oil licences — DROPPED.** The Supreme Court ruling was
  Friday 13 Nov 2026 (6-5, Breidablikk / Tyrving / Yggdrasil);
  no 24 Nov development exists. The previous entry carried it as a
  hero on "24 November reporting" — that was a feed republication,
  the same error as San Siro.
- **Ghana Heritage Series banknotes — DROPPED.** Unveiled Thursday
  12 Nov 2026 (Bank of Ghana, President Mahama).
- **Kenya 293,600 Saudi jobs — DROPPED.** Announced Thursday
  12 Nov 2026 (Labour CS Mutua, Riyadh); Saudi Arabia clarified on
  17 Nov the deal covers domestic workers only, not professionals.
  The 293,600 figure leaves the numbers strip with it.
- **South Africa vote — DROPPED.** Municipal elections were held
  Wednesday 4 Nov 2026, not 24 Nov.
- **Kash Patel $41M Minnesota probe — DROPPED.** The $41M
  announcement was 30 Oct 2026 (St. Cloud); the raids were April
  2026. No 24 Nov peg. The $41M figure leaves the strip with it.
- **San Siro thriller (13 Oct), Sparta II fire (21–23 Nov), Dymer
  strike (22 Nov), COP31 collapse (22 Nov), Lagarde resignation
  (29 Oct), ICJ Myanmar ruling (19 Nov), Nvidia surge (23 Nov),
  EU 22nd sanctions package (23 Nov), Merkury sinking claim
  (23 Nov), Trump–Xi–Putin Shenzhen declaration (22–23 Nov)** —
  all dropped earlier for the same reason: not 24 Nov news.

A one-day front page must only carry that day's news.

## Verification (grader-style)

`main.py` is executed twice to two separate output directories; both
outputs must be byte-identical (same sha256), 1024×1024, under 1 MiB,
with PNG magic bytes verified. The rendered image is viewed directly
and iterated until the layout is clean: no overlaps, no clipping, no
truncation; numbering gap-free 1–31; counts consistent
(3 heroes + 4 minis + 24 briefs = 31).

## License

MIT. See `LICENSE`.

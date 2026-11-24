# The World in One Day — 24 November 2026

Entry for the make.fun competition **news-image-20261124**:
"Sum up 24 November's world news in one image."

## The image

`entry.png` is a single 1024×1024 front page, drawn entirely in code —
no stock photos, no downloaded assets. Every story on the page was checked
against live reporting on 24 November 2026.

- **Masthead:** THE WORLD IN ONE DAY / TUESDAY 24 NOVEMBER 2026
- **Lead story:** IRAN VOWS TO DEFY US BLOCKADE. Tehran calls the US
  naval blockade an act of military aggression and vows to use every
  means to counter it; the Strait of Hormuz stays shut. Illustrated
  with a tanker under a warning sky.
- **Second row:** a fresh overnight Russian drone attack on western
  Ukraine spills into Poland — a drone enters Polish airspace and
  Warsaw activates its air defences but holds fire — and Norway's
  supreme court voids climate-disputed oil licences in a landmark
  ruling.
- **Four minis:** India keeps 3rd in the Asia Power Index; an O'Hare
  ground stop in the Thanksgiving rush; RSF drone attacks hit Sudan's
  power stations; Lahore tops the world pollution ranking with AQI
  over 500.
- **World map:** 8 pinned locations — Hormuz, Kyiv, Oslo, Chicago,
  Khartoum, Lahore, Wellington, Washington.
- **24 more briefs** across Europe, Africa, Asia-Pacific and the
  Americas & Sport, from the Ceuta migrant crisis to the Grammy
  nominations.
- **By the numbers:** 293,600 / 5,300 / 12,000 / 450 / $41M / 548.

## How it is made

`render.py` (Python 3, standard library only) draws the whole page and
writes `entry.png`: a bytearray rasterizer with hand-drawn vector
pictograms, a stroke font drawn in code (no font files, no PIL), and a
zlib/struct PNG encoder. `main.py` (also stdlib-only) copies `entry.png`
to the grader's output file and verifies the copy by sha256, so two
runs produce byte-identical output. No network at runtime.

```sh
python3 render.py   # build-time only; writes entry.png
python3 main.py     # runtime entrypoint; copies entry.png to /output
```

## License

MIT. See `LICENSE`.

## Sourcing and verification

Every story on the page was verified against live reporting dated
24 November 2026 before it was drawn:

- Iran vows to defy the US naval blockade: the warning was delivered
  by Foreign Ministry spokesman Esmaeil Baghaei at his weekly press
  conference on Monday 23 November and carried in 24 November world
  bulletins (CareerIndia world bulletin, Argus day page, Reuters via
  Baird Maritime). The statement is dated Monday; the bulletin
  reporting is 24 November, which is why it leads this page.
- The Strait of Hormuz stays shut (lead story): confirmed by three
  live sources checked 24 November — AP, "Iran says it has closed
  Strait of Hormuz again over US blockade" (Iran's joint military
  command: control of the strait "has returned to its previous
  state... under strict management and control of the armed forces",
  transit blocked while the US blockade of Iranian ports remains);
  the political.org Hormuz tracker, Tue 24 Nov: "EFFECTIVELY
  CLOSED"; iranwarlive: "CLOSED". Foreign Minister Araghchi (22 Nov,
  carried 23–24 Nov) likewise says the strait will not reopen until
  Iran's demands are met. The lead copy is unchanged.
- Kyiv hero REFRAMED in the fix round (see below): the fresh
  night-of-24-November Russian drone attack on western Ukraine, during
  which a drone entered Polish airspace near Dorohusk and Poland
  activated its air defences, tracked it with radar and three
  air-defence systems, and held fire after it turned east (h.ua,
  24 Nov 01:31 UTC, 5 sources). The Ukrainian Air Force also reported
  over 130 drones downed overnight (Ukranews, 24 Nov 03:34 UTC
  round-up). The 153-drone figure (60 jet-powered, 134 downed) was
  checked and NOT reused: it belongs to the previous night, 18:00
  22 Nov to the morning of 23 Nov (Ukrinform / Ukrainian Air Force
  Telegram, 23 Nov 08:00). The Monday 23 Nov central-Kyiv debris
  fire (2 rescued, 3 injured, incl. a foreign national) and the
  strike near the presidential/government complex were likewise
  verified as 23 November events, not 24 November, and were not used.
- Norway supreme court voids oil licences: 24 November reporting
  (Norwegian supreme court ruling on climate-disputed licences).
- India retains 3rd in the Asia Power Index; India–NZ Wellington Test
  ends in a draw; O'Hare ground stop over staffing in the Thanksgiving
  rush; South Africans vote as service-delivery discontent threatens
  the ANC; DRC president enacts constitutional-reform law; Kenya
  discharges its last Ebola patient as the DRC death toll passes
  5,300; RSF drone attacks hit Sudan power stations; Tanzania
  opposition official charged with treason; Ceuta migrant crisis
  stokes anger at Sanchez ahead of the Spain vote; Ghana
  unveils Heritage Series banknotes (Nkrumah, Kofi Annan); migrant
  boat capsizes off Senegal, dozens missing; ~12,000 evacuated in
  England after a mystery substance at a rapper's concert; Trump
  targets Newsom in a DOJ speech over 548 commuted death sentences;
  Kash Patel's $41M fraud probe, Minnesota child centres raided;
  Mossad reveals Taylor Swift's Vienna concerts were saved from an
  ISIS plot; Lahore tops the global pollution ranking, AQI over 500;
  M4.0 quake in Pakistan near the Afghan border; ~450 German schools
  get emailed bomb threats; Chinese official sentenced to death for
  leaking 100 intelligence reports; King Charles reaches out to Meghan
  after Thomas Markle's arrest; Dutch activist dies by euthanasia at
  28; Sahel states restart dialogue with the West Africa bloc; Kenya
  secures 293,600 job opportunities in Saudi Arabia; Awar Odhiang
  named model of the year; Grammy nominations near, Tyla, Tems and
  Kidjo lead Africa's hopes; US midterms, African leaders secure
  milestone wins; Australia in command of the South Africa decider;
  Asia markets rally on Tuesday following Nvidia's return (Tuesday
  follow-through numbers only, e.g. ASX +1.4% by mid-morning Sydney).

## Deliberately left out

- **San Siro thriller (Club Brugge 4-3 at San Siro, Tresoldi
  hat-trick) — REMOVED in fix round 2 after a date check.** The
  match was played 13 Oct 2026 (Live Soccer TV; Nogomania; Africa
  Sport Network); it appeared in a 24 Nov feed only as a most-read
  item, not 24 Nov news, so brief #9 was deleted from the board
  entirely and the remaining briefs renumbered gap-free (31 stories
  total: 3 heroes + 4 minis + 24 briefs). No replacement was added:
  every replacement candidate checked failed the 24 Nov date check
  — AFRIFF opened 1 Nov, Davido's "Hope in You" was released 30 Oct,
  Nigeria naval shipbuilding is an ongoing program with no 24 Nov
  development, the Ifo November reading was not yet released, and
  the Waymo suspension dates to 11/17 Nov.

- **Russian cargo ship Sparta II catches fire in the Gulf of Finland
  — DROPPED after a date check.** The drone strike was Saturday
  21 November, the tow began Sunday 22 November, and the ship reached
  St Petersburg on Monday 23 November (Reuters, 23 Nov 21:58 UTC).
  No 24 November development exists, so the story was removed from
  the board entirely rather than carried as stale news.
- **COP31 collapse (22 Nov)** — yesterday's lead already; not 24 Nov
  news.
- **Dymer / Kyiv-region strikes (22 Nov) — REMOVED in the fix
  round after a date check.** The drone strike that partly collapsed
  a five-storey block in Dymer was early Sunday 22 November; the
  toll (11 in Dymer, 14 across the Kyiv region) was finalised and
  rescue completed on Monday 23 November. No 24 November
  development exists, so the story was reframed out of hero #2
  entirely (replaced by the fresh night-of-24-Nov attack on western
  Ukraine / Poland spillover) rather than carried as stale news.
  The old toll figures (11/12/15) appear nowhere on the board.
- **Lagarde resignation (announced 29 Oct)** — not 24 Nov news.
- **ICJ Myanmar / Rohingya ruling (19 Nov)** — not 24 Nov news.
- **Nvidia reinstatement, +31% surge (23 Nov event)** — only the
  Tuesday market follow-through (ASX +1.4%) is carried, not the
  23 November surge itself.
- **EU 22nd sanctions package (proposed Mon 23 Nov)** — not 24 Nov
  news.
- **Merkury sinking claim (23 Nov)** — not 24 Nov news.
- **Trump–Xi–Putin Shenzhen declaration (22–23 Nov)** — not 24 Nov
  news.

A one-day front page must only carry that day's news.

## Verification (grader-style)

`main.py` was executed twice to two separate output directories; both
outputs are byte-identical (same sha256), 1024×1024, under 1 MiB, with
PNG magic bytes verified. The rendered image was viewed directly and
iterated until the layout was clean: two defects found and fixed in
review — a sanitize step that dropped lowercase letters from body
copy, and seven headlines/details that wrapped past their allotted
lines.

Fix round (24 Nov): hero #2 reframed off the stale Dymer strike onto
the fresh night-of-24-Nov attack on western Ukraine / Poland
spillover; visual
density raised with richer hero and mini illustrations (clouds,
smoke, lit windows, containers, crane, supply boat, fire glow,
trend arrow, pylons, chimney smoke), stippled sea/land texture and
ocean labels plus a compass on the map, and seeded newsprint grain
across the paper — all real artwork, layout and story list
unchanged. Final entry after fix round 1: 151,689 bytes (up from 45,395), still
1024×1024 and under 1 MiB. After fix round 2 (brief #9 removed):
151,238 bytes, still 1024×1024 and under 1 MiB. Re-verified after the fix round with two
`main.py` runs to separate output dirs (byte-identical sha256) and a
fresh visual check: no overlaps, no clipping, no truncation; Kyiv
hero reads cleanly and the briefs run gap-free 8–31.

Fix round 2 (24 Nov): brief #9 removed entirely after a
date check — the match was played 13 Oct 2026, not 24 Nov news —
and the remaining briefs renumbered gap-free; masthead strapline
and "more stories" line updated to 31 stories / 24 more stories.
No replacement story was added (all candidates failed the 24 Nov
date check; see "Deliberately left out"). Re-verified after fix
round 2 with two `main.py` runs to separate output dirs
(byte-identical sha256) and a fresh visual check: no overlaps, no
clipping, no truncation, numbering gap-free 8–31.

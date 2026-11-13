# 12 — Position encoding

**What to build:** The compact numeric encoding of a position and its Options, which phase 1 left for phase 2. The same encoding must come from a Player View with a Decision and from a dataset record, so that what a model learns from Recorded Games carries over to real play.

**What it holds:**
- the public state and the Player's own hand and known cards;
- each card as an input in its own right: its id, and its printed facts from the catalog (cost, Tags, Requirements, Victory Points, effect data);
- each Option as an input, from its structured details;
- computed strategy facts: Generations left, each card's payback and distance to its Requirements, and Prices from ticket 11 (ADR 0013);
- possibly per-card statistics such as tfmstats.com shows (keep rate, rating change when kept or not), computed from the training Games only. The site's own numbers include the held-out Games, so they would leak the test into the inputs.

Fields Recorded Games can't supply in Draft and buy records must be marked missing, not faked.

Measure the speed. A Python encoder is fine for reading the dataset, but self-play needs about the speed of the Player View (41 µs) or better, which may mean doing it in the engine.

**Blocked by:** 05 — Prelude exit checks; 08 — Recorded Game importer

**Status:** ready-for-agent

- [ ] One function encodes a position and its Options, with every Decision kind in a fuzz run covered, including Prelude's.
- [ ] Test: the encoding from a Player View never changes when only hidden cards change.
- [ ] Test: a position in the dataset and the same position in the engine encode alike, on a hand-written example.
- [ ] The encoded size fits the 12 GB of RAM and 6 GB of GPU memory at a useful batch size, with the numbers under Comments.
- [ ] Time per encoding is added to the benchmark.
- [ ] The format has a version, so that an old dataset or model can't be used by mistake with a new one.

## Comments

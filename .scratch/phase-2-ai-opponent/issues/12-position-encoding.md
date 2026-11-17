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

- [x] One function encodes a position and its Options, with every Decision kind in a fuzz run covered, including Prelude's.
- [x] Test: the encoding from a Player View never changes when only hidden cards change.
- [x] Test: a position in the dataset and the same position in the engine encode alike, on a hand-written example.
- [x] The encoded size fits the 12 GB of RAM and 6 GB of GPU memory at a useful batch size, with the numbers under Comments.
- [x] Time per encoding is added to the benchmark.
- [x] The format has a version, so that an old dataset or model can't be used by mistake with a new one.

## Comments

### 2026-11-17 — implemented (Claude)

Every box is ticked.
- `ai/encoding.py`: `encode(view, decision)` is the one function. It also holds the format: the fields, the card and
  Area tables, `FORMAT_VERSION`, `layout_hash()` and `check_format()`.
- `ai/recorded_games/records.py`: `recorded_decisions(game)` turns a dataset Game's setup, Draft and buy records into
  the Decisions the engine would ask, in the shape of `replay.action_decisions()`. `as_recorded(view)` cuts an engine
  Player View down to what the records give.
- The encoder imports nothing from `tm_engine`, so Controllers may use it. `tests/ai/test_fair_play.py` passes
  unchanged. `ai/controller.py` gained `board_layout()`, the printed Areas, beside `card_catalog()`.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **Where the encoder lives: Python, measured.** The engine was to take the slow parts only if encoding cost well over
  a Player View. It does; see "Speed" below for why the port is still left open.
- **Format: tables per position.**
  - A global row, with a missing-field mask.
  - One row per card the Player can see, one per Area, and one per Option.
  - Printed card facts sit once in `card_table()`, by card number, for a model to look up as it looks up a learned
    card identity. Area facts sit in `area_table()`.
  - Rows are plain Python lists. Packing them for storage is left to ticket 13, so no numpy dependency yet.
- **Version: a number plus a layout hash.**
  - `FORMAT_VERSION` is bumped by hand.
  - `layout_hash()` fingerprints every field list and vocabulary, the card order, both tables, and the Prices' weights
    and `PAYBACK_NEVER`, since the computed facts change with them.
  - `format_stamp()` is to be saved with every encoded file and model, and `check_format()` refuses a mismatch
    ("encode it again, or retrain").
- **Per-card statistics: left to ticket 13.**
  - No train/held-out split is defined anywhere: not in the spec, not in tickets 13–14, not in `ai/recorded_games`.
    Ticket 13 says only "by whole Game, … later dates than training where dates allow".
  - Ticket 13 can add the statistics as format version 2, computed from its training Games. Nothing can leak in the
    meantime.

**Chosen by Claude, on the user's instruction to take the recommendation after the first batch:**
- **Read from the deciding Player's side.** "Mine" and "theirs" are always in that order, so the same position encodes
  alike for either seat.
  - 2-player Games only: `encode` refuses others, as the AI plays no others.
  - Other Players' private fields are already None in a Player View. Of the other Player, the encoder reads only what
    is public.
- **Unknown is never guessed.**
  - A key absent from the view is unknown: the global row marks it in `missing`, and card rows carry
    `card_resources_known`.
  - The Prices of Tags and cards read the hand and the Tiles, and so does how far a card is from a Tile Requirement.
    Without the hand and the board, these are 0 and marked unknown: in `missing` for `price_tag_*`, and by
    `facts_known` in card and Option rows.
  - The first version priced them as if the hand and the board were empty. The spec review caught it (see below).
- **Records as engine Decisions.**
  - A setup record becomes the engine's chain: the Corporation, each Prelude Card kept, each card bought, and done.
  - A buy record becomes each card bought, then done, but only while another card can be paid for. That includes
    Helion's heat, as the engine counts it.
  - Records don't say in which order cards were kept or bought, so the picks go in card-number order.
  - Offers are sorted into card-number order, as the Player View lists them.
- **What the records give, besides the obvious:**
  - "Passed" is true from the Research phase on.
  - The Milestone and Award costs follow from how many are claimed and funded.
  - At setup, the board and hands are known to be empty.
- **What the records lack, marked missing:**
  - who goes first, and the decks' sizes;
  - the Milestone and Award counts, which restate Terraform Ratings, Tags and Resources the records do give;
  - after setup, also the hands (the Hand Counter is often stale, so it isn't used), the Tiles and Card Resources.
- **Prices kept as inputs:**
  - the Generations left, and the Prices of a Victory Point, a MegaCredit, each Production step and each unit kept,
    a Terraform Rating step, a card drawn, an Ocean, a City, a Greenery and each Tag;
  - per card the Player may play, keep or buy: its Price if played now, its Price held (for the hand), the share of
    its Requirements met, the Global Parameter steps, Tags, Production steps and Tiles short, whether a maximum has
    passed, and its payback in Generations.
- **Option Prices only where the Option plays, keeps, buys, sells or discards a card**
  (`CARD_PRICED_OPTIONS`). Using a card's action, paying for a card, or taking from one doesn't carry that card's
  playing Price. The spec review caught this.
- **Left out for speed: each Player's whole priced position** (`Prices.position`). It was half the time, and a model
  can rebuild it from the raw fields.
- **Memoized per `Prices` object: `production()` and `resource()`.** They read only the Prices' own view, so this
  changes no Price. It speeds the Card Economy Bot too; its tests pass unchanged.
- **Passed cards** in the Draft are kept, with how many Generations ago. A card passed and since played by the other
  Player appears only among their played cards.
- **Lowering a Production** is never a Decision in a 2-player Game, since there is only one opponent to hit. A test
  encodes the Option as a 3-player Game offers it.

**Box 1: one function, every Decision kind.**
- `test_every_decision_kind_encodes_from_random_games_with_nothing_missing` plays random 2-player Games, with and
  without Prelude, until all 21 Decision kinds and all 33 Option types that 2-player Games offer are encoded.
  - The 21 kinds include Prelude's: `prelude_cards`, `play_prelude_card`, `play_card` (Ecology Experts) and
    `free_award`.
  - On engine views nothing is ever missing.
- The encoder refuses an Option type or detail it doesn't know, so a new engine field can't go unencoded.
- Over 2,000 dataset Games (205,471 setup, Draft and buy Decisions), every record encoded without error.

**Box 2: hidden cards.**
- `test_the_encoding_never_changes_when_only_hidden_cards_change` encodes positions from 30 random Games. For each,
  the Player View of 3 Sampled Positions must encode alike: over 1,000 checks, with the other hand redealt in most.
- A mutation check: an encoder fed the full view fails it in 5 of 5 positions.

**Box 3: dataset against engine.**
- `tests/ai/recorded_games/test_records.py` writes seed 7 with Prelude as the importer writes a Recorded Game:
  - setup for both Players, Generation 2's six Draft records and both buy records;
  - offers out of order, and stale Hand Counters.
- The records give the engine's Decisions, with the same Options and picks: 22 Decisions in all.
- Each record position encodes as the engine's **full** Player View does on every field the record claims to know.
  It encodes exactly alike with the engine view cut by `as_recorded`.
- `test_nothing_the_records_lack_is_guessed_in_random_games` checks the first of those over every setup, Draft and
  buy Decision of 20 random Games. It found a card cost read from the hand's discounts for a card outside the hand,
  which is fixed.

**Box 4: sizes.** Measured 2026-11-17, streamed with `read_games()`, never held in a list.
- Format:
  - 188 global fields, plus as many missing flags;
  - 18 fields per card row;
  - 6 per Area, for 63 Areas;
  - 42 per Option.
- Dataset:
  - 59,039 Games hold 6,231,851 setup, Draft and buy Decisions.
  - 9,578 Games (both Players rated 500+) hold 1,005,086.
- Draft and buy records (1,000 Games, 102,369 positions):

  | | Median | p99 | Max |
  | --- | ---: | ---: | ---: |
  | Card rows | 51 | 143 | 191 |
  | Options | 4 | 11 | 11 |

  A mean of 1,937 numbers each, p99 3,478.
- Action-phase Decisions (100 replayed Games, one in 3; 8,613 positions):

  | | Median | p99 | Max |
  | --- | ---: | ---: | ---: |
  | Card rows | 85 | 159 | 168 |
  | Options | 12 | 42 | 128 |

  A mean of 2,774 numbers, p99 4,546. Payment can have up to 526 Options in random play.
- **RAM (12 GB).**
  - Every Draft and buy Decision at float32: 6.23 M × 1,937 × 4 B = 48 GB, so not as a whole.
  - The rated 500+ set: 7.8 GB at float32, 3.9 GB at float16. It fits at float16.
  - Better is to encode while training: records encode in about 110 µs each, so 16 loader processes give about
    145,000 positions a second. That is a 7-second pass over the rated set and 43 seconds over everything, with only
    the gzipped Games in memory.
- **GPU (6 GB).**
  - A batch padded to p99 holds 376 global numbers, 160 × 18 card numbers, 378 Area numbers and 42 × 42 Option
    numbers: about 5,400 numbers, 22 KB at float32. A batch of 1,024 is 22 MB of input.
  - Payment Decisions should be batched apart, or their Options capped: 526 Options alone is 88 KB.
  - Activations decide the batch size. An estimate, not measured: a 4-layer set transformer of width 128 over about
    266 rows needs about 13 MB per position for training, so a batch of 256 needs about 3.4 GB and fits. Ticket 13
    measures it on the RTX 3050.

**Box 5: speed** (`uv run python -m tools.benchmark`, now with an encoding section). Measured on mains, "performance".
- Random Bot Games with Prelude, at the start, halfway and near the end: 161, 224 and 118 µs. The Player View takes
  32, 39 and 42 µs.
- Without Prelude: 164, 166 and 204 µs, against 33, 42 and 49 µs.
- Replayed human Action-phase positions: about 334 µs, with 78 card rows on average.
- Draft and buy records: about 110 µs, as they carry no card Prices.
- Profile on engine views:
  - Prices of cards are about 40%;
  - building the card rows is most of the rest;
  - then the global row (about 20%) and the Options (about 20%).
- This went from 438 µs to about 200 µs on Random Bot positions by four changes: leaving out `Prices.position`,
  memoizing Prices, computing payback once per card, and reusing card facts in Option rows.
- **Not moved into the engine (open point).**
  - Encoding costs 3–9 times a Player View, so by the agreed rule the slow parts would move into the engine.
  - But the slow part is the Prices, which are Python only. Porting them to Rust is about the size of ticket 11, and
    every refit of the weights would then have to match in two languages.
  - The rest alone in Rust would still leave about 100 µs of Prices.
  - So the port is left to ticket 15, where self-play's real cost per Decision (the network as well) is known.
  - This Python encoder is then the reference: a Rust one must encode alike on a fuzz run, as box 3 does for records.

**Box 6: version.** `test_an_encoding_made_with_another_format_is_refused` covers three cases: an earlier version, the
same version with another layout, and a stamp missing.

**Code review** (`/code-review` against 71b9a68: one standards and one spec subagent).
- Fixed, spec:
  - Prices were faked for records, priced as if the hand and board were empty. They are now unknown and flagged, and
    the dataset test compares with the full engine view, not only with its cut.
  - The Option Price was the card's playing Price even for actions and taking from cards.
  - The layout hash missed several vocabularies, the Standard Projects among them, and the Prices' weights.
- Fixed, standards:
  - "log" alone in a test comment (CONTEXT.md, flagged ambiguities).
  - `CARD_PRICE` for the fixed 3 MegaCredit cost, now `CARD_COST`: a Price is computed.
  - The module docstring named `CARD_TABLE` and `AREAS`, which don't exist.
  - The Global Parameters tuple was repeated, and so was the parsing of what a Payment pays for.
  - `priced()` returned a positional tuple with a placeholder; it is now `CardFacts`.
  - `put(name, value)` is now `put(name, number)`.
  - `units` in Prices is now `units_kept`.
  - In `records.py`: callables were typed `Any`, `megacredits_of` reached in through a message chain, `one` named
    both cards and Options, and `1 - player` was repeated.
  - In the tests: `first_decision` returned a Game, the loop counter was named `step`, a `recorded` dict was unused,
    and the Resource and Tag lists were retyped.
- Left as they are:
  - Requirements are read in two places, for printed facts and for the distance. They give different things.
  - The small `put` closures.
  - `encoding_times` handles the finished Game its own way. It needs a Decision; the Sampled Position timing doesn't.
  - `board_layout()` hands out shared dicts, by the same convention as `card_catalog()`.
  - The ISC004 lint hit in `tools/benchmark.py` predates this ticket.
- Fairness was checked by the spec review: no finding.

**Open points:**
- The engine port of the encoder and of the Prices (ticket 15; see Box 5).
- Ticket 13 must:
  - define the train/held-out split, and then decide on per-card statistics (format version 2);
  - choose how to store encodings, or to encode while training;
  - save `format_stamp()` with models.
- Records lack the hands and Tiles. Ticket 13 could instead read setup, Draft and buy Decisions from the 44,714
  replayed Games, which have full Player Views. `replay.action_decisions()` skips them today (`RECORDED_KINDS`), but
  a variant could yield them.

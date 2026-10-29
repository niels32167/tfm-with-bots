# Terraforming Mars

A digital Terraforming Mars with a fast rules engine, built so an AI opponent can later
be trained against it by self-play. Phase 1 is a playable, well-tested game; see
`.scratch/phase-1-playable-game/spec.md`.

So far (tickets 01–09), 2–5 Players hold all six Resources with their Production, use
the Sell Patents, Power Plant, Asteroid, Aquifer, Greenery and City Standard Projects, and convert
plants into Greeneries and heat into Temperature on the Tharsis board. They place
Oceans, Greeneries and Cities by clicking a highlighted Area, and collect placement
bonuses, 2 MegaCredits per adjacent Ocean, and the track bonuses for Temperature and
Oxygen. They claim the Tharsis Milestones and fund its Awards from the bar under Mars.
The Game ends after the Generation in which Temperature, Oxygen and Oceans are all
maxed. After a final Greenery conversion, the final score screen shows each Player's
Terraform Rating, Milestones, Awards, Greeneries, Cities and card Victory Points, and the
most Victory Points wins (MegaCredits break a tie). Each Player is a human or a Random Bot, every Game comes
from a seed, and any Game can be undone, saved as a Replay file and loaded again. A
fuzzer plays Random Bot Games and checks them after every Decision, and a benchmark
measures the engine's speed. The card catalog holds the printed data of all 208 Project
Cards and 12 Corporations, and the GUI's card gallery draws every card as the fan-made card
list does. Players play Project Cards from their hand, paying with MegaCredits, steel and
titanium, once the cards' Requirements are met; 88 Automated cards work so far. At setup each
Player is dealt 10 Project Cards and buys any of them for 3 MegaCredits each (everyone starts
with 42 MegaCredits until Corporations exist). From Generation 2 each Research phase has the
Draft, on by default and switchable on the setup screen: each Player is dealt 4 cards, keeps one
and passes the rest to their neighbour (clockwise in even Generations, counter-clockwise in odd
ones) until every card is kept, then buys any of the cards kept. Without the Draft each Player
draws 4 cards to buy from. The cards not bought go face down to the discard pile, which is
shuffled into a new deck when the deck runs out. Drafting and buying are hidden from the other
Players, and each Player sees the cards they passed. The hand sits in a dock at the bottom of
the window. While most cards are not implemented, the
setup screen's "Deal the implemented cards first" (on by default) puts the playable ones on
top of the deck.

## How it fits together

```
Rust engine  →  Python engine module (tm_engine)  →  local Python server  →  browser GUI
engine/          built by maturin, used by tests      server/ (FastAPI,       gui/ (React +
                                                      WebSocket)              TypeScript, Vite)
```

Tests, the server and the future AI all go through the Python engine module; nothing
else reaches into the engine.

## Setup (once)

You need [Rust](https://rustup.rs), [uv](https://docs.astral.sh/uv/) and Node.js 22.
Then, in the project folder:

```bash
uv sync
```

```bash
npm --prefix gui install
```

`uv sync` creates `.venv` and builds the engine. After that, `uv run` rebuilds the
engine by itself whenever a Rust file changes, so there is no separate build step.

## Run the tests

```bash
uv run pytest
```

The suite includes about 1,000 fuzzed Games: Random Bot Games with 2–5 Players, checked
after every Decision for things that must never happen, such as a negative Resource, a
Tile on an Area where the rules never allow one, or an Area Decision that offers the
wrong Areas (`tests/fuzzing/invariants.py` lists them all).

## Fuzzing and speed

The full fuzz run plays 100,000 Games on all cores and takes a few minutes:

```bash
uv run python -m tests.fuzzing
```

It starts from a random seed (`--first-seed` repeats a run, `--games` changes how many).
Every failure is saved in `fuzz-failures/` as a Replay file: **Load Replay…** opens it at
the moment it went wrong, with every Player set to human, so **Undo** steps back from there.

The speed benchmark (ADR 0004) reports 2-player Games per second across all cores, how
long copying a Game takes, and how many Decisions per second a Python loop gets through.
It exits with status 1 if a target is missed:

```bash
uv run python -m tools.benchmark
```

## Cards

The printed card data (ADR 0005) comes from the fan-made card list at
ssimeonoff.github.io/cards-list. The import parses a saved copy of that page
(`tools/card_list_snapshot/`) into the card file, `engine/cards/cards.json`, which the engine
builds in:

```bash
uv run python -m tools.card_import
```

`--download` fetches the page, its stylesheet and the card icons again first. Running the
import again rewrites each card's printed fields and keeps any field written by hand. The
engine module reads the catalog with `tm_engine.card_catalog()`.

A card is implemented once it has `"effects"` in the card file (ADR 0009), such as
`"effects": {"production": {"megacredits": -2, "heat": 3}, "tiles": ["ocean"]}` for Black Polar
Dust; cards without it are never offered. Effects can gain or lose Resources, change
Production, raise Temperature and Oxygen, raise Terraform Rating, draw cards and place Tiles.
Declare any new field in `engine/src/cards.rs` first, since the card file allows no unknown
field. Each card's scenario tests live in `tests/cards/test_<id>.py`, and the coverage report
lists the cards that have none yet (the test suite shows the count as a warning):

```bash
uv run python -m tools.card_coverage
```

The mismatch report, `docs/card-mismatches.md`, compares the card file with the open-source
game's card definitions (cost, Tags, Requirements, Victory Points, type and Corporate Era):

```bash
uv run python -m tools.card_mismatches --download
```

Its downloads are GPL-3.0, so they stay in `.cache/` (ignored by git); without
`--download` the report is rebuilt from there.

## Play

Start the server in one terminal:

```bash
uv run python -m server
```

and the GUI in another:

```bash
npm --prefix gui run dev
```

Then open http://localhost:5173. The setup screen asks for the number of Players, each
Player's Controller (human or Random Bot), a seed (empty for a random one) and how fast
Random Bots pick. With two or more humans (Hotseat), or only Random Bots, the screen shows
the full view; with one human, only that Player's Player View.

During a Game, the top bar shows the seed (click to copy) and has **Cards**, **Undo** (back
to the last Decision a human answered, skipping Random Bot picks), **Save Replay**,
**Load Replay…** and the Random Bot speed. **Cards** (also on the setup screen) opens the
card gallery: every card, filtered by type, Tag, or name or number; hover over a card to
enlarge it, or click it to see it large. The server keeps the Game in memory, so
reloading the page picks it up again.

Below the board are your hand and every Player's played cards, grouped into Automated,
Active and Events; hover over a card to enlarge it. A card you can play now is outlined:
click it to play it. When steel or titanium can pay for it, the status bar shows a payment
picker: step the steel and titanium up or down, then **Pay** for the rest in MegaCredits.
In the full view every hand is shown. Player boards show the cards in hand and the Tags in
play.

## Other checks

- Rust lint: `cargo clippy --manifest-path engine/Cargo.toml`
- GUI type check: `npm --prefix gui run typecheck`

## Where things are

| Path | What |
| --- | --- |
| `engine/src/game.rs` | The rules: Game state, Decisions and Options |
| `engine/src/board.rs` | The Tharsis board: Areas, adjacency, and where each Tile may go |
| `engine/src/resources.rs` | The six Resources, and an amount of each (held, or Production) |
| `engine/src/cards.rs` | The card catalog, read from the card file `engine/cards/cards.json`, with each card's effect data |
| `engine/src/playing_cards.rs` | The central card rules: Tag counting, Requirements, payment, carrying out effects, drawing, card Victory Points |
| `engine/src/card_set.rs`, `engine/src/deck.rs` | Hands and played cards (sets of cards), and the deck |
| `engine/src/milestones_and_awards.rs` | The Tharsis Milestones and Awards, and what each one counts |
| `engine/src/scoring.rs` | Final scoring: the breakdown, Award places, ranks and the winner |
| `engine/src/scenario.rs` | Starting a Game from a Scenario |
| `engine/src/replay.rs` | Replays: rebuilding a Game from its start and picks |
| `engine/src/random.rs` | The Game's seeded random numbers |
| `engine/src/random_bot.rs` | Random Bot playouts inside the engine (`Game.play_randomly`), for the benchmark and later search |
| `engine/src/view.rs` | The Player View and Decisions as plain data for Python |
| `engine/src/log.rs` | The game log |
| `engine/src/lib.rs` | The Python bindings (`tm_engine`) |
| `engine/tm_engine.pyi` | The Python API, for your editor |
| `tests/rules/` | Scenario tests of the rules, through `tm_engine` |
| `tests/engine/` | Tests of the engine module itself: views, copies, Replays, reproducibility |
| `tests/server/` | Tests of the local server over its WebSocket |
| `tests/fuzzing/` | The fuzzer: its invariants, the runner, and `python -m tests.fuzzing` for the full run |
| `tools/benchmark.py` | The speed benchmark |
| `tools/card_import.py` | The card import; `tools/card_list_snapshot/` is its saved copy of the card list page |
| `tools/card_mismatches.py` | The mismatch report against the open-source game; the report is `docs/card-mismatches.md` |
| `tools/card_coverage.py` | The coverage report: catalog cards without a scenario test |
| `tests/cards/` | Tests of the card catalog, and each card's scenario tests (`test_<id>.py`) |
| `tests/helpers.py` | `scenario()`, `player()`, `ocean()`, `city()`, `claimed()`, `funded()`, `terraformed_mars()`, `pick()`, `offered()`, `area()`, `milestone()`, `award()`, `resources()`, `hand()`, `played_cards()`, `final_scores()`: helpers that make tests read like play |
| `server/` | The local server and the Random Bot |
| `gui/src/` | The browser GUI; the board is `gui/src/components/MarsBoard.tsx`, the Milestones and Awards bar `gui/src/components/MilestonesAwards.tsx`, and the printed tracks are in `gui/src/tracks.ts` |
| `gui/src/cards/` | Cards drawn as the card list draws them (`PrintedCard.tsx`, `cardList.css`), the card gallery, and the hands and played cards under the board (`PlayerCards.tsx`) |
| `gui/public/card-list/` | The card list's icons and font |
| `CONTEXT.md` | The glossary; code, tests and messages use its terms |
| `docs/adr/` | Architecture decisions |
| `docs/rules-notes.md` | Every rules judgment call |
| `.scratch/phase-1-playable-game/` | The phase-1 spec and tickets |

## Credits

The card faces copy the fan-made Terraforming Mars card list by ssimeonoff
(github.com/ssimeonoff/ssimeonoff.github.io, BSD-3-Clause): its layout, stylesheet and icons.
Its title font, Prototype, is free for personal use. Terraforming Mars is a game by
FryxGames; this is a private, personal project.

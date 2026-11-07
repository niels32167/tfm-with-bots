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
Cards and 12 Corporations, and of the Prelude box's 47 cards (ADR 0011), and the
GUI's card gallery draws every card as the fan-made card list does. Players play Project Cards from their hand, paying with MegaCredits, steel and
titanium, once the cards' Requirements are met; all 208 Project Cards work, 112 Automated, 59 Active
and 37 Events. An Active card's action is an Action its Player may use once per Generation, and
its ongoing effects lower card costs, raise what steel and titanium pay, ease Requirements or
gain its Player something each time a Tile, card or Tag sets them off. A card that takes from
"any Player" lets its Player pick whose Production it lowers or whose Resources it removes.
Special Tiles show their card's symbol on the board, Noctis City, Phobos Space Haven and Ganymede
Colony place their Cities on the Areas reserved for them, and Land Claim marks an Area that only
its Player may place a Tile on. Cards can hold Card Resources, which show on the played cards and may count for Victory Points. At
setup each Player is dealt 2 Corporations and 10 Project Cards, chooses a Corporation and buys any of
the cards for 3 MegaCredits each, all hidden until every Player is done: then each reveals their
Corporation, gets its starting Resources and Production, and pays. All 12 Corporations work, and each
Player's shows on their board with its ability. From Generation 2 each
Research phase has the Draft, on by default and switchable on the setup screen: each Player is
dealt 4 cards, keeps one and passes the rest to their neighbour (clockwise in even Generations,
counter-clockwise in odd ones) until every card is kept, then buys any of the cards kept.
Without the Draft each Player draws 4 cards to buy from. The cards not bought go face down to
the discard pile, which is shuffled into a new deck when the deck runs out. Drafting and buying
are hidden from the other Players, and each Player sees the cards they passed. The hand sits in
a dock at the bottom of the window.

Prelude is a setting of each Game, off by default for now and switchable on the setup screen. With
it, each Player is also dealt 4 Prelude Cards at setup and keeps 2, chosen after their Corporation and
hidden until played; then each Player in player order plays both, in the order they choose, before
Generation 1's first Turn. A Prelude Card that can't be played is discarded for 15 MegaCredits. Played
Prelude Cards stay in play and their Tags count. Prelude is unfinished: 26 of the 35 Prelude Cards work and
only those are dealt, and Prelude's 7 Project Cards join the deck but can't be played yet, nor are its 5
Corporations dealt.

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
Dust; cards without it are never offered, and a Prelude Card without it is never dealt. 21 of
the Prelude box's 47 cards have none yet.
Effects can gain or lose Resources, change
Production, raise Temperature and Oxygen, raise Terraform Rating, draw cards, let the Player
look at cards to keep some of them, place Tiles (special Tiles too, as `"special"`), let the Player
choose between effects (`"choice"`) and claim an Area (Land Claim's `"claim_area"`), add Card
Resources to the card itself or to another of the Player's (`"card_resources"`, `"add_to_another"`;
the card names what it holds in `"holds"`); an Active card can also have an action, which may let
the Player choose between effects too, as well as discounts, steel and titanium values, Requirement steps and Triggers (`"when"`), and an Event an
effect on the next card played.
Declare any new field in `engine/src/cards.rs` first, since the card file allows no unknown
field. Each card's scenario tests live in `tests/cards/test_<id>.py`, and at least one must name the card.
The coverage check lists any implemented card that has none, and then both it and the test suite
fail. A card needs its test as soon as it has `"effects"`; until then the check only counts it as not
implemented yet:

```bash
uv run python -m tools.card_coverage
```

The mismatch report, `docs/card-mismatches.md`, compares the card file with the open-source
game's card definitions (cost, Tags, Requirements, Victory Points, type, Corporate Era and the box
a card comes in), for the base box and Prelude:

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

The screen is laid out like Board Game Arena's: the status bar and the board on the left, with the
Players' areas beneath them, and the Global Parameters, player boards and game log on the right. The
hand is docked at the bottom of the window, showing the tops of the cards; hover over its header to see them whole. The board shows Mars on a NASA image, the Oxygen arc over it,
the thermometer and how many Oceans are left to its right, and the Standard Projects and the
Milestones and Awards around it; those a Decision offers are lit, and clicked there.

During a Game, the top bar shows the seed (click to copy) and has **Cards**, **Save Replay**,
**Load Replay…** and the Random Bot speed. **Undo** is in the status bar, in red: it goes back
to the last Decision a human answered, skipping Random Bot picks. While a Random Bot acts, the
status bar says what it last did; it doesn't pause for a Decision with one Option. **Cards** (also on the setup screen) opens the
card gallery: every card, filtered by type, Tag, or name or number; hover over a card to
enlarge it, or click it to see it large. The server keeps the Game in memory, so
reloading the page picks it up again.

Below the board is an area for each Player, you first: their Resources, Production and Tags, then
their cards in the columns Headquarters, Automated, Effects and Actions. Their Events are folded away
behind the red button. Hover over a card anywhere to see it large with its details. A card you can play now is outlined:
click it to play it. A played card whose action you can use now is outlined too: click it to
use the action. A card whose action is used this Generation turns grey. A card
that holds Card Resources shows how many are on it, next to their icon; when a Decision asks which
card gets or loses some, the cards it offers are outlined, and each is a button in the status bar
too.
When steel or titanium can pay for a card or an action, the status bar shows a payment picker:
step the steel and titanium up or down beside their icons, then **Pay** for the rest in MegaCredits.
In the full view every hand is shown. Player boards show the cards in hand and the Tags in
play.

### The dev panel

For hunting rule bugs, **Dev panel** in the top bar opens a panel beside the game view. It never
changes the Game unless you start from a position in its state editor; closing it brings back the view
you had.

- **Seed:** the Game's seed.
- **Full view:** the board and player boards show what Players hide from each other, and the panel lists
  all hands, the deck from the top and the discard pile. Only this tab sees them.
- **Replay:** step forwards and backwards through every Option picked. The whole screen shows the state
  at that step, the panel the Decision waiting there, its Options (another Player's only in the full view),
  the one picked and the game log so far. Nothing can be picked while looking back, and the Game carries on
  meanwhile.
- **State editor:** edits the position shown as a Scenario: Resources and Production, Terraform Rating,
  Global Parameters, the Generation, who holds the first-player marker and whose Turn it is, cards in a hand
  or among played cards, Card Resources, Corporations and their first action, actions used, Tiles and
  Land Claim. **Start from this position** replaces the current Game, and the engine says if it refuses
  the position. One it accepts but real play can't reach, such as two Cities next to each other, starts and
  is listed at the top of the panel, with why.

**Save Replay** saves such a Game like any other, and **Load Replay…** opens it again. A saved file can
start a scenario test directly:

```python
game = load_game("tests/rules/found_in_the_gui.json")  # from tests/helpers.py
pick(game, "Play Mine")
```

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
| `engine/src/card_resources.rs` | Card Resources on the played cards, and adding them to another card |
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
| `tests/helpers.py` | `scenario()`, `player()`, `ocean()`, `city()`, `claimed()`, `funded()`, `terraformed_mars()`, `pick()`, `offered()`, `area()`, `milestone()`, `award()`, `resources()`, `hand()`, `played_cards()`, `final_scores()`, `load_game()`: helpers that make tests read like play |
| `server/` | The local server and the Random Bot |
| `gui/src/` | The browser GUI; the board is one SVG drawn by `gui/src/components/MarsBoard.tsx` with the parts beside it (`OxygenTrack`, `TemperatureTrack`, `OceanTrack`, `StandardProjects`, `MilestonesAwards`), sharing `boardLayout.tsx`, and the printed tracks are in `gui/src/tracks.ts` |
| `gui/src/components/DevPanel.tsx`, `StateEditor.tsx`, `gui/src/scenario.ts` | The dev panel, its state editor, and the edits it makes to a Scenario |
| `gui/src/cards/` | Cards drawn as the card list draws them (`PrintedCard.tsx`, `cardList.css`), the card gallery, the hand (`HandDock.tsx`), the played cards under the board (`PlayedCards.tsx`), and the zoom on any card (`CardZoom.tsx`) |
| `gui/public/card-list/` | The card list's icons and font |
| `gui/public/mars/` | The NASA image of Mars under the board |
| `CONTEXT.md` | The glossary; code, tests and messages use its terms |
| `docs/adr/` | Architecture decisions |
| `docs/rules-notes.md` | Every rules judgment call |
| `.scratch/phase-1-playable-game/` | The phase-1 spec and tickets |

## Credits

The card faces copy the fan-made Terraforming Mars card list by ssimeonoff
(github.com/ssimeonoff/ssimeonoff.github.io, BSD-3-Clause): its layout, stylesheet and icons.
Its title font, Prototype, is free for personal use. The globe is "Mars Valles Marineris", a Viking 1
Orbiter mosaic by NASA/USGS (JPL PIA04304), public domain, from
commons.wikimedia.org/wiki/File:Mars_Valles_Marineris.jpeg. Terraforming Mars is a game by
FryxGames; this is a private, personal project.

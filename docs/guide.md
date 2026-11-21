# Developer guide

The detailed companion to the [README](../README.md): what the rules engine covers, how to play, and every
tool in the project. The words in capitals (Decision, Option, Controller, Sampled Position, …) are defined in
the glossary, [`CONTEXT.md`](../CONTEXT.md).

## What the engine covers

2–5 Players hold all six Resources with their Production, use
the Sell Patents, Power Plant, Asteroid, Aquifer, Greenery and City Standard Projects, and convert
plants into Greeneries and heat into Temperature on the Tharsis board. They place
Oceans, Greeneries and Cities by clicking a highlighted Area, and collect placement
bonuses, 2 MegaCredits per adjacent Ocean, and the track bonuses for Temperature and
Oxygen. They claim the Tharsis Milestones and fund its Awards from the bar under Mars.
The Game ends after the Generation in which Temperature, Oxygen and Oceans are all
maxed. After a final Greenery conversion, the final score screen shows each Player's
Terraform Rating, Milestones, Awards, Greeneries, Cities and card Victory Points, and the
most Victory Points wins (MegaCredits break a tie). Each Player is a human or a registered Controller, such
as the Random Bot, every Game comes
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

Prelude is a setting of each Game: on by default on the setup screen, and everywhere else off unless named. With
it, each Player is also dealt 4 Prelude Cards at setup and keeps 2, chosen after their Corporation and
hidden until played; then each Player in player order plays both, in the order they choose, before
Generation 1's first Turn. A Prelude Card that can't be played is discarded for 15 MegaCredits. Played
Prelude Cards stay in play and their Tags count; Research Network's wild Tag counts as any Tag for an
action, but never for a Trigger, an Award or Victory Points. Prelude's 7 Project Cards join the deck and
its 5 Corporations the deal, and every card of the Prelude box works: Valley Trust's first action draws 3
Prelude Cards from those nobody was dealt, and Psychrophiles' microbes may pay for plant cards.

## Run the tests

```bash
uv run pytest
```

The suite includes about 1,000 fuzzed Games: Random Bot Games with 2–5 Players, checked
after every Decision for things that must never happen, such as a negative Resource, a
Tile on an Area where the rules never allow one, or an Area Decision that offers the
wrong Areas (`tests/fuzzing/invariants.py` lists them all).

## Fuzzing and speed

The full fuzz run plays 100,000 Games on all cores and takes about 48 minutes. At about one Decision in 25 it
also takes a Sampled Position for a Player at random, checks that it is fair, and plays it to the end:

```bash
uv run python -m tests.fuzzing
```

It starts from a random seed (`--first-seed` repeats a run, `--games` changes how many).
Every failure is saved in `fuzz-failures/` as a Replay file: **Load Replay…** opens it at
the moment it went wrong, with every Player set to human, so **Undo** steps back from there.

The speed benchmark (ADR 0004) reports 2-player Games per second across all cores, how
long copying a Game and making a Sampled Position take, how long encoding a position and its Options takes beside
the Player View (`ai.encoding`), and how many Decisions per second a Python loop gets through, and the mean Generations of Random Bot Games without Prelude and with it. `--prelude`
benchmarks Games with Prelude. It exits with status 1 if a target is missed:

```bash
uv run python -m tools.benchmark
uv run python -m tools.benchmark --prelude
```

## Matches

A Match (ADR 0013) plays two Controllers against each other on all cores: N Games on N/2 seeds, each seed
both ways, 2-player with the Draft and Prelude unless `--no-draft` or `--no-prelude` is given. It reports
each Controller's win rate with a 95% interval, its mean Victory Points, card Victory Points and Terraform
Rating, the mean Generations, and how often Player 1 and the first player won:

```bash
uv run python -m ai.match random_bot random_bot --games 1000
uv run python -m ai.match my_bot random_bot --games 400 --threshold 0.5
```

A Controller is named as registered in `ai/controllers.py`, or as `module:attribute` to try one out. With
`--threshold`, the exit status is 1 unless the low end of the first Controller's interval is above it, so a
step up the ladder is checked by a command; it is 3 if a Game went wrong. Stalled Games (past
`--pick-limit` picks) and Games that went wrong are saved in `match-failures/` as Replay files.

A Controller is handed only a read-only handle: its Player's Player View, the Decision and a random
source, never the Game (`ai/controller.py`). To look ahead, it asks the handle for Sampled Positions:
`handle.sample(seed=...)` gives a new Game with the cards its Player can't see dealt at random, made inside
the engine from the Player View (see "Sampled Positions" in `docs/rules-notes.md`). A Controller that uses
only that random source plays the same way from the same seeds.

The registered Controllers are the Random Bot, the Flat Playout Bot (`flat_playout`), which plays each
Option out at random on 20 Sampled Positions and picks the best mean Victory Point margin (about 14 ms a pick
on average, under 0.2 s at most), the Card Economy Bot (`card_economy`), and the Imitation Bot (`imitation`)
once its model is trained.

### The Card Economy Bot

The Card Economy Bot (`ai/card_economy.py`) compares Options by their Prices (`ai/prices.py`): what things
are worth in MegaCredits to its Player at that moment. Cards being chosen, drafted, bought or sold are
priced from their printed data. Every other Option is picked on one Sampled Position, its own follow-up
Decisions answered quickly, and the position that follows priced: its worth less the other Player's. The
Generations left are estimated once per Decision and held for every Option, or the Bot would refuse to
terraform. It explains any pick:

```bash
uv run python -m ai.explain saved-game.json --step 120
```

The Prices' weights are fitted by Matches, and checked against Recorded Games:

```bash
uv run python -m ai.fit_prices --generations 14 --population 10 --games 100
uv run python -m ai.recorded_games.price_check
uv run python -m tools.setup_choices
```

`ai.fit_prices` tunes every weight with a separable CMA-ES, each candidate playing the starting Bot; it keeps
every core busy for about an hour and writes `.cache/price-fit.json`. `price_check` regresses the final
Victory Point margin on the Players' position differences by Generations left, and prints the coefficients
beside the Bot's Prices. `setup_choices` compares how often the Bot chooses each Corporation and keeps each
Prelude Card with how often Players did. A check's figures may move a starting weight, as the spec allows
(the card in hand's, from 4 to 6), but they are never a fitting target or a model input: they include
held-out Games.

### The Imitation Bot

The Imitation Bot (`imitation`, `ai/imitation/bot.py`) answers every Decision with the Imitation Model, which
predicts the Option strong Players pick there. It is offered once a model is trained; the registered one is
`.cache/models/imitation.pt`, which is private like the dataset it was trained on. Ticket 13's bot, which answered
only setup, the Draft and buying cards and left the rest to the Card Economy Bot, stays registered as
`imitation_draft_buy` with its model in `.cache/models/imitation-draft-buy.pt`. Train, evaluate and check a model
with:

```bash
uv run python -m ai.imitation.train --positions 6000000 --min-rating 450 --prelude-games-only --compile \
  --start-from .cache/models/imitation-draft-buy.pt --out .cache/models/runs/all-decisions.pt
uv run python -m ai.imitation.train --positions 20000000 --min-rating 450 --prelude-games-only --compile \
  --start-from .cache/models/runs/all-decisions.pt --out .cache/models/runs/all-decisions-20m.pt
uv run python -m ai.imitation.evaluate --model .cache/models/imitation.pt
uv run python -m ai.imitation.checks keep-rates --prelude-games-only
uv run python -m ai.imitation.checks synergies --pairs point_luna:business_empire
uv run python -m ai.imitation.checks self-play --games 200 --most-games 4000
```

The registered model is the second run's (about 1 hour 20 minutes), copied to `.cache/models/imitation.pt`.

Games are split by whole Game and by date (`ai/imitation/split.py`): about 80% train, the next 10% choose
between models (validation), and the latest 10% are held out to test; Games without a valid date go by a hash of
their id. Training reads the dataset while it trains: each Game's setup, Draft and buy Decisions come from its
replay through the engine where the replay reaches them (the full Player View) and from its records elsewhere; every
other Decision comes from the replay alone, as far as it goes, leaving out the picks the Recorded Game's log didn't give. Worker
processes encode them, shuffle them and batch them by their Options and card rows (`ai/imitation/positions.py`).
`--start-from` begins a run from another model's weights. A run saves the model,
its encoding format, its settings and its validation results every `--validate-every` positions, and the same
command resumes it. It needs about 3.5 to 4.5 GB of RAM with 10 workers (systemd counted a 5.7 GB peak for the
20M-position run, page cache included): run long ones outside the desktop app, with a cap, so that running out of memory stops the training rather than the app:

```bash
systemd-run --user --same-dir --unit=tm-train -p MemoryMax=6G -p MemorySwapMax=0 uv run python -m ai.imitation.train
```

`evaluate` reports accuracy on held-out Games by Decision kind, Generation, rating and source, beside a random
pick, the most-kept card (keep rates of the training Games, so only at setup, Draft and buy Decisions) and the Card
Economy Bot's pick (at Action-phase Decisions with a handle on the replay's Game). `checks` compares the model's
keep rate for each card at setup with Players', probes whether it gives a Corporation and a Prelude Card a higher
chance together than apart, and sets a bot's Games against itself beside Players' Games: Generations, Victory
Points, Milestones, Awards and how often a funder loses the Award they funded.

### The Value Bot and the self-play loop

The Value Bot (`value`, `ai/value/bot.py`) tries, of the 6 Options the Imitation Model rates likeliest, those it
gives at least half the likeliest Option's chance, each on the same 4 Sampled Positions. It lets the Imitation Model
answer the Decisions that follow from each (a card's Payment, its Tile), and picks the Option after which the **Value
Model** gives its Player the best mean chance of winning. The Value Model is the Imitation Model's transformer with a new head, which reads the Player View alone (no
Decision or Options) and gives the chance of winning and the expected Victory Point margin (`ai/value/model.py`). It
is offered once a model is registered at `.cache/models/value.pt`.

The self-play loop trains it, in a run folder under `.cache/models/value-runs/`:

```bash
systemd-run --user --same-dir --unit=tm-value -p MemoryMax=6G -p MemorySwapMax=0 \
  uv run python -u -m ai.value.loop --minutes 50
journalctl --user -u tm-value -f -o cat            # its progress
uv run python -m ai.value.loop --register          # copy the run's best version to .cache/models/value.pt
```

It warm-starts the Value Model on Recorded Games' results (version v000), rates a fixed panel of old Controllers
against each other, and then plays rounds: Games of the best version against itself and against a pool of earlier
versions, the Imitation Bot and the Card Economy Bot; training a candidate on the last rounds' Games; a gating Match
against the best, which it must score 55% in to replace it; and a rating against the panel, logged in the run's
`ratings.tsv`. The same command resumes a stopped run at the step it was in; `--rounds` and `--minutes` may change,
other settings are fixed by `run.json` and saved with every model, beside the seed and the engine's commit. See the
module's description (`uv run python -m ai.value.loop --help`) for every setting.

The first run (ticket 15, `--minutes 35`, `.cache/models/value-runs/main`) took 36 minutes with 10 Match processes:
- a 5.3-minute warm start, then rounds of about 7 minutes;
- a peak of 4.65 GB anon under the 6 GB cap;
- 17 MB of disk.

A second run (ticket 15, 2026-11-21) started from that v001 with `--start-from` and trained one pass over each
round's Games (`--train-passes 1`, now the default; the first run's fixed 100,000 positions a round were learned by
heart). It took 57 minutes for 6 rounds of 240 Games, and its v006 is now registered. Only a share of each Game's positions is learned from (`--warm-keep`, `--keep`): with every
position, the model learned which Game it was in rather than which positions win.

## Recorded Games

Games humans played on Board Game Arena, from tfmstats.com's log archive (ADR 0012), unpacked into the
gitignored `tm_statistics/` (147 GB, one JSON log per Game and perspective). The importer turns them into a
compact private dataset in `.cache/recorded-games/` (about 1 GB), on all cores, in about 9 minutes:

```bash
uv run python -m ai.recorded_games
uv run python -m ai.recorded_games.tables
```

It keeps 2-player Games on Tharsis with Corporate Era and the Draft, without Colonies, once each however
many perspectives the archive holds, and writes each Player's setup, Draft and buy Decisions with only what
that Player could see, the public position each was made in, the results, and a slim copy of the moves for
rebuilding hands and replaying Games later. Player names are left out; ids are salted hashes. It reports
coverage (Games read, skipped and why, names it couldn't map) and resumes after an interruption; the
format is described in `ai/recorded_games/__init__.py`. The second command prints tables to compare with
the spec and with tfmstats.com. The logs name no licence, so the archive, the dataset and anything trained
from them stay out of git and are never published.

`ai/recorded_games/hands.py` rebuilds each Player's hand move by move from the slim moves (`HandReader`).
Its size matches Board Game Arena's Hand Counter at 99.2% of the moves where that counter is fresh. Which
cards it holds is known by name except after a discard the log doesn't name (Sell Patents, Mars University)
and, in old logs, for the opponent's cards. Ticket 09 has the measurements.

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
Dust; cards without it are never offered. Every card of the catalog has it.
Effects can gain or lose Resources, change
Production, raise Temperature and Oxygen, raise Terraform Rating, draw cards, let the Player
look at cards to keep some of them, place Tiles (special Tiles too, as `"special"`), let the Player
choose between effects (`"choice"`) and claim an Area (Land Claim's `"claim_area"`), add Card
Resources to the card itself or to another of the Player's (`"card_resources"`, `"add_to_another"`;
the card names what it holds in `"holds"`); an Active card can also have an action, which may let
the Player choose between effects too, as well as discounts (per card, or per Tag with `"per_tag"`), steel and
titanium values, Requirement steps and Triggers (`"when"`), and an Event an effect on the next card played. A
Corporation's `"first_action"` may draw cards, place a Tile, fund an Award (`"fund_award"`) or draw Prelude Cards to
play one (`"prelude_cards"`).
Declare any new field in `engine/src/cards.rs` first, since the card file allows no unknown
field. Each card's scenario tests live in `tests/cards/test_<id>.py`, and at least one must name the card.
The coverage check lists any implemented card that has none, and then both it and the test suite
fail. A card needs its test as soon as it has `"effects"`; until then the check only counts it as not
implemented yet:

```bash
uv run python -m tools.card_coverage
```

The mismatch report, `docs/card-mismatches.md`, compares the card file with the open-source
game's card definitions (cost, Tags, Requirements, Victory Points, type, Corporate Era, the box
a card comes in, and the MegaCredits a Corporation starts with or a Prelude Card gains or pays),
for the base box and Prelude:

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
Player's Controller (human, or a registered Controller such as the Random Bot), a seed (empty for a
random one) and the bot speed: how long each of their picks takes at least. With two or more humans
(Hotseat), or none, the screen shows the full view; with one human, only that Player's Player View. A
registered Controller thinks in a worker thread, so the server stays responsive while it does.

The screen is laid out like Board Game Arena's: the status bar and the board on the left, with the
Players' areas beneath them, and the Global Parameters, player boards and game log on the right. The
hand is docked at the bottom of the window, showing the tops of the cards; hover over its header to see them whole. The board shows Mars on a NASA image, the Oxygen arc over it,
the thermometer and how many Oceans are left to its right, and the Standard Projects and the
Milestones and Awards around it; those a Decision offers are lit, and clicked there.

During a Game, the top bar shows the seed (click to copy) and has **Cards**, **Save Replay**,
**Load Replay…** and the bot speed. **Undo** is in the status bar, in red: it goes back
to the last Decision a human answered, skipping the registered Controllers' picks. While one acts, the
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
- **Bot:** at a step a registered Controller answers, why it picks what it picks, as `ai.explain` gives it:
  every Option priced, best first, with the Prices that changed most. Another Player's reasons show only in
  the full view, as their Options show their hand.
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
| `server/` | The local server, which asks registered Controllers for their picks |
| `ai/` | Controllers and the tools that compare them: the handle a Controller is given (`controller.py`), the registered Controllers (`controllers.py`), the Random Bot (`random_bot.py`), the Flat Playout Bot (`flat_playout.py`) and the Match tool (`match.py`) |
| `ai/recorded_games/` | The Recorded Game importer (`build.py`, run as `python -m ai.recorded_games`), one log to a dataset entry (`importer.py`), names to catalog ids (`names.py`), the slim moves (`moves.py`), reading the dataset (`dataset.py`) and its comparison tables (`tables.py`) |
| `tests/ai/` | Tests of fair play, the registered Controllers the Match tool and the Recorded Game importer |
| `ai/imitation/` | The Imitation Model: the train/validation/test split (`split.py`), training positions read and encoded while training (`positions.py`), the model (`model.py`), the training command (`train.py`), accuracy against baselines (`evaluate.py`), keep-rate and synergy checks (`checks.py`) and the Imitation Bot (`bot.py`) |
| `gui/src/` | The browser GUI; the board is one SVG drawn by `gui/src/components/MarsBoard.tsx` with the parts beside it (`OxygenTrack`, `TemperatureTrack`, `OceanTrack`, `StandardProjects`, `MilestonesAwards`), sharing `boardLayout.tsx`, and the printed tracks are in `gui/src/tracks.ts` |
| `gui/src/components/DevPanel.tsx`, `StateEditor.tsx`, `gui/src/scenario.ts` | The dev panel, its state editor, and the edits it makes to a Scenario |
| `gui/src/cards/` | Cards drawn as the card list draws them (`PrintedCard.tsx`, `cardList.css`), the card gallery, the hand (`HandDock.tsx`), the played cards under the board (`PlayedCards.tsx`), and the zoom on any card (`CardZoom.tsx`) |
| `gui/public/card-list/` | The card list's icons and font |
| `gui/public/mars/` | The NASA image of Mars under the board |
| `CONTEXT.md` | The glossary; code, tests and messages use its terms |
| `docs/adr/` | Architecture decisions |
| `docs/rules-notes.md` | Every rules judgment call |
| `.scratch/phase-1-playable-game/` | The phase-1 spec and tickets |

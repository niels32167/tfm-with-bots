# Terraforming Mars

A digital Terraforming Mars with a fast rules engine, built so an AI opponent can later
be trained against it by self-play. Phase 1 is a playable, well-tested game; see
`.scratch/phase-1-playable-game/spec.md`.

So far (tickets 01–06), 2–5 Players hold all six Resources with their Production, use
the Power Plant, Asteroid, Aquifer, Greenery and City Standard Projects, and convert
plants into Greeneries and heat into Temperature on the Tharsis board. They place
Oceans, Greeneries and Cities by clicking a highlighted Area, and collect placement
bonuses, 2 MegaCredits per adjacent Ocean, and the track bonuses for Temperature and
Oxygen. They claim the Tharsis Milestones and fund its Awards from the bar under Mars.
The Game ends after the Generation in which Temperature, Oxygen and Oceans are all
maxed. After a final Greenery conversion, the final score screen shows each Player's
Terraform Rating, Milestones, Awards, Greeneries and Cities, and the most Victory Points
wins (MegaCredits break a tie). Each Player is a human or a Random Bot, every Game comes
from a seed, and any Game can be undone, saved as a Replay file and loaded again. A
fuzzer plays Random Bot Games and checks them after every Decision, and a benchmark
measures the engine's speed.

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

During a Game, the top bar shows the seed (click to copy) and has **Undo** (back to the
last Decision a human answered, skipping Random Bot picks), **Save Replay**,
**Load Replay…** and the Random Bot speed. The server keeps the Game in memory, so
reloading the page picks it up again.

## Other checks

- Rust lint: `cargo clippy --manifest-path engine/Cargo.toml`
- GUI type check: `npm --prefix gui run typecheck`

## Where things are

| Path | What |
| --- | --- |
| `engine/src/game.rs` | The rules: Game state, Decisions and Options |
| `engine/src/board.rs` | The Tharsis board: Areas, adjacency, and where each Tile may go |
| `engine/src/resources.rs` | The six Resources, and an amount of each (held, or Production) |
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
| `tests/helpers.py` | `scenario()`, `player()`, `ocean()`, `city()`, `claimed()`, `funded()`, `terraformed_mars()`, `pick()`, `offered()`, `area()`, `milestone()`, `award()`, `resources()`: helpers that make tests read like play |
| `server/` | The local server and the Random Bot |
| `gui/src/` | The browser GUI; the board is `gui/src/components/MarsBoard.tsx`, the Milestones and Awards bar `gui/src/components/MilestonesAwards.tsx`, and the printed tracks are in `gui/src/tracks.ts` |
| `CONTEXT.md` | The glossary; code, tests and messages use its terms |
| `docs/adr/` | Architecture decisions |
| `docs/rules-notes.md` | Every rules judgment call |
| `.scratch/phase-1-playable-game/` | The phase-1 spec and tickets |

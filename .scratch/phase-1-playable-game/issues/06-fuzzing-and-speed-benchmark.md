# 06 — Fuzzing and speed benchmark

**What to build:** Tooling that hammers the engine and measures its speed (ADR 0004).

A Random Bot playout runs inside the engine and is exposed through the Python engine module. A fuzz runner plays Random Bot Games with 2–5 Players (Draft on and off, once ticket 10 lands), checks invariants after every Decision, and saves a Replay for every failure. A short run is part of the normal test suite; the full 100,000-Game run is a separate command that uses all cores.

A benchmark command reports:
- 2-player Random Bot Games per second across all cores;
- how long a copy of a Game takes;
- for information only, how many Decisions per second a Python loop achieves.

Invariants for rules that don't exist yet apply as soon as their ticket lands.

**Blocked by:** 02 — New Game setup, seed, undo and Replays

**Status:** ready-for-agent

- [x] After every Decision, the fuzzer checks:
  - no negative Resources;
  - Production within its limits;
  - Global Parameters within range;
  - Tiles only on legal Areas;
  - at most three Milestones claimed and three Awards funded;
  - every Decision has at least one Option.
- [x] Per Game, the fuzzer checks that it ends within a generous Generation limit (a fuzzing guard, not a rule) and that the score breakdown adds up.
- [x] Every failure is saved as a Replay that reproduces it when loaded.
- [x] About 1,000 fuzzed Games run with the normal test suite, and the full 100,000-Game run is one command.
- [x] The benchmark is one command, and its first numbers are recorded under Comments in this ticket.

## Comments

### 2026-10-23 — implemented (Claude)

**Decisions made with the user:**
- **Test seam:** the Python engine module only.
  - `tests/engine/test_random_playouts.py` covers the in-engine Random Bot playout.
  - `tests/fuzzing/` holds the invariants, each with a test that breaks exactly that thing in a real view, plus the runner and the ~1,000-Game run.
  - `tests/tools/test_benchmark.py` checks that the benchmark still runs.
  - No server changes. In the browser, a saved failure (from a planted invariant) opened at the moment it broke, and Undo went back to the Decision before it.
- **Commands and files:**
  - `uv run python -m tests.fuzzing` plays 100,000 Games on all cores from a random first seed (`--first-seed`, `--games` and `--processes` change that).
  - `uv run python -m tools.benchmark` runs the benchmark.
  - Failures are saved in `fuzz-failures/` (gitignored) as Replay files with every Player set to human.
- **"Tiles only on legal Areas" is strict:**
  - After every Decision, every Tile must sit where its type may go: Oceans on Ocean Areas with no owner, Greeneries and Cities on unreserved Areas of Mars with an owner, and no two Cities adjacent.
  - Every Area Decision must offer exactly the legal Areas, worked out in Python from the printed board (`ADJACENT_AREAS` in `tests/helpers.py`), including the rule that a Greenery goes next to its owner's Tiles when it can.
- **Scenarios refuse a Terraform Rating below 5,** so MegaCredit Production −5 can never take MegaCredits below 0 (see `docs/rules-notes.md`).

**Design notes:**
- **Engine:**
  - `engine/src/random_bot.rs`: `Game.play_randomly(seed=…, picks=None)` picks random Options inside the engine. It draws on its own SplitMix64 (never the Game's) and records its picks in the Replay like any others.
  - `Game::apply_pick(&decision, index)` is the one place a pick is recorded and carried out. `pick` checks the index first; the playout works out each Decision only once.
  - **Neighbour table:** `board.rs` now works out each Area's neighbours once (`ADJACENT_AREAS`, a `LazyLock`). Playouts got 23 % faster (quartiles 1.22–1.25 over 30 rounds), measured in one process switching between the two ways every half second, because separate runs on the power-saver profile varied up to threefold. Legal Areas are still worked out for every Decision; at this speed there was no need to go further.
- **Test helper:** `play_randomly` in `tests/helpers.py` now calls the engine's playout instead of running its own Python Random Bot.
- **Fuzzer** (`tests/fuzzing/`):
  - Game `seed` has 2 + seed % 4 Players, and its Random Bot picks come from `random.Random(seed)`.
  - After every Decision it runs the seven checks in `invariants.AFTER_EVERY_DECISION`.
  - At the end it runs `score_breakdown_adds_up`:
    - the six parts add up to the total;
    - Terraform Rating, Milestones (5 each), Greeneries, Cities (adjacent Greeneries) and MegaCredits agree with the board;
    - ranks follow Victory Points, then MegaCredits.
  - Guards: 100 Generations and 50,000 picks.
  - What a failure saves:
    - a broken invariant: the Replay up to that position;
    - an error on a pick (a Rust panic arrives as a `BaseException`): the Replay up to just before it, plus `failing_pick`. So the file still loads in the GUI (the server checks the whole Replay first), and picking `failing_pick` there raises the error again;
    - an error while checking: the Replay of that position.
  - The suite's run uses seeds 0–999, a fixed regression set. The full run starts from a random seed, so repeated runs explore new Games.
- **Benchmark** (`tools/benchmark.py`):
  - Worker processes start together at a barrier.
  - A copy is timed as the fastest of 5 × 10,000 copies.
  - The exit status is 1 if a target is missed.
  - ADR 0004 asks for copies "in microseconds". Claude read that as under 10 µs.

**First numbers** (2026-10-23). The machine is an AMD Ryzen 7 8845HS: 8 cores with 2 threads each, so `os.cpu_count()` is 16. Linux's power profile was "power-saver" throughout.

| | On battery | On mains |
| --- | --- | --- |
| 2-player Games per second, 16 processes (target 1,000) | 123,784–129,625 | 187,313 |
| 2-player Games per second, 1 process | about 5,000 | 18,130 |
| Copy at the start (0 picks, 1 log line) | 0.20 µs | 0.21 µs |
| Copy halfway (93 picks, 212 log lines) | 0.33 µs | 0.32 µs |
| Copy at the end (187 picks, 458 log lines) | 0.63 µs | 0.65 µs |
| Python loop, Decisions per second (for information) | about 210,000 | 223,406 |

- **Power-saver:** one busy process runs at a low clock, so on battery the single-process figure swung between 4,900 and 13,400 Games per second in identical runs. The all-core figure is the one ADR 0004 asks for.
- **Fuzzing:** 100,000 Games with 2–5 Players and 20,549,284 Decisions took 213 s with no failures. The longest Game lasted 36 Generations. That run was before the code review fixes. A rerun on the final code (seeds from 7,778,755,389,001,349) played 100,000 Games and 20,553,492 Decisions in 239 s, again with no failures and a longest Game of 36 Generations.
- **Copy cost:**
  - A log event is still 40 bytes. `AwardPlace` is 16, and `Produced`, which carries a `Resources`, is still the largest.
  - The Game itself is 1,952 bytes, mostly the board's 63 Areas.
  - At the end of a 2-player Game the log adds about 18 KB and the Replay's picks 1.5 KB.
  - These sizes were measured with a throwaway compile-time probe; nothing in the code asserts them.
- **Game length:** a 2-player Random Bot Game is about 190 Decisions (205 on average over 2–5 Players), not ADR 0004's "roughly 800 Decisions" with Draft and cards. The speed target needs checking again once cards and Draft exist.
- **Final Greenery conversion:** random play now reaches it in about 12–17 Games out of 100, because placement bonuses give plants. Ticket 04's note said it never did.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - "seat", a glossary _Avoid_ word, in docstrings, a test name, the benchmark report and the README.
  - Unbounded loops:
    - the fuzzer's per-Game loop now has a pick guard as well as the Generation guard;
    - the tests' calls to the engine playout pass `picks=MAX_PICKS`;
    - the benchmark's loops stop at `MAX_PICKS`.
  - `apply_pick(index, option)` could record one index and carry out a different Option, which would break Replays (ADR 0010). It now takes the Decision and the index.
  - A panic while reading the Decision or the view, or an error inside a check, escaped `fuzz_game`. It would have stopped the whole run without saving anything; it is now saved as a failure.
  - An engine error on a pick saved a Replay that ended with the failing pick, which Load Replay refuses. The Replay now stops before it, and the file has `failing_pick`.
  - The benchmark exits with status 1 on a missed target, and copies now have a target.
  - The score check now also confirms Milestones, Greeneries and Cities against the board.
  - The test helper and the engine both had a Random Bot called `play_randomly`; the helper now calls the engine.
  - Naming:
    - `board` became `player_board` for a Player's board in the checks;
    - the `Decision` alias no longer includes "no Decision";
    - `fuzz_game` no longer has a closure that reads a variable assigned later.
- Left as is:
  - `processes or os.cpu_count()` and the `--processes` option appear in both commands.
  - A "pick at random" loop still appears in the server's Random Bot, the fuzzer and the benchmark's Python loop. Each is that place's own Controller loop, and the benchmark measures exactly that loop.
  - The score check doesn't work out Award places again; the rules tests cover them.
  - Beyond the ticket text:
    - the single-process Games-per-second line;
    - `picks=` on the playout, which the test helper uses;
    - the extra checks: the Ocean track against the Ocean Tiles, scores against the board, ranks, and "over but still waiting on a Decision".

    They are cheap and serve the same purpose.

**Open points:**
- **Ticket 10:** fuzz with Draft on and off. `fuzz_game` needs a Draft setting, and `players_for` becomes a settings function.
- **Tickets 08–09:**
  - add "card count conserved across deck, discard, hands, played cards and Draft" to `AFTER_EVERY_DECISION`;
  - add the `cards` score part to `parts_shown_on_the_board`.
- **Ticket 18:** `tiles_only_on_legal_areas` and `legal_areas` must learn about:
  - Noctis City and the two Areas off Mars;
  - special Tiles;
  - cards that change placement rules (Mangrove, Research Outpost, Urbanized Area and others).

  "No two Cities adjacent" does not hold for Noctis City.
- **Ticket 24:**
  - rerun the benchmark and the 100,000 Games with cards and Draft;
  - the "16 processes" are hardware threads on 8 cores.
- **Benchmark conditions:** on the power-saver profile the numbers are a lower bound. For the best figures, run on mains with the "balanced" or "performance" profile.
- **Suite time:** the ~1,000-Game run takes 2–5 s on 16 processes, and the whole suite now takes 5–12 s, depending on the CPU's state.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.

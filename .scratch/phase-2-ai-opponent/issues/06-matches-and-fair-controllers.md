# 06 — Matches and fair Controllers

**What to build:** The new `ai/` package with the Controller seam, and one command that plays a Match. The Random Bot becomes the first Controller using the seam. Every later rung is judged by this tool, so it comes first.

**The seam:** a Controller is given a read-only handle and returns an Option's index. The handle offers the Player View and the Decision, and Sampled Positions once ticket 07 adds them. It never gives access to the Game (ADR 0013).

**A Match:** two Controllers play N seeds, each Controller taking each Player on every seed. Each Game runs in its own process on all cores, and failures are saved as Replays.

**In the GUI:** the setup screen lists registered Controllers for each Player, as well as human and Random Bot, and the server asks the Controller for its pick. A slow Controller must not freeze the server's event loop.

**Blocked by:** none

**Status:** ready-for-agent

- [x] `uv run python -m ai.match <a> <b> --games N` reports each Controller's win rate with a 95% interval, mean Victory Points, Generations, card Victory Points and Terraform Rating, and which Player won more often.
- [x] It exits with a chosen status when a threshold is missed, so that a ladder step can be checked by a command.
- [x] A guard ends a Game that doesn't finish within a pick limit, and the report counts these as stalled.
- [x] The same seeds and Controllers give the same results, for Controllers that use only their given random source.
- [x] Test: nothing reachable from the handle gives the Game, its copies, or another Player's hidden cards.
- [x] The first Match is recorded under Comments: Random Bot against itself, as a check that the tool shows about 50% (and how far first player and Player order shift that).
- [x] The GUI can play a Game with a registered Controller as a Player, at a usable speed, and undo and Replays still work.

## Comments

### 2026-11-07 — implemented (Claude)

Every box is ticked. The new `ai/` package holds the seam (`ai/controller.py`), the registered Controllers
(`ai/controllers.py`), the Random Bot (`ai/random_bot.py`) and the Match tool (`ai/match.py`); the server and
GUI now ask registered Controllers for their picks.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **The seam:** `Controller.pick(handle) -> int`. The handle is a frozen dataclass of plain data: `player`,
  `player_view`, `decision` and `random` (a `random.Random` the Match or server gives it). The Player View is
  built for every Decision (about 42 µs). Ticket 07 adds Sampled Positions, made inside the engine, so that
  the Game stays in Rust.
- **The registry:** `ai/controllers.py` maps a name (`"random_bot"`) to a label and a factory; each Player in
  each Game gets a Controller of their own. The Match tool also takes `module:attribute` names, to try a
  Controller out before registering it; the server never does, since a Replay file must not import code.
- **Match defaults:** 2 Players, Corporations, Draft and Prelude (ADR 0011), with `--no-draft` and
  `--no-prelude`. `--games N` counts Games, must be even, and plays N/2 seeds from `--first-seed` (0) both
  ways. A draw counts as half a win. The pick limit is 5,000 (`--pick-limit`); a Game past it is stalled
  and counts towards neither win rate. `--threshold P`: the exit status is 1 unless the low end of the first
  Controller's 95% (Wilson) interval is above P. It is 3 if a Game went wrong, and 2 for wrong arguments.
  Stalled and failed Games are saved as Replay files in `match-failures/` (gitignored).
- **Replay files** name Controllers by registry name, so old Replays (`"human"`, `"random_bot"`) load
  unchanged; an unknown name is refused with the known ones listed.
- **The server** builds the handle on the event loop and runs only `controller.pick(handle)` in
  `asyncio.to_thread`. The bot delay (now "Bot speed" in the GUI) is the least time a pick takes, thinking
  included. There is still no pause while drafting or buying, or for a Decision with one Option. A pick that
  comes back after an undo, a load or a new Game is dropped (by sequence number and session). Controllers are
  made afresh after an undo. A Controller that raises, or picks an Option not offered, is reported to the GUI
  as an error, and the Game waits.

**Reproducibility.** In a Match, each Controller's random source is `random.Random(f"{seed}/{side}/{player}")`,
where side is 0 for the first Controller named. So a Controller playing itself doesn't play the same Game twice
on a seed; otherwise a mirror Match would show exactly 50% and prove nothing. On the server it stays
`f"{seed}/{sequence}"`, as before, so the Random Bot picks exactly as it did and undo brings the same picks.
A test runs the same Match twice on 1 process and once on 2, and compares the whole results.

**Fair play.** `tests/ai/test_fair_play.py` plays 6 Prelude Games with the Draft (seeds 7 to 12, one with 3
Players), all the way through. At every Decision it walks everything reachable from the handle (with
`gc.get_referents`, not following classes or modules) and asserts two things: no `tm_engine.Game` is
reachable, and no card the deciding Player can't see is either. Hidden cards are every card id in
`full_view()` and `to_scenario()` that the Player View and Decision don't name. They include other hands,
Corporations and Prelude Cards being chosen, cards under way in the Draft or being bought, the deck, the
discard pile and the Prelude deck. The test also remembers cards that left the Game while hidden: the Prelude
Cards not kept at setup, and Valley Trust's 2 discards (seeds 9 and 12 have Valley Trust draw, and the test
asserts one did). A further test shows the check can fail: a handle holding an opponent's card, or a bound
`game.copy`, is caught.

**Limit, from the code review.** The handle guarantees only that nothing hidden is handed over. Python
can't stop a Controller that cheats on purpose: one that imported the engine could make Games from small
Match seeds until the deal matched its own. So no Controller may import `tm_engine`. Only `ai/controller.py`,
which builds handles, and `ai/match.py` may, and `test_no_controller_imports_the_engine` checks it. The random
source is a hash of the seed and can't be inverted, but trying seeds against it would work just as well, so
seeding it apart from the Game seed wouldn't close this hole.

**The first Match:** Random Bot against itself, 20,000 Games on seeds 0 to 9,999, each played both ways, with
Prelude and the Draft. Run on commit c2c2c80 plus this work, on the laptop on mains (`online` 1), in the
"performance" profile, on 16 processes, in 75 s (265 Games per second):

```
uv run python -m ai.match random_bot random_bot --games 20000 --threshold 0.45

                                     a: random_bot       b: random_bot
  Win rate                                   49.6%               50.4%
    95% interval                       48.9%–50.3%         49.7%–51.1%
  Wins / draws / losses           9912 / 7 / 10081    10081 / 7 / 9912
  Mean Victory Points                         77.9                78.1
  Mean card Victory Points                     5.3                 5.3
  Mean Terraform Rating                       43.1                43.1

Mean Generations: 17.84
Player 1 won 50.5% of finished Games, Player 2 49.4%; the first player won 49.8%.
Finished: 20,000, stalled: 0, failed: 0.
```

- **The tool shows about 50%.** a's interval, 48.9–50.3%, holds 50%, so the tool shows no difference between
  the two sides.
- **Player order and going first barely matter for Random Bots.** Player 1 won 50.5% (±0.7 points at 95%,
  so not significant), and the first player won 49.8%. Random Bots play too badly for going first to count.
  Stronger Controllers may differ, and each Match reports it.
- **Other checks:** 7 draws (0.04%). The mean Generations, 17.84, agree with ticket 05's benchmark (17.87 with
  Prelude). A run without Prelude (2,000 Games, `--no-prelude`) gave 21.07, against the benchmark's 20.99, and
  51.8% (49.6–54.0%). With `--threshold 0.5` that exits 1, as a ladder check should.
- **Speed:** one process plays 32 Games per second, about 17,300 picks per second, or 58 µs a pick. 42 µs of
  that is building the Player View for the handle. A raw Python loop does 270,000 Decisions per second because
  it reads no view. If search needs more speed, the place to look is a lighter view.

**The GUI.** The server sends `{"type": "controllers", ...}` after the card catalog: a human, then the
registered Controllers with their labels. The setup screen, player boards and status bar take names and labels
from it, and the top bar shows "Bot speed" whenever any registered Controller plays. Browser check at 1440x900
(server on port 8001 and vite on 5174, as the previous session's servers still held 8000 and 5173):
- The setup screen listed Human and Random Bot from the server.
- A Human-vs-Random-Bot Game, seed 2 with Prelude, went through setup. The Random Bot chose, kept and bought
  without pausing. At 0.8 s per pick it played its Prelude Cards in 809 ms, and its 9-pick Turn in about 7 s.
- The status bar read "Player 2 (Random Bot) is taking their Turn…".
- **Undo** went back to the human's second-Action Decision.
- **Save Replay** and **Load Replay** went through a second WebSocket, to avoid a download: the file had
  `["human", "random_bot"]` and Prelude, and it loaded with undo still available.
- **End Turn** then brought the Random Bot's same Turn: the same last 3 log lines, and step 30 as before.
- There were no console errors.
- Server tests cover a Controller that thinks for 1 s: the server answers a Save Replay meanwhile in under
  0.5 s, and a pick that comes back after an undo is dropped. That test fails with both guards removed.

**Checks:** 1,997 tests pass in 46 s. Clippy and `cargo fmt --check` are clean (the engine is unchanged), and
`npm --prefix gui run build` succeeds. On the touched files, `ruff check` finds only its old hits (TRY004 in
`server/app.py`, UP037 twice in `server/session.py`). `ruff format --line-length 120` agrees, except for keeping
`except (KeyboardInterrupt, SystemExit)` in parentheses, as `tests/fuzzing/runner.py` does.

**The code review against c2c2c80** (Standards and Spec, in parallel):
- **Fixed:**
  - README now covers `ai/`, Matches and the bot speed.
  - CONTEXT.md gains Registered Controller and Handle.
  - A Controller's name is `ControllerName` in the server and GUI, so that `Controller` keeps its glossary
    meaning.
  - The Option check is one function, `ai.controller.offered`.
  - The label lookup is one function, `server.session.label_of`.
  - The threshold test is one method, `Side.above`.
  - The Match tool lost its duplicate argument checks, its job tuple, and a Corporations setting no flag
    could change.
  - The GUI uses one `HUMAN` constant.
  - The no-engine-import guard was added (above).
- **Left:**
  - The test Controllers `FirstOption` and `Broken` are written out in both `tests/ai/test_match.py` and
    `tests/server/test_registered_controllers.py`.
  - A Game that kills its worker process outright, rather than raising, would end the Match with
    `BrokenProcessPool` and save no Replay. Engine panics arrive as exceptions and are caught, so none is
    known.
  - A failure Replay naming a `module:attribute` Controller won't open in the GUI, which refuses such names.
    The docstring and README say so.


# 02 — New Game setup, seed, undo and Replays

**What to build:** A new-Game screen, plus the reproducibility that ADR 0010 promises.

On the setup screen the user can:
- choose 2–5 Players;
- set each Player's Controller to human or Random Bot;
- enter a seed or let one be picked at random;
- set how fast Random Bots move.

With more than one human Controller (Hotseat), the GUI shows the full view with all hands; with one human, it shows only that Player's Player View. The first-player marker moves to the next Player every Generation.

In the engine, a Game can be copied, exported as a Replay, loaded from a Replay, and rebuilt at any step of its Replay. In the GUI, the user can undo back to their previous Decision and save or load Replay files.

**Blocked by:** 01 — Walking skeleton

**Status:** ready-for-agent

- [x] The engine and the setup screen support 2–5 Players, and the first-player marker rotates every Generation.
- [x] Controllers can be set per Player. Hotseat shows the full view; a single human sees only their own Player View.
- [x] The seed is shown and can be entered.
- [x] Test: the same settings, seed and Options always give an identical Game and game log, also when replayed in a separate process.
- [x] Test: changing a copied Game never changes the original.
- [x] Test: exporting and loading a Replay gives back the same Game, including Games started from a Scenario.
- [x] Undo in the GUI returns to the human's previous Decision, skipping Random Bot moves, any number of times.
- [x] Replay files can be saved and loaded from the GUI.
- [x] Random Bot speed is adjustable in the GUI.

## Comments

### 2026-10-22 — implemented (Claude)

**Decisions made with the user:**
- Tests go through two seams: the Python engine module, and the server's WebSocket for undo, which view the GUI gets, Replay files and Random Bot speed. The GUI was checked by hand in the browser.
- The first player of a new Game is drawn from the seed (spec story 8), so the engine now has its seeded random number generator. A Scenario sets the first player itself; the default is Player 1.
- A Game with only Random Bots shows the full view, like Hotseat.
- A Replay file holds the engine's Replay plus each Player's Controller, so loading one resumes the Game with the same humans and Random Bots.

**Design notes:**
- **Replay:** `{"start": {"settings": {...}} or {"scenario": {...}}, "picks": [...]}`. The Game keeps its own Replay as it is played (`engine/src/replay.rs`). `Game.from_replay(replay, step=n)` rebuilds the Game after the first n picks.
- **Random numbers:** SplitMix64, written out in `engine/src/random.rs`, so the numbers can't change with a crate update.
- **Seeds:** at most 2^53 − 1 (`tm_engine.MAX_SEED`). Replays travel as JSON, and the browser keeps whole numbers exact only up to there.
- **Undo:** the server rebuilds the Replay at the last Decision a human answered. A Random Bot's pick depends only on the seed and the Decision's sequence number, so making the same human picks again after an undo, or after loading a Replay file, gives the same Game.
- **Game log:** every Generation now begins with "Generation n begins, with Player p as first player."
- **Controls:** until the dev panel (ticket 22) exists, the seed, Undo, Save Replay, Load Replay… and the Random Bot speed sit in the top bar.
- **Small extras:** clicking the seed copies it (story 74), and the final scores have an Undo button.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Replay files could change a seed above 2^53 when the browser read them; seeds now stop at 2^53 − 1.
  - Random Bot picks now come from the seed and sequence number, so undo and loading no longer change what the bots pick.
  - the glossary's _Avoid_ term "move";
  - `set_out` became `prepare` and `begin`;
  - the undo history is named by sequence numbers;
  - the Rust `PlayerView` struct became `View`, since it also holds the full view;
  - duplicated Controller lists, labels and Option matching;
  - "You" now comes from the server's viewer;
  - a hard-coded Asteroid cost in a test.
- Left as is:
  - "step" for a position in a Replay, which is the spec's own word ("rebuilt at any step of its Replay");
  - the setup screen's hint about Hotseat and the full view, which has to be worked out before the server has a Game;
  - one test that waits 0.6 s to show a stopped Random Bot stays stopped.

**Open points:**
- **Copy cost:** a Game now carries its Replay, which grows with every pick, as the log does. Ticket 06's copy-time benchmark should check both against ADR 0004.
- **Glossary:** "full view" and "first player" are used in the spec and code but are not in CONTEXT.md yet. They are candidates for `/domain-modeling`.
- **Status line:** it is still `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.

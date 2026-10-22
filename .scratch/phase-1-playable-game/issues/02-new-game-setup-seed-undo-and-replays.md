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

- [ ] The engine and the setup screen support 2–5 Players, and the first-player marker rotates every Generation.
- [ ] Controllers can be set per Player. Hotseat shows the full view; a single human sees only their own Player View.
- [ ] The seed is shown and can be entered.
- [ ] Test: the same settings, seed and Options always give an identical Game and game log, also when replayed in a separate process.
- [ ] Test: changing a copied Game never changes the original.
- [ ] Test: exporting and loading a Replay gives back the same Game, including Games started from a Scenario.
- [ ] Undo in the GUI returns to the human's previous Decision, skipping Random Bot moves, any number of times.
- [ ] Replay files can be saved and loaded from the GUI.
- [ ] Random Bot speed is adjustable in the GUI.

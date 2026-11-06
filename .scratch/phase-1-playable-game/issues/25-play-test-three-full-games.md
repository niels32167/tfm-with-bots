# 25 — Play-test three full Games

**What to build:** The user plays complete Games in the GUI to confirm that the rules feel right. Include at least one Game against a Random Bot and one Hotseat Game with three or more Players, with Draft on.

Every rule bug found is saved as a Replay, filed as a new ticket and fixed. Play-testing continues until three complete Games in a row have no rule bug.

**Blocked by:** 22 — Dev panel; 23 — Visual polish; 24 — Phase-1 exit checks

**Status:** ready-for-human

- [ ] Three complete Games in a row played without finding a rule bug.
- [ ] Every bug found along the way has a ticket with its Replay and a regression test.

## Comments

### 2026-11-05 — note from ticket 21 (Claude)

Worth watching while playing: choosing a Corporation with the 10 Project Cards shown small above it, Helion's payment Decision with many splits (the heat stepper), and being asked how to pay with heat right after Done in a Research phase.

### 2026-11-06 — hand-off from ticket 22 (Claude)

For a bug found in play: **Dev panel** in the top bar steps back through the Game and shows the Decision and Option picked at each step. **Save Replay** gives the file for the ticket, and `load_game(path)` in `tests/helpers.py` starts its regression test from that file. The state editor can cut it down to the position that matters.

### 2026-11-06 — hand-off from ticket 23 (Claude)

The board now scales to the window as one picture. At 1366×768, its smallest, it is 609 px wide, or 695 px with the hand folded, so the Milestones and Awards text is about 6.5 px. In play, say whether that reads well enough, or whether the board should take more of the height there.

### 2026-11-06 — hand-off from ticket 24 (Claude)

The exit checks are done, so this ticket is unblocked: 100,000 fuzzed Games were clean, with every card and Corporation played. The setup screen no longer has "Deal the implemented cards first", so new Games deal from the whole shuffled deck, and Replays saved with it still load and deal as they did. Restart the TM server if it has been running since before this commit. A rule bug found in play is worth checking against `docs/rules-notes.md`, which lists each call made.

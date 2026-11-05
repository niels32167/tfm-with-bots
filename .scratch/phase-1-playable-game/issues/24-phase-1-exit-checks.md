# 24 — Phase-1 exit checks

**What to build:** Prove that the engine is complete, correct and fast enough to start AI work:
- the full 100,000-Game fuzz run is clean, with 2–5 Players, Draft on and off, and all cards and Corporations;
- the speed target (ADR 0004) is met, with profiling and optimization if needed;
- every card is tested and no card data mismatch is left open;
- the rules notes are complete.

**Blocked by:** 06 — Fuzzing and speed benchmark; 10 — Draft; 11–21 — all card batches and Corporations

**Status:** ready-for-agent

- [ ] 100,000 fuzzed Games finish with no crash and no broken invariant.
- [ ] The benchmark shows at least 1,000 2-player Random Bot Games per second across 16 cores, with a Game copy taking microseconds. The numbers are recorded under Comments.
- [ ] The card coverage check from ticket 08 now fails when any Project Card or Corporation lacks a scenario test, and it passes.
- [ ] The card mismatch report has no open entries.
- [ ] The rules notes list every judgment call made.

## Comments

### 2026-11-05 — hand-off from ticket 20 (Claude)

Every Project Card is implemented now, so the `implemented_cards_first` setting and the setup screen's "Deal the implemented cards first" change nothing about which cards can be played. They were left in, as old Replays name the setting. Decide here whether to remove them (`docs/rules-notes.md`, "Dealing the implemented cards first").

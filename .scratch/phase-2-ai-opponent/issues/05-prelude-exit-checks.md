# 05 — Prelude exit checks

**What to build:** Prove Prelude is complete, correct and fast enough to train on, then switch it on by default. The checks follow phase 1's ticket 24 and 25.

The play-test is mine to do. Unlike phase 1's, it records its seeds, so that its result can be checked.

**Blocked by:** 03 — The Prelude Cards; 04 — Prelude's Corporations and Project Cards

**Status:** ready-for-agent, then ready-for-human for the play-test

- [ ] The full 100,000-Game fuzz run is clean with Prelude on and off, 2–5 Players, Draft on and off.
- [ ] The fuzzer's report shows every Prelude card played.
- [ ] The benchmark still meets ADR 0004's targets with Prelude on, and the numbers are recorded under Comments with the power state.
- [ ] The coverage check and mismatch report pass, and the rules notes list every call.
- [ ] Mean Generations in Random Bot Games with and without Prelude are recorded, as a check that Prelude shortens Games as expected.
- [ ] Prelude is on by default on the setup screen. Scripts, tests and Replays that don't name it keep their old behaviour.
- [ ] I play two full Prelude Games in the GUI without finding a rule bug, and their Replay files are kept and named under Comments.

## Comments

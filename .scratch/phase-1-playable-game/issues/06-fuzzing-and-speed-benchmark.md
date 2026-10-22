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

- [ ] After every Decision, the fuzzer checks:
  - no negative Resources;
  - Production within its limits;
  - Global Parameters within range;
  - Tiles only on legal Areas;
  - at most three Milestones claimed and three Awards funded;
  - every Decision has at least one Option.
- [ ] Per Game, the fuzzer checks that it ends within a generous Generation limit (a fuzzing guard, not a rule) and that the score breakdown adds up.
- [ ] Every failure is saved as a Replay that reproduces it when loaded.
- [ ] About 1,000 fuzzed Games run with the normal test suite, and the full 100,000-Game run is one command.
- [ ] The benchmark is one command, and its first numbers are recorded under Comments in this ticket.

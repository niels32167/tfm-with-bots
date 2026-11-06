# 24 — Phase-1 exit checks

**What to build:** Prove that the engine is complete, correct and fast enough to start AI work:
- the full 100,000-Game fuzz run is clean, with 2–5 Players, Draft on and off, and all cards and Corporations;
- the speed target (ADR 0004) is met, with profiling and optimization if needed;
- every card is tested and no card data mismatch is left open;
- the rules notes are complete.

**Blocked by:** 06 — Fuzzing and speed benchmark; 10 — Draft; 11–21 — all card batches and Corporations

**Status:** ready-for-agent

- [x] 100,000 fuzzed Games finish with no crash and no broken invariant.
- [x] The benchmark shows at least 1,000 2-player Random Bot Games per second across 16 cores, with a Game copy taking microseconds. The numbers are recorded under Comments.
- [x] The card coverage check from ticket 08 now fails when any Project Card or Corporation lacks a scenario test, and it passes.
- [x] The card mismatch report has no open entries.
- [x] The rules notes list every judgment call made.

## Comments

### 2026-11-05 — hand-off from ticket 20 (Claude)

Every Project Card is implemented now, so the `implemented_cards_first` setting and the setup screen's "Deal the implemented cards first" change nothing about which cards can be played. They were left in, as old Replays name the setting. Decide here whether to remove them (`docs/rules-notes.md`, "Dealing the implemented cards first").

### 2026-11-05 — hand-off from ticket 21 (Claude)

`uv run python -m tools.card_coverage` now lists no card, Corporations included, so the check can start failing as this ticket asks. The fuzzer plays random Corporations in every Game; `Game(corporations=False)` remains only for Replays saved before ticket 21, and for tests of buying that don't concern Corporations. The mismatch report compares starting MegaCredits too. In identical Games the Corporation code costs about 3.7 % of the Games per second (5,307 in 1 process and 53,785 on 16 at ticket 21).

### 2026-11-06 — implemented (Claude)

**Decisions made with the user:** only to commit the two GUI tweaks first (c9ec510). Every other call is Claude's recommended one, on the user's standing instruction from ticket 19, and none contradicts this ticket's notes.

**The numbers,** all on the final engine (its last edit at 17:43, the fuzz started at 17:46), on mains and charging, battery 19 % rising to 63 %, "balanced" profile:
- **Fuzz:** `uv run python -m tests.fuzzing`, seeds 4235514413934542 to 4235514414034541, on 16 processes. 100,000 Games and 65,840,876 Decisions in 2,353 s, **0 failures**, nothing in `fuzz-failures/`. 2–5 Players and the Draft on and off in equal shares, with all cards and random Corporations. The longest Game lasted 34 Generations (the limit is 100). **All 220 cards were played**, the run's new report says; none was never played. The time includes the code review, `pytest` on `tests/tools` and a browser check running alongside.
- **Benchmark:** `uv run python -m tools.benchmark`. **5,373 Games per second in 1 process and 47,826 on 16** (target 1,000: met, with no profiling or optimization needed). A copy takes **0.22 µs** at the start, **0.58 µs** halfway and **0.89 µs** at the end (target under 10 µs: met). A Python loop gets through 280,804 Decisions per second. The baseline, on battery with the "performance" profile, was 5,440 and 55,543, and 0.19–0.87 µs; the 16-process rate is 14 % lower, likely the profile, as these engine changes touch only setup, though that was not measured apart.
- **Coverage:** `uv run python -m tools.card_coverage` says "All 220 cards have a scenario test." and exits 0. With `test_mine.py` and `test_credicor.py` moved away it listed both, exited 1, and `test_every_card_has_a_scenario_test` failed.
- **Mismatch report:** 0 differences, 0 names that differ, 0 missing.
- **Tests:** 1,723 passed. `cargo clippy` and `cargo fmt --check` are clean, and `npm --prefix gui run build` builds.

**Calls:**
- **`implemented_cards_first` is gone from new Games, but stays in the Replay format.** `tm_engine.Game`, the server's `new_game`, the setup screen and the fuzzer no longer have it, and new Replays leave it out. It couldn't go altogether: the setup screen had it on by default, so most Replays saved from the GUI name it, the format refuses unknown settings, and without the extra shuffle they would deal other cards (ADR 0010). A test pins what seed 7 deals, recorded before the change. The filter on effects went, as every Project Card has effects, so the shuffle is the same and draws the same random numbers. See "Dealing the implemented cards first" in the rules notes.
- **A card has a scenario test** if `tests/cards/test_<id>.py` holds a test function that names the card by its id, asserts something and isn't marked skip, skipif or xfail. A file's mere existence, the old check, would have passed an empty file. All 220 pass the stricter check as they stood.
- **`Game(corporations=False)` doesn't undermine the check:** no file in `tests/cards/` or `tests/helpers.py` uses it, and all 12 Corporation files go through real setup (`start_as`). It remains in tests of buying and of old Replays.
- **Search for Life's Victory Points**, the report's one "Not compared" entry, were checked by hand: the open-source game's `getVictoryPoints` gives 3 with any resource on the card and 0 without, as our card file does. The note says so.
- **The ~1,000-Game test allows up to 5 cards unplayed,** as Random Bots seldom reach some Requirements: only Anti-Gravity Technology (7 science Tags) went unplayed at seed 0. The full run has to say which, and it played all of them.

**Rules notes audit:** I went through the calls in every ticket's Comments (bullet by bullet for 01–22; ticket 23 has only GUI calls) and searched the notes for each, and for each card named in a call. Nearly all were there. Added: there is always an Area for an Ocean (ticket 11), Convoy From Europa at 9 Oceans (ticket 14), Toll Station counting a Corporation's Tags (ticket 21) and the two corrected card names (ticket 07; not a rules question, but decided with the user). Fixed: one test name gone stale, and "The other Corporations' abilities", which had no Why. New `tests/tools/test_rules_notes.py` checks that every note has its Call, Why and Tests and that every test it names exists. It can't check that the list is complete; that rests on this audit.

**Added beyond the ticket, in support of it:** the fuzzer reports the cards played and never played; `tests/tools/test_card_mismatches.py` fails if the saved report has open entries or, where `.cache/` holds the definitions, is out of date; the report's text now mentions starting MegaCredits.

**Checked in the browser** (1440×900): the setup screen has no such option, a new Game starts, and a Replay naming the setting loads through a second WebSocket and saves again with the setting kept.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Text the change made false: the README's "shows the count as a warning", the setup screen's doc comment, and the note saying the engine no longer has the setting.
  - A second `cards_in_play`, and never-played worked out twice (now `FuzzRun.cards_never_played`).
  - A needless default on `FuzzedGame.cards_played`, two test names, and test files parsed at import in `test_rules_notes.py`.
  - The coverage check passed a test that asserted nothing, or was skipped; "Names that differ" wasn't in the report's check; the Call after the Why in the Corporations' note; and the two implicit calls above.
- Left as is:
  - **The name `implemented_cards_first`, which now means one more shuffle, and `on_top`:** the Replay format fixes the first, and a serde rename would only hide it. Both sit in the few lines that keep old Replays working.
  - **`implemented_cards_first: false` written in `lib.rs` and `replay.rs`:** two lines, and a default would hide that a new Game never has it.
  - **`test_rules_notes.py` under `tests/tools/`, though it tests no tool:** it sits with the other checks on the repo's own files.
  - **`test_card_mismatches.py` importing `CACHE`, `COMMIT`, `REPORT` and `load_open_source_cards`:** needed to check the saved report.
  - **The coverage check doesn't look for a `scenario(` or `start_as(` call:** `load_game` and helpers count as well, and nothing exploits it: a scan of all 220 files found both an assert and such a call in each.

**Open points:**
- **Hand-off:** ticket 25 (what changed for the play-test).
- **Still open from earlier tickets:** the paw's emoji font (ticket 23).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.

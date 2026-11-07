# 05 — Prelude exit checks

**What to build:** Prove Prelude is complete, correct and fast enough to train on, then switch it on by default. The checks follow phase 1's ticket 24 and 25.

The play-test is mine to do. Unlike phase 1's, it records its seeds, so that its result can be checked.

**Blocked by:** 03 — The Prelude Cards; 04 — Prelude's Corporations and Project Cards

**Status:** ready-for-human (every check is done; `docs/agents/triage-labels.md` has no "done" label)

- [x] The full 100,000-Game fuzz run is clean with Prelude on and off, 2–5 Players, Draft on and off.
- [x] The fuzzer's report shows every Prelude card played.
- [x] The benchmark still meets ADR 0004's targets with Prelude on, and the numbers are recorded under Comments with the power state.
- [x] The coverage check and mismatch report pass, and the rules notes list every call.
- [x] Mean Generations in Random Bot Games with and without Prelude are recorded, as a check that Prelude shortens Games as expected.
- [x] Prelude is on by default on the setup screen. Scripts, tests and Replays that don't name it keep their old behaviour.
- [x] I play two full Prelude Games in the GUI without finding a rule bug, and their Replay files are kept and named under Comments.

## Comments

### 2026-11-06 — from ticket 01 (Claude)

End the coverage check's exception: remove `test_only_the_prelude_boxs_cards_may_lack_effect_data`'s allowance and make `test_every_project_card_of_the_base_box_is_implemented` cover every card. The numbers to beat, from the commit before Prelude, are in ticket 01's Comments.

### 2026-11-07 — from ticket 04 (Claude)

Every card of the Prelude box works: the coverage check reports 267 implemented and 0 left, and the mismatch report 0
differences. Ticket 01's request is done: `test_every_card_is_implemented` covers the whole catalog, and the coverage
check has no exception left for the Prelude box. A Game with Prelude now deals its Corporations from all 17, and Valley
Trust draws from the Prelude deck at random, so a Replay of a Game with Prelude saved before ticket 04 may not load;
the setup hint still says so, and switching Prelude on by default should drop that sentence. The baseline script used
since ticket 02 leaves out the view keys that are always empty without Prelude; ticket 04 added `prelude_deck_size`.
See ticket 04's Comments for the speed measured against ticket 03.

### 2026-11-07 — implemented (Claude)

Every check but the play-test is done, and Prelude is on by default on the setup screen. The play-test box is the
user's, and stays unticked.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **The default changes only on the setup screen.** `tm_engine.Game`, the server's `new_game` and Scenarios keep
  Prelude off unless it is named, so no script, test, Replay or Scenario that leaves it out changes.
- **The fuzz run:** the default command, from a random first seed, on 16 processes.
- **Mean Generations** are measured by the benchmark, on 2-Player Games with the Draft, the AI's own setting.
- **Seams:** `tools.benchmark`, the fuzz checks and the mismatch tool; the server's existing test pins that leaving
  `prelude` out of `new_game` means off. The GUI has no test runner, so its default was checked in the browser.

**The numbers,** on the laptop on mains (battery 80 %), "performance" profile:
- **Fuzz:** `uv run python -m tests.fuzzing`, seeds 807096050756828 to 807096050856827, on 16 processes, 18:03 to
  18:44. 100,000 Games and 61,437,864 Decisions in 2,477 s, **0 failures**, nothing in `fuzz-failures/`. 2–5 Players,
  the Draft on and off and Prelude on and off, in equal shares (`settings_for` cycles every 16 seeds). The longest
  Game lasted 34 Generations (the limit is 100). The full test suite ran once alongside it.
- **Every card played:** the report says "267 cards were played; never played: none.": the 220 of the base box and
  all 47 of the Prelude box (35 Prelude Cards, 5 Corporations, 7 Project Cards).
- **Benchmark:** `uv run python -m tools.benchmark --seconds 6`, without and with `--prelude`, 2 alternating rounds
  with nothing else running:

  | 2-Player Games with the Draft | without Prelude | with Prelude |
  |---|---|---|
  | Games per second, 1 process | 5,518 / 5,494 | 5,897 / 5,828 |
  | Games per second, 16 processes (target 1,000) | 55,403 / 55,404 | 58,506 / 54,751 |
  | Copy at the start / halfway / at the end (target under 10 µs) | 0.20–0.21 / 0.60–0.62 / 0.92–0.97 µs | 0.19–0.20 / 0.44–0.46 / 0.68–0.69 µs |
  | Python loop, Decisions per second | 277,079 / 277,858 | 269,625 / 270,302 |

  Every target is met, both ways. Without Prelude these match ticket 04's (5,543 and 55,277; 0.22 / 0.61 / 0.93 µs),
  as the engine hasn't changed since. Ticket 01's numbers were taken on battery in "power-saver", so they don't
  compare.
- **Mean Generations of Random Bot Games** (2 Players, Draft, seeds 0 to 1,999 each): **20.99 without Prelude and
  17.87 with it**, 15 % fewer. ADR 0011's human Games go from 12.4 to 10.7 (14 % fewer), so Prelude shortens Games as
  expected. Random Bots take longer, as they terraform at random.
- **Picks:** Games with Prelude average 532 picks against 596 (−11 %, 2,000 Games each), but a pick costs about 4 %
  more (3.05 million picks per second in one process against 3.19 million), so Games per second rise only about 7 %.
  Not looked into, as the target is met 55 times over.
- **Coverage:** "All 267 implemented cards have a scenario test." **Mismatch report:** 0 differences, 0 names that
  differ, 0 missing, now with Prelude Cards' MegaCredits compared (below).
- **Tests:** 1,966 pass. Clippy and `cargo fmt --check` are clean, the GUI builds, and `ruff check` finds nothing new
  in the touched files (its old hits in `server/app.py`, `tools/benchmark.py` and the fuzz files predate this).
- **Games without Prelude unchanged:** the 120 Random Bot Games saved before ticket 02 (2–5 Players, Draft and
  Corporations on and off; 80,927 picks) still replay to the same view, Decision and game log, and the same seeds play
  the same Games.

**Found by the fuzz run — a check too narrow, not an engine bug.** The first run flagged 7 of its first 10,000 Games:
Valley Trust's first action drew Ecology Experts, the Player picked a card from the hand, and at the payment Decision
that followed, the check said the next card "still waits on the Prelude Card 'ecology_experts'". The engine is right:
it clears the effect once the card is paid for and played, and the payment must still follow it. The check allowed
for the `play_card` Decision only. It now also allows a payment Decision of Valley Trust's Player for a card in their
hand, and nothing else (not a card's action, not an expense), each with a test. All 7 seeds play to the end clean.
That run and a second one, started before the check was narrowed to cards in the hand, were stopped; the run above
is the only one on the final checks.

**Calls:**
- **The rules notes list every call.** Ticket 05's one rules-level call, where the default changes, is in "The Prelude
  setting", which now names the server's test too. The fuzz check's fix follows the engine's existing Valley Trust
  note and makes no call. The calls in tickets 01–04's Comments were each found in the notes (Robinson Industries,
  Vitor, Valley Trust, Point Luna, Psychrophiles, Lava Tube Settlement, the "Pay X" cards, Ecology Experts and
  Excentric Sponsor, Research Network's wild Tag, the 15 MegaCredits for an unplayable Prelude Card, the names), and
  `tests/tools/test_rules_notes.py` passes.
- **Prelude Cards' MegaCredits are compared,** ticket 01's last request: the open-source game's `startingMegacredits`,
  or else the MegaCredits in `behavior.stock` (as its PreludeCard reads them), against our effect data's MegaCredits
  less its `pay`. All 35 agree, so the "Pay X" cards' prices (Business Empire 6, Galilean Mining 5, Huge Asteroid 5,
  Aquifer Turbines 3) and the gains (Donation 21, Loan 30, Allied Banks 3, Martian Industries 6, Nitrogen Shipment 5)
  match. Before our side counted `pay`, the check found exactly the 4 "Pay X" cards.
- **The setup hint** no longer says that Replays of Prelude Games saved before all of Prelude worked may not load,
  as ticket 04 asked.
- **The benchmark** reports mean Generations both ways on every run, whatever `--prelude` says, over 2,000 Games each
  (about a second); `measure()` takes a smaller count for the tests.

**Checked in the browser** (1440×900, no console errors): the setup screen shows Prelude ticked and the shorter hint.
A Game started with the defaults saves `"prelude": true` in its Replay; with the box unticked, the Replay leaves the
setting out, as before.

**Code review** (`/code-review`, standards and spec):
- **Fixed:**
  - the fuzz check's exemption was any payment Decision of Valley Trust's Player; it is now one for a card in their
    hand, with a test that a payment for another card or for an expense is still flagged;
  - `new_game` in the benchmark had no doc comment;
  - "whichever is benchmarked" in the benchmark's doc, which read as if only one setting were measured;
  - the three mean-Generations fields of `Results` are now one `MeanGenerations`;
  - the local named `settings` that held a phrase, and the README's wording of the default;
  - the rules note's Tests didn't name the server's test of the default.
- **Kept, with reasons:**
  - `prelude` passed through each benchmark function, as `seconds` already is: a settings type for one flag would
    be more than it saves.
  - `measure()` and `Results` hold both the speed targets and the mean Generations: the ticket asks for both from
    the same Random Bot Games, and the Generations cost about a second.
  - The default is explained in the README, the rules notes, the engine's doc comment, the server's doc and the
    setup screen: each is read on its own, and each says it in a line.
  - `test_prelude_shortens_random_bot_games_as_the_benchmark_reports` compares 200 Games each. The seeds are fixed,
    so it can't flake; it is ADR 0011's claim, kept as a test.

**Open points:**
- **The play-test is the user's:** two full Prelude Games in the GUI, without finding a rule bug, with both Replay
  files kept (Save Replay) and named here. Restart the TM server first if it has run since before this commit. A rule
  bug found in play is worth checking against `docs/rules-notes.md`; Dev panel and Save Replay give its Replay.
- **Still open from earlier tickets:** the paw's emoji font (phase 1, ticket 23); the state editor can't put Prelude
  Cards in a Scenario (ticket 02).

### 2026-11-07 — play-test (Claude, on the user's report)

**The user played one full Prelude Game in the GUI, found no rule bug, and judged one Game enough** instead of the
two this box names. The box is ticked on that decision, which is the user's to make, as the play-test is theirs.

**The Game,** kept as `.scratch/phase-2-ai-opponent/play-test/terraforming-mars-seed-263853680-pick-345.json` (saved
with Save Replay at 19:23, on 5859556):
- 2 Players, the user against a Random Bot, with the Draft and Prelude; seed 263853680, 345 picks.
- The user played United Nations Mars Initiative with Huge Asteroid and Metals Company; the Random Bot played Cheung
  Shing Mars with Biolabs and Metal-Rich Asteroid.
- Over in Generation 12: the user won, 80 Victory Points to 38.

**What Claude checked:** the file loads with `tm_engine.Game.from_replay` and replays to the end of the Game, with
the final scoring above. Whether every rule felt right rests on the user's report.

**Bugs found: none,** so there are no new tickets, Replays or regression tests. Nothing in the engine, the server or
the GUI changed for this, so the numbers above stand.

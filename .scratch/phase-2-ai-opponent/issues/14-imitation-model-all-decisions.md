# 14 — Imitation Model for all Decisions

**What to build:** Extend the Imitation Model to every Decision, using the Action-phase data from ticket 10. Payment, Area and target Decisions are all Options like any other (ADR 0002).

Consider how much to learn at each kind of Decision. Payment has up to 166 Options, though few choices matter. A model may be poor at rare Decision kinds, so check that it still does something sensible there.

Humans also make Decisions in ways the engine's chain may split differently, so ticket 10 decides how those map onto Options.

**From ticket 09: the accuracy needed for hands.**
- **Which Games.** Learn Action-phase Decisions from the "named" Games: 37,884 with Prelude and 4,547 without, 22,081 of them not conceded. Read the hands with `resync=True`.
- **What a hand at a Decision must have:**
  - its size right at every fresh Hand Counter check of the Game ("counted");
  - every card the Player later plays from it present by name (99.43% are).
- **Sold cards.** Cards that left without a name (Sell Patents, Mars University) are resolved in hindsight from named cards never played later, as ticket 10 does. The only error left is which never-played cards a Player still held: cards that drove no later play.
- **Not required.** Exact hands throughout would leave 170 Games not conceded.
- **Old-version Games** name only one Player's cards. They are left out at first.

**Blocked by:** 10 — Recorded Games in the engine; 12 — Position encoding; 13 — Imitation Model for Draft and buy

**Status:** ready-for-agent

- [x] On held-out Games, it predicts picks better than a random pick and the Card Economy Bot, reported by Decision kind, Generation and rating.
- [x] A Controller using only this model plays complete Games with none stalled.
- [x] It beats the Controller from ticket 13 in a Match with the interval above 50%.
- [x] Its Games against itself are recorded beside the human benchmark: Generations, Victory Points and card Victory Points, and which Milestones it claims and Awards it funds, in which Generation, and how often it loses an Award it funded (the flip rate: tfmstats.com's if it answers, or else the dataset's, from the replayed Games' final scoring; see "When tfmstats.com doesn't answer" in the spec). This is the first check that it plays like the Players it learned from.
- [x] It is selectable in the GUI, and a pick takes well under a second.

## Comments

### 2026-11-19 — implemented (Claude)

All five boxes are ticked; the evidence follows. The work:
- `ai/imitation/positions.py`: each replay also gives its Action-phase Decisions (the Prelude Cards played and
  every Decision of the Action phases), up to the replay's first difference. Picks the Recorded Game's log didn't
  give (`inferred`) are left out. Batches sort by Option band (up to 8, 16, 32, 64…) and then by card rows.
- `ai/imitation/train.py`: `--start-from` begins a run from a saved model's weights.
- `ai/imitation/bot.py`: the Imitation Bot answers every Decision. `imitated=DRAFT_AND_BUY` plays like ticket 13's.
- `ai/controllers.py`: `imitation_draft_buy`, "Imitation Bot (Draft and buy)", plays ticket 13's model from
  `.cache/models/imitation-draft-buy.pt`.
- `ai/imitation/evaluate.py` and `ai/recorded_games/replay.py`: at Action-phase Decisions the Card Economy Bot is
  asked with a handle on the replay's Game (`also_asked`), as in play. Most-kept is blank at kinds without keep rates.
- `ai/match.py`: `game_summary(replay)` plays a Replay through the engine and notes each Milestone claimed and Award
  funded, with its Generation, and whether the funder lost the Award. `ai/imitation/checks.py self-play` sets a
  bot's Games against itself beside Players' Games.
- `ai/encoding.py`: a Payment for a Prelude Card's price (Helion paying Aquifer Turbines with heat), which the engine
  names by the card, failed to encode. It now encodes as paying for that card. The layout is unchanged, so ticket
  13's model still loads.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **Every kind is learned with equal weight per Decision, and inferred picks are left out.** Batches are bucketed by
  Option count as well as card rows. Measured first on 4 shards (247,109 Action-phase Decisions):
  - `action` 64%, `area` 12%, `payment` 10%, `sell_patents` 4%, then 13 kinds under 3% each.
  - Payment averages 5.3 Options (99th percentile 34, most 240). Decisions with 40+ Options hold 4.7% of all Option
    rows.
  - Inferred picks are 66% of Sell Patents and almost all of discard-to-draw, production and Viral Enhancers. They
    are the replay's hindsight choices, not the Player's.
- **One model, warm-started from ticket 13's weights** (the same encoding), trained on setup, Draft, buy and
  Action-phase Decisions mixed.
- **Ticket 13's bot is registered apart** (above), so that box 3 can play it.
- **About an hour of time**, so one training run of about 30 minutes and no pilot.

**Chosen by Claude, on the user's instruction to take the recommendation after the first batch:**
- **Option bands of 8, 16, 32, 64…, then card rows,** as the sort key. On 40,000 real positions, batches pad 1.41
  tokens for each real one (card rows sorted alone: 1.53), and 1.86 Option rows for each real one (alone: 4.89).
- **Settings as ticket 13's best:** Players rated 450+, Games with Prelude only, 6M positions, `--compile`, 10
  workers.
- **Which Games:** Action-phase Decisions come from every replay (44,714 Games with both Players' setup records,
  ticket 10), each up to its first difference. The ticket asks for ticket 09's 42,431 "named" Games, with each
  hand's size right at every fresh Hand Counter check. Ticket 10 found the replay's own checks stronger: it stops at
  a card not in hand, a deck out of step or a tracker that differs. So no separate Hand Counter filter is applied.
  Old-version Games have no replay and stay out.
- **The Card Economy Bot's baseline at Action-phase Decisions** is its real pick: the replay gives it a handle on
  the replay's Game, Sampled Positions included. It is computed only for evaluation.
- **The human benchmark** is Players' Games with Prelude, not conceded, replayed fully, with both Players rated
  450+, from every split: 4,111 Games. The spec allows every Game for rates that describe how Players play.
- **The flip rate:** a funder lost the Award if the other Player's count was higher at the end. A tie for first is
  no loss. It comes from the engine's final view of each replayed Game.

**Training** (a user systemd service capped at 6 GB, 5.1 GB peak, 29 minutes):
```bash
uv run python -m ai.imitation.train --positions 6000000 --validate-every 1000000 --min-rating 450 \
  --prelude-games-only --compile --workers 10 --start-from .cache/models/imitation-draft-buy.pt \
  --out .cache/models/runs/all-decisions.pt
```
- About 3,500 positions a second (ticket 13's: 6,500). Positions now carry about 82 card rows.
- Validation accuracy over every kind: 62.2% at 1M, 63.5% at 2M, 64.1% at 3M, 65.1% at 4M, 65.9% at 5M and 66.1% at
  6M. It was still rising, and 6M is less than one pass over the training Decisions.
- Registered as `.cache/models/imitation.pt`. Ticket 13's model is `.cache/models/imitation-draft-buy.pt`.

**Box 1: held-out accuracy.** `uv run python -m ai.imitation.evaluate --shard-share 8`: 242,015 test positions,
every rating, with Prelude and without. The full table is in `.cache/models/runs/evaluate-14-test.txt`.

| | Positions | Model | Random | Card Economy Bot | Most-kept |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 242,015 | **63.4%** | 21.4% | 37.3% | 53.8% (setup, Draft, buy) |
| action | 103,154 | **52.9%** | 11.0% | 24.8% | - |
| buy_cards | 49,071 | **71.5%** | 26.5% | 33.8% | 46.6% |
| draft | 36,819 | **71.7%** | 36.1% | 44.2% | 63.1% |
| area | 18,091 | 39.5% | 11.6% | 39.8% | - |
| payment | 17,010 | **92.9%** | 28.3% | 76.0% | - |
| keep_cards | 4,288 | **76.4%** | 45.9% | 52.3% | - |
| prelude_cards | 2,568 | **70.0%** | 29.2% | 44.2% | 52.6% |
| target | 2,230 | **93.1%** | 45.7% | 88.5% | - |
| sell_patents | 1,941 | 100.0% | 16.0% | 100.0% | - |
| play_prelude_card | 1,390 | 66.2% | 48.7% | 67.0% | - |
| corporation | 1,306 | **70.2%** | 50.0% | 54.0% | 66.2% |
| effects, resources, olympus_conference, final_greenery, add_to_card | 3,871 | 73–98% | 44–50% | 61–98% | - |
| free_award, viral_enhancers, play_card, discard_to_draw (rare) | 286 | 36–100% | 13–50% | 5–58% | - |
| Generation 1 / 5 / 10+ | | 72.2% / 65.8% / 56.7% | 21.4% / 22.9% / 18.7% | 37.1% / 38.6% / 34.6% | |
| Rated under 300 / 500–599 / 600+ | | 58.7% / 65.0% / 65.5% | 22.8% / 20.8% / 20.9% | 39.2% / 36.5% / 36.6% | |

- It beats both baselines overall, in every Generation and in every rating band.
- It beats them at every kind but two, where it ties the Card Economy Bot within one standard error:
  - Area: 39.5% against 39.8% (18,091 positions, standard error 0.4 points).
  - Playing a Prelude Card: 66.2% against 67.0% (1,390 positions, standard error 1.3 points).
  - Ticket 13's box 2 was ticked with such a tie, at the Corporation.
- Setup, Draft and buy hold up: 71.5% buying and 71.7% drafting, against ticket 13's 71.6% and 72.0%.
- Accuracy falls from 72% in Generation 1 to 57% in Generation 10+, as the Action phase's share and its Options grow.
- **Rare kinds:** free_award (90 positions) 35.6% against the bot's 32.2% and random's 20.0%. Viral Enhancers, play_card
  and discard_to_draw (58–78 each) are at 88–100%.
- Sell Patents and discard-to-draw score 100% for both, likely because the inferred picks were left out and what
  remains is mostly the one obvious pick (not measured).

**Box 2: complete Games with none stalled.** Every Game finished:
- 400 Games against ticket 13's bot (box 3);
- 200 against itself (box 4);
- 3 seeded Games in the timing check (box 5), which end in Generations 10–12;
- a Game in the GUI.

The Controller answers every Decision with the model (`test_every_pick_with_a_choice_is_the_option_the_model_rates_highest`).

**Box 3: Match.** `uv run python -m ai.match imitation imitation_draft_buy --games 400 --processes 10`.
- The Imitation Bot won **57.0% (52.1–61.8%)**: 228 to 172, with 0 stalled and 0 failed.
- Victory Points 99.7 against 96.6, card Victory Points 24.2 against 20.8, Terraform Rating 47.2 against 41.0.
- Games last **11.5 Generations**, against 13.3 in ticket 13's Match against the Card Economy Bot and humans' 10.7.
- It took 2.3 minutes at 3.4 GB peak. 400 Games were enough for the interval to clear 50%.

**Box 4: self-play beside Players.** `uv run python -m ai.imitation.checks self-play --games 200 --processes 10`.
tfmstats.com didn't answer on 2026-11-19 at 20:47, neither to `curl` (timed out after 20 s) nor in the browser pane.
The flip rate is therefore the dataset's, from the engine's final view of the replayed Games, as the spec's "When
tfmstats.com doesn't answer" says.

| | Imitation Bot against itself | Players rated 450+ |
| --- | ---: | ---: |
| Games | 200 | 4,111 |
| Generations | 11.0 | 10.5 |
| Victory Points (a Player) | 90.3 | 98.5 |
| card Victory Points (a Player) | 19.2 | 21.4 |
| **Flip rate (Awards funded, then lost)** | **35.3%** | **7.8%** |

| Milestone | claimed per Game, mean Generation (bot) | (Players) |
| --- | --- | --- |
| Builder | 0.80, 6.8 | 0.77, 6.5 |
| Gardener | 0.85, 7.1 | 0.77, 6.4 |
| Mayor | 0.16, 7.3 | 0.32, 6.9 |
| Planner | 0.64, 5.5 | 0.57, 5.6 |
| Terraformer | 0.54, 7.5 | 0.57, 7.0 |

| Award | funded per Game, mean Generation, share lost (bot) | (Players) |
| --- | --- | --- |
| Banker | 0.17, 11.2, 53% | 0.41, 8.7, 6% |
| Landlord | 0.70, 8.2, 33% | 0.65, 7.5, 11% |
| Miner | 0.43, 9.4, 28% | 0.52, 7.7, 7% |
| Scientist | 0.00 | 0.62, 7.9, 6% |
| Thermalist | 0.06, 12.0, 67% | 0.53, 8.5, 9% |

- **It plays like the Players in Game length and Milestones.**
  - Its Games last 11.0 Generations, against 10.5.
  - It claims each Milestone about as often and within a Generation of when Players do. Mayor is the exception,
    claimed half as often.
  - It scores 19.2 card Victory Points, against 21.4.
- **Awards are what it hasn't learned.**
  - It funds 1.4 Awards a Game against Players' 2.7, a Generation or two later, and never Scientist.
  - It loses 35% of those it funds, against 7.8%. Likely causes, not measured: Players fund an Award they are sure
    to win, while the model picks one step at a time and doesn't foresee the other Player overtaking it.
  - Fund-award Options are a small share of `action` picks, so few training positions teach them. Likely next steps:
    the Value Model (ticket 15) and search (ticket 16).
- The saved table is in `.cache/models/runs/self-play-14.txt`.

**Box 5: GUI and speed.**
- The setup screen offers "Imitation Bot" and "Imitation Bot (Draft and buy)" for each Player.
- A Game with both Players set to the Imitation Bot played into Generation 4's Action phase in the browser pane, with
  no console or server errors.
- Pick times in 3 seeded Games against itself (scratch script, CPU, one thread): 1,428 picks, **mean 3.1 ms, at most
  7.8 ms**.
  - The widest Decisions were an Area with 48 Options (at most 5.8 ms), Payments with 30 (5.6 ms) and Actions with
    30 (7.8 ms).
  - Faster than ticket 13's bot (mean 6.9 ms), which asked the Card Economy Bot to try Options on Sampled Positions.
- `test_a_pick_takes_well_under_a_second` now times the Decision with the most Options in its Game, under 0.25 s.

**Code review** (`/code-review` against 0e0d97a: one standards and one spec subagent, read-only during training).

Fixed:
- **Spec review:** `checks.py` imported the engine, so `test_no_controller_imports_the_engine` failed. `Claim`,
  `GameSummary` and `game_summary` moved to `ai/match.py`, which may import it, with their test in
  `tests/ai/test_match.py`.
- **Spec review:** the speed test timed only a Draft pick. It now times the Decision with the most Options.
- **Spec review:** `players_games`, the human benchmark's filter, had no test. It now has one.
- **Standards review:**
  - "the log" alone, an _Avoid_ word, is now "the Recorded Game's log".
  - `Benchmark`'s unnamed tuples are now `MilestoneRate` and `AwardRate`.
  - "Gen" is spelled out.
  - CONTEXT.md now defines the Imitation Bot for every Decision, and names ticket 13's.
- Found while running the full suite: the bot tests' untrained model started from unseeded random weights, so each
  run played a different Game. The fixture now seeds them.

Left as they are:
- **`DRAFT_AND_BUY` repeats replay.py's `RECORDED_KINDS`, and `cards_by_name()` repeats `names.card_id`.** The bot and
  the encoding must not import Recorded Game code (fair play, `test_the_bot_loads_no_dataset_reader_or_replay_code`).
- **`also_asked` takes any Controller**, though only the Card Economy Bot uses it. The replay shouldn't name a
  Controller.
- **`checks.py` now also runs a Match** (self-play), beside the model checks. It is the ticket's check command, as
  ticket 13's boxes 5 and 6 were.
- **`players_games` repeats the Prelude, not-conceded and rating filter** of `price_check.py` and `replay_dataset.py`.
- **`Claim.lost` is None for Milestones.**

**Open points:**
- **Awards:** the flip rate is 35% against Players' 7.8% (box 4). A target for the Value Model and search.
- **Area placement** ties the Card Economy Bot (box 1). The board token is a single flattened row, which may limit
  what the model sees of Areas.
- **A longer run:** accuracy was still rising at 6M (66.1%), short of one pass over the data. A run of 20M or more
  (about 1.6 hours) is the cheap next step.
- **A Match against the Flat Playout Bot**, which the README's training-progress table asks of each rung. Not run, for
  time, as in ticket 13.

### 2026-11-20 — the longer run, now the registered model (Claude)

The user OK'd the longer run from the open points above. Every box still holds, with better numbers. The 6M model is
kept in `.cache/models/runs/all-decisions.pt`, and `.cache/models/imitation.pt` is now the 20M model.

**The run.** It used the same settings as the 6M run, warm-started from it:
`train --positions 20000000 --validate-every 2000000 --min-rating 450 --prelude-games-only --compile --workers 10
--start-from .cache/models/runs/all-decisions.pt --out .cache/models/runs/all-decisions-20m.pt`, under the 6 GB cap.
- It took 1 hour 20 minutes at about 4,200 positions a second, about 3.1 passes over the 6,423,216 training positions.
- systemd counted a **5.7 GB memory peak**, page cache included (cgroup anon was 4.4 GB at 2M). That is close to the
  cap. A longer or wider run needs fewer workers or a higher cap.
- **Validation accuracy:**
  - The restarted learning rate first dipped it to 64.7% at 2M.
  - It then rose to 65.5% at 4M, 66.5% at 8M, 67.1% at 12M, 67.9% at 16M and **68.4% at 20M**, against the 6M
    model's 66.1%.
  - Validation loss fell from 0.963 to 0.847. Train loss (0.842) stayed level with it, so there is no sign of
    overfitting yet.
- The model was chosen on validation. The test split was evaluated once, afterwards.

**Box 1: held-out accuracy** (the same command and test positions; `.cache/models/runs/evaluate-14-20m-test.txt`):

| Kind | Positions | 6M model | 20M model | Card Economy Bot | Random |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 242,015 | 63.4% | **65.4%** | 37.3% | 21.4% |
| action | 103,154 | 52.9% | **55.2%** | 24.8% | 11.0% |
| area | 18,091 | 39.5% | **48.4%** | 39.8% | 11.6% |
| payment | 17,010 | 92.9% | **94.4%** | 76.0% | 28.3% |
| buy_cards | 49,071 | 71.5% | **72.1%** | 33.8% | 26.5% |
| draft | 36,819 | 71.7% | **72.1%** | 44.2% | 36.1% |
| free_award | 90 | 35.6% | **45.6%** | 32.2% | 20.0% |
| play_prelude_card | 1,390 | 66.2% | **68.1%** | 67.0% | 48.7% |
| resources | 1,166 | **73.3%** | 72.4% | 60.6% | 45.6% |

- Every kind rose except `resources` (1,166 positions, down 0.9 points).
- Every Generation rose by 1 to 2.7 points, the late ones most (10+: 56.7% → 59.0%).
- Every rating band rose (600+: 65.5% → 68.0%).
- **The Area tie is gone:** 48.4% against the Card Economy Bot's 39.8%. The single flattened board row was not what
  held it back; more training was.
- `play_prelude_card` (68.1% against 67.0%) is now the closest call to the Card Economy Bot.

**Box 3: Match.** `uv run python -m ai.match imitation imitation_draft_buy --games 400 --processes 10`
(`.cache/models/runs/match-14-20m.txt`):
- It won **82.2% (78.2–85.7%)**, 329 to 71, with 0 stalled and 0 failed. The 6M model won 57.0%.
- Mean Victory Points 104.1 – 87.8, card Victory Points 24.5 – 18.0, Terraform Rating 48.8 – 39.1.
- Mean Generations 10.99.
- Player 1 won 49.8% of Games.

**Box 4: self-play beside Players** (`uv run python -m ai.imitation.checks self-play --games 200 --processes 10`;
`.cache/models/runs/self-play-14-20m.txt`). 200 Games finished, 0 stalled.

| | 20M model | 6M model | Players rated 450+ |
| --- | ---: | ---: | ---: |
| Generations | 10.4 | 11.0 | 10.5 |
| Victory Points (a Player) | 91.4 | 90.3 | 98.5 |
| card Victory Points (a Player) | 19.6 | 19.2 | 21.4 |
| Awards funded, lost (flip rate) | **10.4%** | 35.3% | 7.8% |

| Award | funded per Game, mean Generation, share lost (20M) | (Players) |
| --- | --- | --- |
| Banker | 0.18, 10.8, 28% | 0.41, 8.7, 6% |
| Landlord | 0.60, 7.7, 15% | 0.65, 7.5, 11% |
| Miner | 0.17, 7.9, 0% | 0.52, 7.7, 7% |
| Scientist | 0.61, 8.9, 5% | 0.62, 7.9, 6% |
| Thermalist | 0.27, 9.2, 7% | 0.53, 8.5, 9% |

- **The flip rate fell from 35% to 10%,** near Players' 7.8%. Scientist, never funded by the 6M model, is now funded
  as often as Players fund it, and Thermalist far more often than before.
- **What is left:**
  - It funds 1.83 Awards a Game against Players' 2.74, about a Generation later.
  - Banker is still lost 28% of the time.
  - Mayor is still claimed half as often (0.17 against 0.32). The other Milestones are within 0.1 a Game and half a
    Generation.

**Box 5: GUI and speed.**
- The model has the same size and architecture, so the 3.1 ms mean pick time measured on 2026-11-19 stands. It was not
  re-measured: the scratch script was gone.
- `test_a_pick_takes_well_under_a_second` times the bot's code path, not this model's weights.
- The GUI loads the registered file the same way. It was not re-checked in the browser pane for this run.

**Docs:** the README's Match row, bot paragraph and training-progress row, and the guide's training recipe (both runs,
the memory note).

**Open points now:**
- **Awards:** they are funded less often and later than Players fund them, and Banker is still often lost.
- **Mayor** is claimed half as often as Players claim it.
- **A Match against the Flat Playout Bot**, still not run.
- **More training:** accuracy was still rising at 20M (+0.1 points over the last 2M, at the end of the cosine
  schedule). A bigger model is more likely to help now than more passes.
- `ai.match` prints the two column headers with no space between them (`a: imitationb: imitation_draft_buy`) when a
  Controller's name is long. This is cosmetic and not from this ticket.

### 2026-11-21 — box 4 rerun on tfmstats.com's tables (Claude)

tfmstats.com answered again (checked 2026-11-20 and 2026-11-21), so box 4's comparison was rerun once on the site's own
tables, as the spec's "When tfmstats.com doesn't answer" asks. Nothing was replayed or retrained: the bot's column is
the 20M model's 200 Games against itself from 2026-11-20 (`.cache/models/runs/self-play-14-20m.txt`). Only the
reference changes.
- **How the site was read** (browser pane, from the home page's links): 2 Players, Tharsis, Prelude and Draft on, both
  Players rated 450+, Colonies unfiltered (its toggle's off state is also its unfiltered state). These are the
  filters ticket 15 used on 2026-11-20 for the Awards page, whose table is reused here.
  - The Milestones page was read on 2026-11-21 with the same filters.
  - The site gives counts, not rates per Game. The Corporations page, with the same filters, gives 50,083 Corporations
    played, so about 25,040 Games. The per-Game rates below divide by that.
  - Each page was Reset afterwards.

| | 20M model | Players rated 450+ (dataset) | tfmstats.com |
| --- | ---: | ---: | ---: |
| Games | 200 | 4,111 | about 25,040 |
| Milestones claimed per Game | 2.97 | 3.00 | 2.94 (73,534 claimed) |
| Awards funded per Game | 1.83 | 2.73 | 2.34 (58,715 funded) |
| **Flip rate** | **10.4%** | 7.8% | **9.3%** |

| Milestone | claimed per Game, mean Generation (20M model) | (Players, dataset) | tfmstats.com: claimed, per Game, mean Generation |
| --- | --- | --- | --- |
| Builder | 0.85, 6.6 | 0.77, 6.5 | 19,239, 0.77, 6.5 |
| Gardener | 0.85, 6.8 | 0.77, 6.4 | 18,370, 0.73, 6.4 |
| Mayor | 0.17, 7.5 | 0.32, 6.9 | 8,150, 0.33, 6.8 |
| Planner | 0.57, 5.2 | 0.57, 5.6 | 15,146, 0.60, 5.6 |
| Terraformer | 0.53, 7.2 | 0.57, 7.0 | 12,629, 0.50, 7.1 |

| Award | funded per Game, mean Generation, share lost (20M model) | (Players, dataset) | tfmstats.com: funded, per Game, mean Generation, flip |
| --- | --- | --- | --- |
| Banker | 0.18, 10.8, 28% | 0.41, 8.7, 6% | 8,644, 0.35, 8.7, 6.7% |
| Landlord | 0.60, 7.7, 15% | 0.65, 7.5, 11% | 14,531, 0.58, 7.5, 11.3% |
| Miner | 0.17, 7.9, 0% | 0.52, 7.7, 7% | 11,035, 0.44, 7.7, 11.4% |
| Scientist | 0.61, 8.9, 5% | 0.62, 7.9, 6% | 13,697, 0.55, 7.7, 6.1% |
| Thermalist | 0.27, 9.2, 7% | 0.53, 8.5, 9% | 10,808, 0.43, 8.5, 10.4% |

- **The site agrees with the dataset.** Every Milestone's and Award's mean Generation is within 0.2 of the dataset's,
  and Milestones per Game within 0.07 (Terraformer).
  - The site counts fewer Awards per Game (2.34 against 2.73). Likely causes, not measured: the site includes
    conceded Games, which end before late Awards are funded, and Colonies Games. The dataset's benchmark is Games
    not conceded and replayed fully.
  - The site's flip rate, 9.3%, is 1.5 points above the dataset's. Miner (11.4% against 7%) is the largest part.
- **What the site's table says of the model:** the same as the dataset's.
  - Milestones: within 0.12 a Game and 0.4 of a Generation of the site's, except Mayor, claimed half as often
    (0.17 against 0.33).
  - Flip rate: 10.4% against the site's 9.3%, a gap of 1.1 points where the dataset's was 2.6.
  - Awards: still funded less often than Players fund them (1.83 against 2.34 a Game) and later. Banker is still lost
    more often (28% against 6.7%).
- **Box 4 stays ticked.** The site's tables don't change its conclusion: Game length and Milestones look like the
  Players', Mayor and Awards are what it hasn't learned, and its flip rate is near Players'. The box asks for the
  comparison to be recorded, and it now is, both ways.

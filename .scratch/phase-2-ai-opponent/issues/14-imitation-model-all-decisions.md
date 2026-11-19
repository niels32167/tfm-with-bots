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

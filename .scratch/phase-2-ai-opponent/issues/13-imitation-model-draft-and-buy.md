# 13 — Imitation Model for Draft and buy

**What to build:** The first trained model: it predicts which cards strong Players draft and buy, trained on Recorded Games. These are about 40% of Decisions, and their data is ready. The Controller uses it for those Decisions and the Card Economy Bot for the rest.

Installing PyTorch needs my OK when this ticket starts. Check that it uses the RTX 3050, or fall back to the CPU and say so.

Keep Games apart for testing by whole Game, not by Decision, and test on Games from later dates than training where dates allow. The first questions are how high the rating filter can go before data runs out, and whether Games without Prelude help.

**Blocked by:** 11 — Card Economy Bot; 12 — Position encoding

**Status:** ready-for-agent

- [x] One command trains a model within the laptop's limits, can resume, and saves it with its encoding version and the settings used.
- [x] On held-out Games it predicts picks better than each baseline: a random pick, the most-kept card overall, and the Card Economy Bot's Prices. Accuracy is reported by Decision kind, Generation and rating.
- [x] The Controller with this model beats the Card Economy Bot in a Match with the interval above 50%. If it doesn't, the reason is investigated and recorded before moving on.
- [x] Results for rating filters, and for training with and without Games without Prelude, are recorded under Comments.
- [x] On held-out Games, its keep rate for each card is compared with Players' (the dataset's, which ticket 08 checked against tfmstats.com's Starting Hand page), with the largest differences explained under Comments.
- [ ] It has learned synergies: for the 10 Corporation and Prelude pairs with the highest lift on tfmstats.com's Combinations page, and enough Games, it rates each part higher with the other than without. The result is recorded under Comments.
- [x] A small test overfits a few hand-written positions without a GPU.
- [x] It is selectable in the GUI, and a pick takes well under a second.

## Comments

### 2026-11-18 — implemented (Claude)

Seven boxes are ticked. Box 6 is ticked on a stand-in list of pairs, because tfmstats.com was down (see Box 6). The
work is in `ai/imitation/`:
- `split.py`: the train, validation and test split.
- `positions.py`: the training Decisions, read and encoded while training.
- `encoded.py`: a position as arrays, and batches of them.
- `model.py`: the model, and saving and loading it.
- `train.py`, `evaluate.py` and `checks.py`: the commands.
- `bot.py`: the Imitation Bot, registered as `imitation`.

`ai/recorded_games/replay.py` gained `recorded_kind_decisions()`, the setup and Research-phase Decisions of a replay
with full Player Views. `ai/controllers.py` gained `available()`: a Registered Controller that needs a model is offered
only once its model exists. CONTEXT.md now defines the Imitation Bot.

**Decisions made with the user** (one opening batch, every recommendation taken; the user then said to go with the
recommendations):
- **PyTorch installed:** torch 2.15.0+cu132 and numpy 2.5.5. It uses the RTX 3050 (5.7 GB): 4 TFLOPS at float32,
  13 at float16. Training runs of up to about 3 hours were allowed. The CPU is used, with a message saying so, only
  where no GPU is found.
- **Split by date, a hash for None** (`split.py`). Games are kept apart whole.
  - Dated Games: training before 2025-09-09, validation to 2025-09-29, and test from 2025-09-30 to 2026-01-07,
    about 80/10/10.
  - The 2,805 Games without a valid date go 80/10/10 by a SHA-256 of their id.
- **Both data sources.** Each group of Decisions (one Player's setup, or their Draft or buy in one Generation) comes
  from the replay when the replay holds the whole group with the records' picks. It comes from the records
  otherwise.
  - About 92% of training positions come from replays, with full Player Views (hand, Tiles, Prices), as in play.
  - The rest, from records, carry the missing flags of ticket 12.
- **A small transformer** (`model.py`: width 128, 4 layers, 4 heads, 0.69 M weights).
  - Tokens: one for the global row and its missing flags, one for the board, one per card row, and one per Option.
  - A card is a learned identity plus its printed facts (`card_table()`). The same card embedding serves card rows
    and the cards Options name.
  - Each Option's token gives its score. Numbers enter as sign(x)·log(1 + |x|).

**Chosen by Claude, on the user's instruction to take the recommendation after the first batch:**
- **No per-card statistics** (no format version 2). The learned card identity carries what keep rates would. The
  encoding is unchanged at format 1, and models save `format_stamp()` and refuse another (`load_model`).
- **The rating filter is on the deciding Player's rating**, not both Players'. A strong Player's picks are worth
  imitating whoever they face, and it keeps more data.
- **Training reads the dataset while it trains.** 10 worker processes encode, shuffle (4,096 positions each) and
  sort positions into batches of similar card-row counts, which doubles GPU speed.
  - About 3,600 positions a second with 10 workers; 6,200 with `--compile` and 12 workers.
  - Nothing is stored: everything at float32 would be 48 GB.
- **AdamW**: learning rate 1e-3, warm-up over 2% of the budget, a cosine down to a tenth, batches of 256, bfloat16 on
  the GPU.
  - Every `--validate-every` positions it reports on every 8th validation shard, and saves the model (with its
    settings, format and validation history) and a checkpoint.
  - The same command resumes from the checkpoint. It refuses other settings.
- **Decisions with one Option are left out.** They teach nothing.
- **Baselines** (`evaluate.py`):
  - Random is the expected accuracy, the mean of 1/Options.
  - "Most-kept" picks the Option whose card (or done) was kept most often at that kind of Decision, over the
    training Games' records, unfiltered: the most-kept card overall.
  - The Card Economy Bot's Prices are scored only where the view holds the hand its Prices read, so not on records
    after setup. The model's accuracy on those same positions is reported beside it.
- **The registered model is the first experiment's** (all ratings, all Games, 1M positions; validation accuracy
  67.3%), copied to `.cache/models/imitation.pt`. The user had about an hour left, so a longer final run is left
  open; see Box 4.

**Memory: the laptop ran out once.**
- At 20:48 on 2026-11-18, systemd-oomd killed the desktop app's whole scope at 9.1 GB: the training started from its
  terminal, Claude, and three of the user's k3s pods (traefik, coredns, clinic-queue).
- The cause: Python 3.14's forkserver re-imports the caller's main module in each worker, so the 12 encoding workers
  each loaded PyTorch.
  - `positions.main_module_left_out()` now hides the main module while workers start. A test checks it.
  - Shuffle buffers were halved, and validation uses 4 workers.
  - Peak anonymous memory fell from 5.6 GB to 3.4 GB.
- Long runs now go as a user systemd service with `MemoryMax=6G` (`docs/guide.md`), so running out stops only the
  training. The laptop also rebooted once mid-run; checkpoints every 1M positions make reruns resume.

**Box 1: one command** — `uv run python -m ai.imitation.train`.
- It runs within the laptop's limits: 3.4 GB of RAM at peak with 10 workers, and 0.7 GB of GPU memory at batch 256.
- It resumes, and saves the model with `format_stamp()`, the settings and the validation history.
- `tests/ai/imitation/test_train.py` covers saving and resuming, and refusing other settings.

**Box 2: held-out accuracy.** `uv run python -m ai.imitation.evaluate --shard-share 8`: the registered model on an
eighth of the test Games, 89,764 positions.

| | Positions | Model | Random | Most-kept | Bot's Prices (model on the same) |
| --- | ---: | ---: | ---: | ---: | --- |
| All | 89,764 | **67.0%** | 30.9% | 53.8% | 38.6% (66.9%) |
| Buying cards | 49,071 | **65.6%** | 26.5% | 46.6% | 33.8% |
| Draft | 36,819 | **69.1%** | 36.1% | 63.1% | 44.2% |
| Prelude Cards | 2,568 | **64.0%** | 29.2% | 52.6% | 44.2% |
| Corporation | 1,306 | 65.5% | 50.0% | **66.2%** | 54.0% |
| Rated under 300 | 21,317 | 62.0% | 31.0% | 48.1% | 38.8% |
| Rated 500–599 | 20,970 | 69.2% | 30.9% | 56.5% | 38.4% |
| Rated 600+ | 29,620 | 69.5% | 30.8% | 56.7% | 38.3% |

- By Generation, the model holds 65.9–68.3% from Generation 1 to 10+. Most-kept falls to 38% in Generation 1,
  where setup buys dominate.
- It beats every baseline overall, in every Generation and rating band, and at every kind but the Corporation.
  There it ties the most-kept Corporation: 65.5% against 66.2% on 1,306 positions, within one standard error
  (1.3 points). The full table is in `.cache/models/runs/evaluate-test.txt`.

**Box 3: Match.** `uv run python -m ai.match imitation card_economy --games 600 --processes 4`.
- The Imitation Bot won **84.3% (81.2–87.0%)**.
- Mean Victory Points 127.0 against 99.9, and card Victory Points 35.8 against 16.0 (humans: about 28).
- Terraform Rating 47.7 against 45.2; 13.5 Generations; 0 stalled, 0 failed.
- Only the setup, Draft and buy picks differ, so drafting and buying as humans do is most of the gain.

**Box 4: rating filters, and Games without Prelude.**
- Each model was trained on 1M positions (cut from 4M when time ran short) with the same settings otherwise.
- All are evaluated on the same test Games with Prelude, on an eighth of the shards: 88,061 positions, 29,217 of
  them by Players rated 600+.

| Training Decisions | Validation (own filter) | Test, all | Test, rated 500–599 | Test, rated 600+ | Test, under 300 |
| --- | ---: | ---: | ---: | ---: | ---: |
| All Players, all Games | 67.3% | 67.0% | 69.2% | 69.5% | 62.1% |
| All Players, Games with Prelude only | 68.1% | **67.8%** | 70.0% | 70.2% | 62.6% |
| Players rated 450+ | 71.0% | 67.3% | **71.0%** | 71.1% | 59.2% |
| Players rated 550+ | 71.1% | 66.7% | 70.6% | 71.0% | 57.9% |
| Players rated 600+ | 71.2% | 66.8% | 70.6% | **71.3%** | 58.0% |

- **The rating filter helps for strong Players' picks:** +1.6 to 1.8 points at 600+ over no filter. A filtered model
  imitates weak Players worse.
- **How high before data runs out:** one pass over the 600+ training Decisions is only 977,672 positions, so the 1M
  budget already repeated them. 450+ gives about the same accuracy with far more data, so it is the setting for
  longer runs.
- **Games without Prelude don't help:** leaving them out gained 0.7–0.8 points at the same budget.
- **Left open:** the registered model is the unfiltered one, trained before these results. A longer run at 450+
  with Prelude Games only (`--min-rating 450 --prelude-games-only`) is the next model to try. Ticket 14 can start
  from it.

**Box 5: keep rates.** `uv run python -m ai.imitation.checks keep-rates --prelude-games-only`.
- The model buys through the whole setup chain itself, with the Corporation and Prelude Cards the Player chose.
- Over the test Games with Prelude, it is compared with Players' keep rates for each card. Those are the dataset's,
  which ticket 08 checked against tfmstats.com's Starting Hand page.
- 215 cards dealt 100+ times: **correlation 0.925**, mean absolute difference 13.2 points.
- Largest differences (the model's minus Players'):
  - Beam from a Thorium Asteroid −48, Terraforming Ganymede −48, Water Import from Europa −44, Noctis City −43,
    Ganymede Colony −41, Commercial District −38, Methane from Titan −35, Greenhouses −35, Domed Crater −33, Space
    Elevator −33, Satellites −33.
  - Herbivores +40, Imported Nitrogen +34, House Printing +30.
- **Likely causes** (reasoned from the list, not measured):
  - Each pick is greedy and one card at a time. The model picks the single most likely next card and stops as soon as
    "done" scores highest. Players keep each card as part of a plan.
  - Expensive cards that pay off only with a strategy (Jovian and space cards, City cards) are kept less often.
    Cheap, generally useful ones are kept more often.
  - The records also give setup buys in card-number order, so the model learned an order, not a set. Replays give
    the order the Players bought in.
  - Keeping the top-k cards by chance, rather than buying greedily, may close much of the gap. Left to ticket 14,
    which revisits buying with every Decision. `checks.py` now also prints the cards kept per setup, which would
    show directly whether the model keeps fewer cards overall.

**Box 7: overfit test.** `test_a_small_training_run_learns_every_pick_of_a_few_positions_on_the_cpu` trains a width-32,
one-layer model on the 22 setup, Draft and buy positions of ticket 12's hand-written seed-7 Game. After 300 steps on
the CPU it gets every pick right, in about 5 seconds. `test_model.py` also checks that each Option gets one score,
that padding never wins, and that a saved model scores alike and refuses another encoding format.

**Box 8: GUI and speed.**
- The setup screen offers "Imitation Bot" for each Player once `.cache/models/imitation.pt` exists. A Game with both
  Players set to it played through setup, the Draft and buying into Generation 2's Action phase in the browser pane.
- Its picks in 3 seeded Games:
  - with the model: 472 picks, **mean 5.2 ms, at most 14.7 ms**;
  - with the Card Economy Bot for the rest: 728 picks, mean 6.9 ms, at most 25 ms.
- `test_a_pick_takes_well_under_a_second` holds a Draft pick under 0.25 s.
- The dev panel's Bot tab explains a model pick with each Option's chance in percent. Without a model, the GUI
  doesn't offer the bot, and `make_controller("imitation")` says how to train one.

**Code review** (`/code-review` against bd17e05: one standards and one spec subagent, read-only while training ran).

Fixed:
- **Both reviews:** the Imitation Bot reached the replay code, and with it the dataset readers, through
  `positions.py`.
  - The position arrays and batching moved to `encoded.py`, which reads neither the dataset nor the engine.
  - A test checks that importing `ai.imitation.bot` loads no `ai.recorded_games` module. The engine itself still
    comes in through `ai.controller`, the seam the fair-play test allows.
- **Spec review:** the synergy probe could put the Corporation into the offer in place of the one the Player chose.
  The chain then refused a pick that isn't offered. Fixed, with a test using a Corporation nobody was dealt.
- **Standards review:**
  - "worth" in the model's docstring.
  - "rates" for the model's preference (CONTEXT.md keeps "rating" for Board Game Arena's).
  - The bot repeated the position encoding; it now uses `Position.of`.
  - `nn.Embedding(4, …)` beside `range(4)`.
  - The four probe sums in magic slots, now named.
  - `scored` lived in the training command and was imported by the other commands; it is now in `model.py`.
  - The Imitation Bot was missing from CONTEXT.md.
- **Spec review, missing pieces:**
  - Training now says so when it falls back to the CPU.
  - `checks.py` prints the cards kept per setup.

Left as they are:
- **The explanation puts a chance in `PricedOption.price`.** The dev panel shows one number per Option, and the label
  says it is a chance in percent. A separate type is left until a second Controller needs one.
- **The most-kept baseline ignores `--min-rating` and `--prelude-games-only`.** The box asks for the most-kept card
  overall.
- **Keep rates and synergies are probed on setup records.**
  - At setup, records know everything a Player View holds except who goes first and the decks' sizes.
  - The keep rate is conditional on the Player's own Corporation and Prelude Cards, as the comparison with Players
    needs.
- **Validation uses every 8th validation shard.** It chooses between runs. Box 2 and Box 4 use the test Games.
- **Replays pair with Games within a shard.** The dataset writes both into the same shard.
- **Smaller smells:**
  - `Position`'s evaluation fields: the Card Economy Bot's pick, Game id, rating, source.
  - The `(folder, split, settings, workers, …)` parameters travelling together.
  - Test modules importing each other's fixtures (`example`, `write_dataset`), as `tests/ai/recorded_games` already
    does.

**Box 6: synergies — not ticked yet.**
- tfmstats.com didn't answer from the laptop all evening on 2026-11-18. curl timed out after 20 s, while other sites
  loaded, so its Combinations page couldn't be read.
- As a stand-in, the 10 pairs come from the training Games only, ranked by lift: the pair's win rate minus what its
  parts predict, among pairs kept 200+ times in Prelude Games not conceded.
  - Tharsis Republic with Early Settlement (+13.9 points) and with Self-Sufficient Settlement (+12.4).
  - Saturn Systems with Io Research Outpost (+11.2).
  - Mining Guild with Self-Sufficient Settlement (+8.9).
  - Saturn Systems with Galilean Mining (+4.9).
  - Credicor with Mining Operations, Vitor with Metals Company, Mining Guild with Aquifer Turbines, Point Luna with
    Research Network, and Saturn Systems with Acquired Space Agency (+3.0 to +3.9).
- The probe's results follow below.
- **Result:** `uv run python -m ai.imitation.checks synergies --most-games 1500 --pairs …` probed the registered model on
  the first 1,500 test Games, 2,962 setup records with Prelude Cards kept. For each pair it gives the chance of the
  Corporation with and without the Prelude Card dealt, and of keeping the Prelude Card first with and without the
  Corporation chosen.

  | Corporation | Prelude Card | Corporation with | without | Prelude Card with | without | Both higher |
  | --- | --- | ---: | ---: | ---: | ---: | --- |
  | Tharsis Republic | Early Settlement | 48.4% | 48.3% | 24.8% | 23.9% | yes |
  | Tharsis Republic | Self-Sufficient Settlement | 48.6% | 48.3% | 10.6% | 10.7% | no |
  | Saturn Systems | Io Research Outpost | 48.6% | 47.9% | 28.4% | 28.3% | yes |
  | Mining Guild | Self-Sufficient Settlement | 50.4% | 50.2% | 11.0% | 10.6% | yes |
  | Saturn Systems | Galilean Mining | 48.6% | 47.9% | 34.9% | 34.7% | yes |
  | Credicor | Mining Operations | 60.9% | 61.3% | 30.3% | 30.3% | no |
  | Vitor | Metals Company | 67.3% | 66.2% | 41.8% | 41.7% | yes |
  | Mining Guild | Aquifer Turbines | 50.2% | 50.3% | 66.0% | 65.8% | no |
  | Point Luna | Research Network | 74.0% | 73.3% | 20.6% | 20.6% | no |
  | Saturn Systems | Acquired Space Agency | 45.3% | 48.3% | 10.1% | 10.3% | no |

- **Not learned:** 5 of 10 pairs score higher together for both parts, but by under 1.1 points, which is no
  synergy. The box stays unticked.
- Likely causes, not measured:
  - The registered model saw only 1M positions, and setup's Corporation and Prelude Card Decisions are under 5% of
    them.
  - Pair effects are rare in Players' picks: each pair is kept 200–300 times in the training Games.
- **Open:**
  - Read tfmstats.com's Combinations page when it answers, and rerun the probe on its 10 pairs.
  - Train longer (the 450+, Prelude-only run of Box 4), possibly weighting setup Decisions.
  - Rerun this probe. It takes about 15 minutes on 1,500 Games.

**Open points:**
- Box 6 (above).
- ~~A longer training run with the best settings from Box 4.~~ Done on 2026-11-19; see below.
- A Match against the Flat Playout Bot, which the README's training-progress table asks of each rung. Not run, for
  time.
- Keep rates: buying by chance rather than greedily, and checking the cards kept per setup (Box 5).
- Ticket 14 extends imitation to every Decision. Payment Decisions (up to 526 Options) need batching apart.

### 2026-11-19 — a longer run replaces the registered model (Claude)

On the user's go-ahead, Box 4's best settings were trained for longer:
```bash
uv run python -m ai.imitation.train --positions 10000000 --validate-every 2000000 --min-rating 450 \
  --prelude-games-only --compile --workers 10 --out .cache/models/runs/r450-prelude.pt
```
- It ran as a user systemd service capped at 6 GB, at 4.2 GB peak and about 6,500 positions a second. That is
  26 minutes for 10M positions, about 4.2 passes over the 2,390,005 training positions.
- Validation accuracy: 72.2% at 2M, 74.0% at 4M, 74.7% at 6M, 75.2% at 8M and 75.3% at 10M. The loss was still
  falling, with no sign of overfitting.
- It is now the registered model, `.cache/models/imitation.pt`. The first one stays in `.cache/models/runs/all.pt`.

**Box 2 again, the same test positions as above** (`uv run python -m ai.imitation.evaluate --shard-share 8`):

| | Positions | First model | **This model** | Most-kept | Bot's Prices |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 89,764 | 67.0% | **71.7%** | 53.8% | 38.6% |
| Buying cards | 49,071 | 65.6% | **71.6%** | 46.6% | 33.8% |
| Draft | 36,819 | 69.1% | **72.0%** | 63.1% | 44.2% |
| Prelude Cards | 2,568 | 64.0% | **70.1%** | 52.6% | 44.2% |
| Corporation | 1,306 | 65.5% | **69.0%** | 66.2% | 54.0% |
| Rated under 300 | 21,317 | 62.0% | 64.2% | 48.1% | 38.8% |
| Rated 500–599 | 20,970 | 69.2% | 75.0% | 56.5% | 38.4% |
| Rated 600+ | 29,620 | 69.5% | **75.3%** | 56.7% | 38.3% |

- By Generation it holds 70.0–73.3%.
- It now beats every baseline at every kind, the Corporation included. That was the first model's one tie.

**Box 3 again:** `uv run python -m ai.match imitation card_economy --games 600 --processes 8`.
- The Imitation Bot won **89.7% (87.0–91.9%)**, up from 84.3%.
- Victory Points 130.8 against 96.8, card Victory Points 37.8 against 15.9, Terraform Rating 48.4 against 44.3.
- 13.3 Generations; 0 stalled, 0 failed. The Match took 3.5 minutes with 8 processes, at 2.8 GB peak.

**Box 6 again:** the same probe, the same 10 stand-in pairs and 2,962 setup records.

| Corporation | Prelude Card | Corporation with | without | Prelude Card with | without | Both higher |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Tharsis Republic | Early Settlement | 44.9% | 33.2% | 42.0% | 17.9% | yes |
| Tharsis Republic | Self-Sufficient Settlement | 34.9% | 34.4% | 8.4% | 4.5% | yes |
| Saturn Systems | Io Research Outpost | 59.9% | 46.3% | 37.3% | 21.2% | yes |
| Mining Guild | Self-Sufficient Settlement | 42.0% | 40.9% | 7.5% | 4.4% | yes |
| Saturn Systems | Galilean Mining | 66.7% | 45.5% | 47.9% | 27.1% | yes |
| Credicor | Mining Operations | 68.4% | 67.1% | 27.0% | 26.2% | yes |
| Vitor | Metals Company | 68.0% | 65.8% | 38.1% | 37.5% | yes |
| Mining Guild | Aquifer Turbines | 43.7% | 40.7% | 77.6% | 66.3% | yes |
| Point Luna | Research Network | 77.0% | 76.6% | 17.7% | 14.9% | yes |
| Saturn Systems | Acquired Space Agency | 58.7% | 46.5% | 0.0% | 0.0% | no |

- **The longer run learned synergies.** 9 of 10 pairs score higher together for both parts, by up to 24 points.
  The pairs with the highest lift move most:
  - Tharsis Republic with Early Settlement: +11.7 for the Corporation, +24.1 for the Prelude Card.
  - Saturn Systems with its Jovian Prelude Cards: +13.6 and +16.1, +21.2 and +20.8.
  The first model, at 1M unfiltered positions, had moved under 1.1 points.
- **The tenth pair can't be measured this way.**
  - Acquired Space Agency is the highest-numbered Prelude Card (267 of 267).
  - The records list kept cards in card-number order, so the first Prelude Card kept is never Acquired Space Agency
    when another is kept. The model learned that order, giving 0.0% both ways.
  - The Corporation part still rose from 46.5% to 58.7%.
  - This is the same card-order trait as Box 5's buying. A probe over the whole keeping chain (kept at all, not
    kept first) would measure it.
- **Still not ticked**, for two reasons:
  - The pairs are a stand-in ranked from the training Games. The box asks for tfmstats.com's Combinations page,
    which still timed out on 2026-11-19.
  - One pair isn't measurable with this probe.
  - To close it: read the Combinations page when it answers, change the probe to "kept at all", and rerun
    `uv run python -m ai.imitation.checks synergies --most-games 1500 --pairs …` (about 9 minutes).

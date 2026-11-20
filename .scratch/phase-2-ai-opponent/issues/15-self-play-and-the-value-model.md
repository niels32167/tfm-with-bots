# 15 — Self-play and the Value Model

**What to build:** A training loop that starts from the Imitation Model and improves by self-play, and the Value Model, which estimates a Player's chance of winning from their Player View.

**The loop:**
- Many processes play Games on the CPU cores, with one process batching model evaluations on the GPU if that proves faster.
- Opponents come from a pool of earlier versions, including the Card Economy Bot and the Imitation Model, so that the model doesn't forget how to beat old strategies.
- A new version joins only if it wins a Match against the current best.

**The Value Model:** it first learns from Recorded Games' results and from self-play. A Controller then picks by trying each Option on a Sampled Position, averaged over a few samples, and comparing what the model says. This is the TD-Gammon recipe, and it fits cheap copies and a game with chance. Whether the policy from the Imitation Model stays to narrow which Options are tried is a call for this ticket.

**Limits:** 16 cores, 12 GB of RAM, a 6 GB GPU and limited disk. Training is streamed and checkpointed, and long runs need my OK. Games aren't stored unless a check needs them.

**Blocked by:** 07 — Sampled Positions; 14 — Imitation Model for all Decisions

**Status:** ready-for-agent

- [x] One command runs the loop, stops and resumes safely, and stays within the limits above, with memory and disk measured under Comments.
- [x] Progress is visible: a rating over time against a fixed set of old Controllers, plotted or logged.
- [x] The result wins a Match against the Controller from ticket 14, with the interval above 50%, using a budget of a few seconds per Decision or less.
- [x] Its Games against itself are recorded beside the human benchmark.
- [x] Test: the loop runs end to end on a tiny model in the normal test suite, with no GPU, and its Controllers go through the fair handle.
- [x] A training run's settings, seed and engine version are saved with its model, so that it can be repeated.

## Comments

### 2026-11-20 — implemented (Claude)

All six boxes are ticked; the evidence follows. The code:
- `ai/value/`:
  - `encoded.py`: the Value Model reads a Player View alone (no Decision, no Options, the `deciding_*` fields
    cleared, since a Player View doesn't say what the other Player decides). It also defines `FOLLOW_UPS`.
  - `samples.py`: positions with their Player's result (1, ½, 0) and Victory Point margin, from Recorded Games'
    replays and the loop's Games. Its worker processes load no PyTorch.
  - `model.py`: the Imitation Model's transformer with a new two-number head (chance of winning, margin), warm-started
    from `imitation.pt`.
  - `train.py`: training and measuring on streamed batches.
  - `bot.py`: the Value Bot.
  - `loop.py`: `uv run python -m ai.value.loop`, the self-play loop.
- `ai/match.py`: `views_along(replay, viewer_at)` steps a Replay through the engine and gives the Player View that
  is asked for (`match.py` may import the engine; Controllers may not).
- `ai/imitation/model.py`: `read()` (tokens through the transformer) split out of `forward`, so that the Value Model
  shares it. `load_model(..., kind=ValueModel)`. Saved models load as before.
- `ai/imitation/bot.py`: `likeliest_picks(positions)`, the Imitation Model's pick for many positions in one batch.
- `ai/controllers.py`: `value`, "Value Bot", available once `.cache/models/value.pt` is registered
  (`python -m ai.value.loop --register`).
- `ai/imitation/encoded.py`: a position with no Options now has shape (0, 42), not (0,).

**Decisions made with the user** (one opening batch, every recommendation taken):
- **The Imitation Model's policy stays and narrows the Options tried.**
- **Value targets: both.** A warm start on Recorded Games' results, then the loop's own Games.
- **Opponents: half self, half pool.** Half the Games are the best version against itself. The other half are
  against every earlier accepted version, the Imitation Bot and the Card Economy Bot, taken in turn.
- **Time: a first 1-hour run, to be continued later.** Laptop time came to about 76 minutes in all: pilots and probes
  about 25, the loop 36, the Match 6.5, the self-play check 6.3 and the full test suite 2.2.

**Chosen by Claude, on the user's instruction to take the recommendation after the first batch:**
- **Options are rated after their follow-ups.** The first pilot's warm-started Value Bot lost all 60 Games against the
  panel. The cause: after "Play Capital (26 MegaCredits)" the Player View changes only in `deciding` and
  `playing_card`. The card is still in hand and nothing is paid until its Payment and Area are answered, so every
  Action looked the same. Now the Imitation Model answers an Option's follow-up Decisions (`FOLLOW_UPS`: payment,
  area, target and the like), batched over all trials, before the Value Model rates the position. The Value Model
  learns only from positions where no follow-up waits.
- **A share of each Game's positions is kept** (`--warm-keep 0.1` for Recorded Games, `--keep 0.5` for the loop's).
  With every position kept, the 1.5M-position warm start overfit: training loss 0.33, validation loss 0.98 (worse than
  a coin's 0.69). Every position of a Game has the same result, and a shuffle buffer of 4,096 holds about a dozen
  Games, so the model learned which Game it was in. With a tenth kept, validation loss was 0.46 and the winner was
  rated likelier at 77.3% of validation positions.
- **An Option is tried only if the policy gives it at least half the likeliest Option's chance** (`SHARE = 0.5`), of
  the 6 likeliest. It is the user's "keep the policy to narrow" with the narrowing by share, not count. Measured with
  the same warm start against the Imitation Bot, on seeds from 1,900,000 (not the final Match's):

  | Narrowing | Games | Score |
  | --- | ---: | --- |
  | the 6 likeliest | 20 | 0% |
  | share 0.2 | 40 | 47.5% (32.9–62.5%) |
  | share 0.5 | 40 | 70.0% (54.6–81.9%) |

  Where the policy is sure, the Value Model's error shouldn't overrule it. A pick with one Option left over is the
  Imitation Bot's.
- **No GPU process batches the evaluations.** The ticket allowed one "if that proves faster". A pick's forward pass of
  24 positions takes 23 ms on one CPU thread, and a pick 25 ms on average, so 10 CPU processes play about 1 Game a
  second. A GPU process would add inter-process traffic for little gain. Not measured further.
- **The gate is a point score of 55% over 60 Games,** not a Match whose interval clears 50%. That would need about 400
  Games a round, most of the hour. A wrongly accepted version is caught by the rating against the fixed panel, and
  box 3's Match is the ladder's real test.
- **The rating** is Elo against a fixed panel: the Card Economy Bot, the Imitation Bot (Draft and buy) and the
  Imitation Bot, with the Imitation Bot at 0. Each version plays 20 Games against each, on the same seeds for every
  version. The panel's own ratings are fitted once from a round robin.
- **Run settings:** the defaults, `--minutes 35`.
  - Warm start: 1.5M positions.
  - Each round: 120 Games, 100,000 positions trained, a 60-Game gate, 20 rating Games against each of the panel.
  - 10 Match processes and 8 batch workers.
  - The Value Bot tries the 6 likeliest Options, each on 4 Sampled Positions, at share 0.5.
- **The margin as a secondary signal** (weight 0.25), as the spec allows.
- **What is saved with each model** (box 6): `settings` (every fixed setting, the seed and the path of the
  Imitation Model) and `provenance`:
  - the engine's version (0.1.0);
  - the commit (8857ac9, committed before the run so that it names code that exists);
  - whether there were uncommitted changes;
  - the encoding's format stamp;
  - Python's and PyTorch's versions;
  - since the code review, the SHA-256 of the Imitation Model's file, as the settings name it only by path.

  The run's `run.json` holds the same settings, and resuming with other settings is refused
  (`test_the_loop_runs_stops_and_resumes_through_the_fair_handle`).

**Box 1: one command, stops and resumes, within the limits.**
```bash
systemd-run --user --same-dir --unit=tm-value -p MemoryMax=6G -p MemorySwapMax=0 \
  uv run python -u -m ai.value.loop --minutes 35
```
- `state.json` lists the steps done, and each step's output is written whole or not at all. The test stops a run
  inside round 1's gate and resumes it without playing round 1 again. The pilot was stopped with
  `systemctl --user stop` mid-step and restarted.
- **Memory**, from the cgroup's `memory.stat` anon every 5 s:
  - warm start (8 batch workers and training on the GPU): 2.2 GB, rising to 4.5 GB with the validation workers;
  - rounds (10 Match processes, each holding both models): 4.4–4.65 GB;
  - **peak 4.65 GB** (systemd: 4.6 GB, page cache included), under the 6 GB cap;
  - the final Match: 3.7 GB; the self-play check: 3.7 GB.
- **Disk:** the run folder is 17 MB. That is six versions of 2.9 MB each, and the last 3 rounds of Games
  (`--buffer-rounds`) at about 33 KB each (120 Replays). Older rounds are deleted. No other Games are stored.
- **Time:** the warm start took 5.3 minutes and a round about 7 minutes: Games 3, training 1, gate 1.7, rating 1.6.

**Box 2: progress over time.** `ratings.tsv` in the run folder; each row is also printed.

| Round | Version | Accepted | Minutes | Rating (Imitation Bot = 0) | vs Card Economy | vs Imitation (Draft and buy) | vs Imitation |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | v000 (warm start) | yes | 5.7 | +72 | 95% | 75% | 70% |
| 1 | candidate-001 | yes, as v001 (55.0%) | 12.8 | +51 | 100% | 80% | 55% |
| 2 | candidate-002 | no (45.0%) | 20.4 | −58 | 95% | 70% | 40% |
| 3 | candidate-003 | no (51.7%) | 27.1 | +13 | 100% | 75% | 50% |
| 4 | candidate-004 | no (53.3%) | 34.3 | −5 | 100% | 70% | 50% |

The panel's own ratings: Card Economy Bot −675, Imitation Bot (Draft and buy) −177, Imitation Bot 0.
- **Most of the gain is the warm start.** In 4 rounds, self-play hasn't improved on it. The ratings differ by less
  than their noise: 20 Games against each of 3 Controllers is about ±60 Elo.
- **Round training repeats too few positions.** The loss was 0.18 in round 1, against 0.46 at the warm start, so the
  model learned its 18,000 positions by heart: 120 Games, half of each Game's positions kept, 100,000 positions
  trained. The loss rose to 0.35 by round 4 as three rounds' Games were kept. A continued run should train for about
  one pass over what is kept, or play more Games a round.

**Box 3: Match against ticket 14's Controller.** `uv run python -u -m ai.match value imitation --games 400 --processes
10`, with v001 registered (`.cache/models/runs/match-15-value.txt`):
- The Value Bot won **57.0% (52.1–61.8%)**, 228 to 172, with 0 stalled and 0 failed.
- Mean Victory Points 93.2 – 90.3, card Victory Points 20.4 – 20.0, Terraform Rating 44.7 – 42.4.
- Mean Generations 10.36.
- Player 1 won 44.5% of Games, and the first player 53.5%.
- **Time per Decision:** 1,058 picks in 2 seeded Games against itself, on one core: **mean 25 ms**, median 4.6 ms,
  99th percentile 279 ms, slowest 334 ms (a Sell Patents Decision with 25 Options). The budget is a few seconds.

**Box 4: self-play beside the human benchmark.** `uv run python -m ai.imitation.checks self-play --controller value
--games 200 --processes 10` (`.cache/models/runs/self-play-15.txt`). 200 Games finished, 0 stalled.

tfmstats.com answered again on 2026-11-20, so the flip rate is shown both ways. The site's Awards page was read with 2
Players, Tharsis, Prelude and Draft on, both Players rated 450+, and Colonies unfiltered (its toggle's off state is also
its unfiltered state). It was Reset afterwards.

| | Value Bot | Imitation Bot (ticket 14) | Players rated 450+ (dataset) | tfmstats.com |
| --- | ---: | ---: | ---: | ---: |
| Games | 200 | 200 | 4,111 | |
| Generations | 10.3 | 10.4 | 10.5 | |
| Victory Points (a Player) | 92.2 | 91.4 | 98.5 | |
| card Victory Points (a Player) | 20.4 | 19.6 | 21.4 | |
| Awards funded per Game | 2.01 | 1.83 | 2.73 | |
| **Flip rate** | **15.7%** | 10.4% | 7.8% | 9.3% (58,715 funded) |

| Award | funded per Game, mean Generation, share lost (Value Bot) | (Players, dataset) | tfmstats.com: funded, mean Generation, flip |
| --- | --- | --- | --- |
| Banker | 0.29, 9.5, 23% | 0.41, 8.7, 6% | 8,644, 8.7, 6.7% |
| Landlord | 0.61, 7.2, 17% | 0.65, 7.5, 11% | 14,531, 7.5, 11.3% |
| Miner | 0.24, 7.6, 13% | 0.52, 7.7, 7% | 11,035, 7.7, 11.4% |
| Scientist | 0.54, 9.0, 8% | 0.62, 7.9, 6% | 13,697, 7.7, 6.1% |
| Thermalist | 0.33, 9.1, 21% | 0.53, 8.5, 9% | 10,808, 8.5, 10.4% |

| Milestone | claimed per Game, mean Generation (Value Bot) | (Players) |
| --- | --- | --- |
| Builder | 0.74, 6.7 | 0.77, 6.5 |
| Gardener | 0.88, 6.6 | 0.77, 6.4 |
| Mayor | 0.14, 7.2 | 0.32, 6.9 |
| Planner | 0.51, 5.5 | 0.57, 5.6 |
| Terraformer | 0.71, 7.3 | 0.57, 7.0 |

- Game length, Victory Points and Milestones are as close to Players' as the Imitation Bot's were.
- It funds more Awards than the Imitation Bot did (2.0 a Game against 1.8), but loses more of them (15.7% against
  10.4%). The Value Model doesn't see that the other Player may overtake it. Search (ticket 16) may.
- Mayor is still claimed half as often as Players claim it.
- The site's flip rate of 9.3% is near the dataset's 7.8%. The site counts Colonies Games too, and its filters are
  Board Game Arena ratings for both Players. Its mean Generations match the dataset's within 0.2.

**Box 5: the test.** `tests/ai/value/test_loop.py` runs the loop on the CPU, in one process, in about 10 seconds:
- a tiny model (width 16, one layer) on a two-Game dataset;
- the warm start, the panel, rating v000, and one round of play, train, gate and rate;
- a crash in the gate, then a resume that doesn't replay the round;
- a `--minutes 0` invocation that starts no step;
- a refusal of other settings.

It wraps `ai.match.handle_for` and `ValueBot.pick`, and checks that every Game was played through ai.match and that
every Value Bot pick got a `Handle`. Also:
- `test_bot.py`:
  - it picks the same from two Games its Player can't tell apart;
  - it rates Options after their follow-ups;
  - it narrows by share;
  - a pick takes under 0.5 s;
  - it loads no Recorded Game code;
  - it is registered.
- `test_samples.py`, `test_model.py`:
  - samples and their targets;
  - a training run that learns a few positions;
  - the batch workers load no PyTorch.

**Box 6:** see "What is saved with each model" above. The registered `.cache/models/value.pt` is v001's file, which
was saved as `candidate-001` before it passed its gate, so its saved `version` says `candidate-001`.

**GUI:** with `.cache/models/value.pt` registered, the setup screen offers "Value Bot" for each Player. A Game between
two reached Generation 3 in the browser pane with no console or server errors.

**Code review** (`/code-review` against 21ab929: one standards and one spec subagent, read-only during the run).

Fixed:
- **Standards:**
  - Three lines over 120 columns.
  - The _Avoid_ words "choice" (a test helper), "worth" (`model.py`) and "copies" (`bot.py`).
  - The loop's docstring didn't list `--register` among the settings that may change.
  - `afterstates` is now `trials`.
  - The policy ran twice per pick; `rated` now takes the Options already chosen.
  - The bot reached into the Imitation Bot's model; that is now `ImitationBot.likeliest_picks`.
  - `chosen` named both a function and a list; the function is now `viewer_at`.
  - The ratings line was rebuilt.
- **Spec:**
  - The Imitation Model was saved only as a path, so retraining it would silently change a repeat. Its SHA-256 is now
    saved too.
  - `--rounds`' help said "no limit" for 1,000.
  - A Recorded Game whose log lacks a final score gave a false margin of 0; it now gives no samples.

Left as they are:
- **`ValueModel` subclasses `ImitationModel`** and replaces its head (Refused Bequest). It keeps the weights' names
  the same, which the warm start needs.
- **`views_along` lives in `ai/match.py`,** a training helper in the Match tool, because only it may import the
  engine (ADR 0013's fair play).
- **The `made` closures in `warm_start` and `train`, the write-then-replace pattern and the margins line repeat**
  small shapes.
- **The run's state is a plain dict,** and version names are built with f-strings.
- **The word "policy"** for the Imitation Model's prediction, as the ticket uses it.
- **Seeds of the gate and the rating collide after 400 rounds,** far past any planned run.
- **The panel's fit adds the same drawn imaginary Game** that keeps a version's rating finite.
- **The 55% gate and the CPU-only evaluations:** see the calls above.

**Open points:**
- **Continue the run:** `uv run python -u -m ai.value.loop --minutes <n>` (same defaults) goes on from round 5.
  First consider fewer positions trained per round (`--train-positions` is a fixed setting, so that means a new run).
  Self-play hasn't yet improved on the warm start.
- **Awards:** the flip rate rose to 15.7%.
- **A Match against the Flat Playout Bot**, still not run.
- **Search with the Value Model** (ticket 16) is the next rung. This ticket's afterstate trials are a one-step search
  it can build on.


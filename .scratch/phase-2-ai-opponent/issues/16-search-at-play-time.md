# 16 — Search at play time

**What to build:** A Controller that searches during play: it builds a tree over Sampled Positions, using the model to narrow Options and the Value Model to judge positions, within a time budget per Decision.

This is where spare seconds become strength. Decide:
- how samples are shared across the tree, or whether each sample gets its own (information set MCTS, or one tree per Sampled Position);
- how to treat the opponent's Decisions and chance, such as card draws;
- how to spend the budget, since many Decisions don't need much of it.

The quick test showed that playout counts matter a lot: going from 5 to 100 per Option took a bot from 3% to 84% against the same opponent. But random playouts undervalue engine building, so check how much rollouts and the Value Model each contribute.

**Blocked by:** 15 — Self-play and the Value Model

**Status:** ready-for-agent

- [x] The time budget is a setting, and the Controller keeps to it in the GUI, with the default chosen so that a Game is pleasant to play.
- [x] Strength against budget is recorded under Comments, for example 0.1, 1 and 5 seconds per Decision, against the Controller from ticket 15.
- [x] It wins a Match against the Controller from ticket 15, with the interval above 50%, at the default budget.
- [x] Test: it plays only through the fair handle, and its picks are equal for equal Player Views given the same seed.
- [x] It is selectable in the GUI.

## Comments

### 2026-11-21 — implemented; the ladder Match not yet won (Claude)

Four boxes are ticked. **Box 3 is not:** in two 400-Game Matches on seeds 0–199 the Search Bot beat the Value Bot
in 51.5% (0.1 s) and 53.0% (1 s) of Games, and neither interval clears 50%. The evidence and what to try next follow.

The code:
- `ai/search.py`: the Search Bot (its docstring explains the search in full).
- `ai/controllers.py`: `search`, "Search Bot", available once `.cache/models/value.pt` is registered. Settings may
  follow a registered name, as in `search?seconds=5&leaves=playouts`: the Match tool, the server and Replay files take
  them alike (`name_and_settings`, `settings_of`). A Controller registered without `settings` refuses them.
- `server/session.py`: a Controller offered on the setup screen may be named with settings, and is labelled with them
  ("Search Bot (seconds=5)").
- `ai/value/bot.py`: `narrowed(chances, tried, share)`, the Options both bots try, is shared.
- `ai/imitation/bot.py`: `chances_at(position)`, the Imitation Model's chances at a Sampled Position's Decision.
- `CONTEXT.md`: **Search Bot**.

**Decisions made with the user** (one opening batch, every recommendation taken but one):
- **Information set MCTS, one tree.** The nodes are the Player's own Decisions as they see them; each walk down it is
  on a fresh Sampled Position, so hidden cards are averaged over rather than known.
- **Default budget: 1 second per Decision.** The recommendation added: lower it if 1 s proves no stronger than 0.1 s.
- **Laptop time: about 1.5 hours** (the user's own pick, against the 3-hour recommendation). On seeing the sweep would
  run over, the user said to run the final Match without asking. Laptop time came to about 2 hours: pilot 4 minutes,
  sweep 42, the two final Matches 10.5 and 56.5, measurements and tests the rest.
- **The Value Model at the leaves, with one check by random playouts.**

**Chosen by Claude** (on the user's standing instruction to take the recommendation after the first batch):
- **The Options searched are the Value Bot's**: of the 6 the Imitation Model rates likeliest, those with at least half
  the likeliest one's chance. If one is left, it is picked at once and the budget isn't spent. This is the budget's
  main saving: at 1 s, 84 of one Player's Decisions in a Game were searched (the 2026-11-21 timing Game below).
- **Common random numbers at the root.** Each Sampled Position is walked once for every Option searched, from the same
  seeds, and the Option with the best mean result is picked. So the root needs no exploration constant, and at the
  smallest budget the bot is the Value Bot with a deeper rating.
- **The other Player's Decisions are chance**, as the cards drawn are: an Option is drawn in proportion to the Imitation
  Model's chances, narrowed by the same share. Follow-ups of either Player (FOLLOW_UPS) are answered by the Imitation
  Model's likeliest, as in the Value Bot.
- **A walk stops** at the Player's own next Decision, after 2 of the other Player's Decisions (`horizon`), or at the
  end of the Game, and the Value Model rates the position there. A node grows below an Option once the Option has been
  rated, and its Options are found again by label (and by count, should two share a label). PUCT picks among them, with
  the Imitation Model's chances as priors, the times each was offered in place of the node's visits, and constant 0.25.
- **Keeping to the budget:** a Sampled Position is begun only if it would end in time at the pace of the slowest so
  far, and a walk only if it would at the pace of the slowest walk. A Sampled Position whose walks don't all finish is
  left out, so that every Option is rated on the same ones. The first is always walked whole. The test first caught an
  overrun of 20 ms on 0.4 s with only the Sampled Position check, and then 3 ms; with both checks it held in 8 runs.
- **The budget is a setting** of the Controller (`seconds`; `samples` caps the Sampled Positions instead, which makes
  picks repeatable) and follows its name elsewhere: `search?seconds=5`. The setup screen offers "Search Bot" at the
  default; it has no field for the budget.
- **The full suite:** 2,245 tests passed in 2.5 minutes, capped (peak 1.9 GB). Ruff is clean on the touched files at
  120 columns.

**Costs** (one core, laptop on mains, "performance" profile):
- A forward pass of either model costs about 2 ms a position on one thread, and batching doesn't lower that. Encoding a
  Player View costs another 0.25–1.1 ms. A mid-Game walk answers about 2.8 Decisions by model and costs about 10 ms.
- So 1 s buys only about 4–10 Sampled Positions at a mid-Game Action with 3–6 Options searched. Late in the Game, walks
  that end the Game need no model and hundreds fit.
- One Game at 1 s against the Value Bot took 84 s on one core: 84 Decisions searched, 0.93 s each on average, 1.004 s at
  most. In a 10-process Match a Game took about 2 minutes, and a 400-Game Match 56.5 minutes (peak 3.6 GB).

**Box 2: strength against budget**, against the Value Bot (`value`, v006), on seeds from 3,000,000 (not the final
Match's), with `uv run python -m ai.match "search?seconds=…" value --games N --processes 10 --first-seed 3000000`
(`.cache/ticket-16/`):

| Budget per Decision | Games | Search Bot score | Victory Points | Minutes |
| --- | ---: | --- | --- | ---: |
| 0.1 s | 100 | 60.5% (50.7–69.5%) | 92.0 – 88.8 | 2.8 |
| 1 s | 100 | 59.0% (49.2–68.1%) | 93.3 – 91.9 | 14.7 |
| 1 s (pilot, before the sweep) | 20 | 60.0% (38.7–78.1%) | 91.1 – 91.0 | 3.9 |
| 5 s | 20 | 55.0% (34.2–74.2%) | 94.6 – 93.2 | 18.6 |
| 1 s, random playouts at the leaves | 40 | 52.5% (37.5–67.1%) | 90.1 – 89.6 | 6.0 |

- **More time didn't buy clear strength.** 0.1 s and 1 s scored alike, and 5 s no better in its 20 Games. The final
  Matches (box 3) show the sweep's 0.1 s score was luck: 60.5% in 100 Games, then 51.5% in 400.
- **The Value Model contributes more than random playouts:** 59.0% against 52.5% at 1 s, though within the noise of 40
  Games. Random playouts undervalue engine building, as the ticket expected.

**Box 3: the ladder Match**, `uv run python -u -m ai.match search value --games 400 --processes 10`
(`.cache/models/runs/match-16-search-0.1s.txt`, `match-16-search-1s.txt`):

| Budget | Score | Wins | Victory Points | card VP | Terraform Rating | Generations |
| --- | --- | --- | --- | --- | --- | ---: |
| 0.1 s | **51.5% (46.6–56.4%)** | 206 to 194 | 93.4 – 92.8 | 20.9 – 20.6 | 43.5 – 43.8 | 10.40 |
| 1 s | **53.0% (48.1–57.8%)** | 212 to 188 | 93.1 – 93.1 | 20.8 – 20.7 | 43.2 – 44.1 | 10.39 |

Both finished all 400 Games, none stalled. The default was set to 0.1 s after the sweep, under the rule above, and the
first Match was played at it. When it failed, the default went back to the user's 1 s and the second Match was played
on the same seeds. Two tries on the same seeds make even a pass weaker evidence, so both are reported. Together, 800
Games give 52.3%.

**Why search gains so little, as far as these numbers show:**
- **The Value Model's errors look like bias, not noise.** Averaging more Sampled Positions (more time) should shrink
  noise, and didn't help. A search that rates every position with the same model inherits its blind spots.
- **Few Sampled Positions fit.** At 2 ms per forward pass, 1 s gives 4–10 Sampled Positions at a mid-Game Action, and the
  other Player's drawn Options add noise to each.
- **The ticket's quick test isn't comparable:** 100 playouts per Option beat a heuristic that never looks ahead, and saw
  the hidden cards. Here both bots look ahead with the same model.

**Box 1:** the budget is the `seconds` setting (above), 1 s by default, the user's choice for a pleasant Game. In the
GUI (server and vite, browser pane at 1440x900), two Search Bots played from setup into Generation 4 with no console or
server errors. A second WebSocket timed the 122 updates: the slowest came 1.048 s after the one before, which is the
1 s pick plus the server's own work. None took over 1.1 s.

**Box 4: the test**, `tests/ai/test_search.py`, with tiny untrained models (width 16, one layer), on the CPU:
- it picks the same from two Games its Player can't tell apart, with the same random source and 4 Sampled Positions;
- it keeps to 0.1 s and 0.4 s, and walks more Sampled Positions given more;
- its tree grows below Options at the Player's own later Decisions;
- an Option that ends the Game is rated by the Player's result;
- with a share of 1 it picks as the Imitation Bot at once;
- random-playout leaves rate by results;
- it is registered, and its settings follow its name.

`tests/ai/test_fair_play.py` checks that no module of `ai/` but the three allowed imports the engine, `ai/search.py`
included. `tests/server/test_registered_controllers.py` checks settings by name on the server.

**Box 5:** the setup screen offers "Search Bot" for each Player (checked in the browser pane, above).

**Code review** (`/code-review` against 0696f31: one standards and one spec subagent, read-only, during the 1 s Match).

Fixed (none changes a pick, so the Matches stand):
- **Standards:**
  - `MOST_STEPS` used the _Avoid_ word "step"; it is `MOST_ANSWERED`.
  - `narrowed` repeated the Value Bot's `likeliest`; both now use `ai.value.bot.narrowed`. `SEEDS` is imported.
  - The `?` in Controller names was split in three places; `name_and_settings` does it once.
  - `leaves="mixed"` wasn't asked for and is gone.
  - The `# type: ignore` in the registry.
  - The test helper rebuilt a Handle by position; it uses `dataclasses.replace`.
- **Spec:**
  - The fairness test left the time budget on, so a busy computer could walk fewer Sampled Positions on one Game than
    the other. It now uses `samples` alone.
  - Options are keyed by label and count, in case two share a label. None did in 26,758 Decisions of 50 random
    Games (`experiments/16/label_repeats.py`).
  - A setting with no value (`search?seconds`) and a budget that isn't a number are refused when the Controller is
    made.

Left as they are:
- **Tests read `search()`'s result** (Edges, visits, the tree) as well as picks. As with the Value Bot's `rated` and
  `trials`, that result is the module's own interface.
- **A Sampled Position left out for time** has still added visits below the root; only the root's means pick.
- **An Edge keeps the prior** from the first Sampled Position that offered it.
- **The first Sampled Position is always walked whole**, which with `leaves=playouts` can run over a small budget.
- **The settings syntax is general** across registered Controllers, though only the Search Bot takes settings.
- **The setup screen has no field for the budget.**

**Open points (what to try for box 3):**
- **Keep the policy's likeliest Option unless another beats it clearly.** With common random numbers each Sampled
  Position gives a paired difference, so the bot can switch only when the difference is, say, 2 standard errors. That
  is ticket 15's lesson (the Value Model's errors mustn't overrule a confident policy) applied to the search. It would
  also stop early when the leader is clear, saving budget.
- **A better Value Model**, since search inherits its bias: bigger gates and longer self-play (ticket 15's open points),
  or training the Value Model on the Search Bot's own Games (expert iteration, out of scope by the spec unless search
  stalls, which it has).
- **Cheaper evaluations:** several threads per forward pass in the GUI, or a smaller model at the leaves, to fit more
  Sampled Positions per second.
- Tuning `horizon` (0 rates as the Value Bot does) and `exploration`, on Matches big enough to tell 3 points apart
  (about 1,000 Games each).

### 2026-11-21 — the paired rule tried; box 3 still not met (Claude)

The user picked the first open point: keep the Imitation Model's likeliest Option unless another beats it clearly.
**It didn't help.** At 1 s with a margin of 2 standard errors, the Search Bot scored **50.2% (45.4–55.1%)** against
the Value Bot in a final 400-Game Match on seeds 0–199 (201 wins to 199). The plain best mean scored 53.0% on the
same seeds. Box 3 stays unticked.

**The code:**
- `Searched.paired` keeps each Option's root result on each Sampled Position.
- `Searched.picked(margin)` keeps the likeliest Option unless another beats it by a mean paired difference over
  `margin` standard errors. Of those that do, it picks the best mean. With one Sampled Position there is no standard
  error, so only a margin of 0 switches.
- The new setting `margin` reaches it, as in `search?margin=2`.
- **Two new tests:** the rule on a hand-made search result with known differences, and that an endless margin
  picks as the Imitation Bot while still searching.
- **The default margin is 0 (Chosen by Claude):** 0 is the plain best mean the earlier Matches played, and nothing
  measured favours 2. The setting is kept so the experiment can be rerun.

**How often each margin keeps the likeliest Option** (`experiments/16/switches.py`, against the Value Bot on seeds
from 3,100,000; the rate is how often the pick is not the likeliest):

| Budget | Decisions searched | Sampled Positions per Decision | margin 0 | 1 | 2 | 3 |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 0.1 s (4 Games) | 400 | median 2; 24% have only 1 | 56.2% | 25.2% | 14.8% | 11.0% |
| 1 s (2 Games) | 173 | median 14 (quartiles 9–26) | 54.3% | 39.3% | 25.4% | 17.9% |

At 0.1 s the standard error rests on about 2 Sampled Positions, too few to mean much. So the rule was tried at the
default 1 s rather than in the cheap 0.1 s Matches proposed earlier (Chosen by Claude).

**The Matches** (`search?margin=2` at 1 s against `value`):

| Seeds | Games | Score | Note |
| --- | ---: | --- | --- |
| from 3,000,000 (pilot) | 200 | 56.5% (49.6–63.2%) | at margin 0, the first 100 of these Games scored 59.0% |
| 0–199 (final, `.cache/models/runs/match-16-search-1s-margin-2.txt`) | 400 | 50.2% (45.4–55.1%) | margin 0 scored 53.0% |

**How they were run:**
- **The pilot** ran as `search?margin=2`.
- **The final Match** ran as plain `search`, so its report's header doesn't show the margin. The default `MARGIN` was 2
  while it ran and was set back to 0 afterwards. To rerun it now, use `search?margin=2`.
- **Going on to the final Match** depended on the pilot scoring about 55% or more, a bar Claude set before the pilot.
  The pilot cleared it, but even it didn't beat margin 0.
- **Stopping early** once the leader is clear (the open point's second half) wasn't built. Each Decision's budget is
  its own, so stopping early would only shorten Matches; it wouldn't add strength.
- **The switch rates** are saved in `.cache/ticket-16/switches.txt`. Their Sampled Positions per Decision cover every
  Decision searched, the Draft and setup included. The README's "4–10 at a mid-Game Action" counts the Action phase
  alone.

**What this says:**
- Over 1,000 Games at 1 s on these two seed ranges, the Search Bot scores about 53% against the Value Bot, whichever
  rule picks.
- Keeping closer to the Imitation Model's picks costs as much as the Value Model's noise does.
- The bottleneck looks like the Value Model itself rather than how the search reads it.
- So the remaining open points are the ones that improve or cheapen the Value Model:
  - longer self-play with bigger gates;
  - training it on the Search Bot's own Games (expert iteration);
  - a smaller leaf model, to fit more Sampled Positions.

**Code review** (`/code-review` against 2e0a26a, one standards and one spec subagent, read-only).

Fixed:
- **The final Match's record:** it ran as `search` with the default margin at 2, not as `search?margin=2` as first
  written.
- **"The first 100 of these seeds"** now reads "Games": the sweep's 100 Games cover 50 seeds.
- **The 55% bar and the skipped early stop** are now recorded.
- **The switch rates** are now saved.
- **`Searched.add`** takes one Sampled Position's results, so the search and the test helper share one path.
- **Clearer names:** `clear` is now `beating` and `error` is `standard_error`.
- **The docstring's wording** is plainer.
- **The endless-margin test** also asserts that it searched.

Left as they are:
- **Each root result is kept twice,** in its Edge and in `paired`. Both are added in one place.
- **`paired` matches Options by their order in `options`,** as documented.
- **The `margin` setting is kept,** though its default is 0, so the experiment can be rerun.

The full suite passed (2,247 tests) before the fixes; the Search Bot, registry and fair-play tests pass after them.

**Laptop time:** about 1.5 hours: the switch rates for 4 minutes, the pilot for 29 minutes and the final Match for 59.

### 2026-11-23 — a better-calibrated Value Model; box 3 met (Claude)

**Box 3 is met.** With the new Value Model registered, the Search Bot (1 s) beat ticket 15's Value Bot (v006, kept as
`.cache/models/value-v006.pt`) in **57.0% (52.1–61.8%)** of a final 400-Game Match on seeds 0–199, 228 to 172
(`.cache/models/runs/match-16-search-1s-warm-all.txt`; Victory Points 93.2 – 90.6, 0 stalled).

**Decisions made with the user:** the route "a bigger warm start", and about 3 hours of laptop time. About 2.3 hours
were used: training 15 minutes, validation 4, the head to head 10, the pilot 28, the final Match 55, the Value Bot's
Match 6 and the full suite 3.

**What was found:**
- The warm start already used every Prelude Game (14,806 in training, about 4.5 passes). Games without Prelude add
  only 2,916.
- On the Prelude validation split's 77,802 positions (`uv run python -m ai.value.evaluate`,
  `.cache/ticket-16/validation.txt`), the earlier models were badly calibrated:

  | Model | Positions trained | Validation loss | Winner rated likelier |
  | --- | ---: | ---: | ---: |
  | v006 (ticket 15, registered) | 1.5M, then self-play | 1.06 | 71.0% |
  | v001 | 1.5M, then self-play | 1.11 | 71.3% |
  | v000 (ticket 15's warm start) | 1.5M, Prelude only | 0.569 | 75.0% |
  | every Game, 2.5M | 2.5M | 0.666 (overfit) | 74.5% |
  | **every Game, 800k (registered)** | 800k | **0.460** | **76.6%** |
  | every Game, 400k | 400k | 0.460 | 76.5% |

- So the warm start overfit at 1.5M positions, and self-play made the model overconfident (a loss over a coin's
  0.693). A likely reason search suffers more from that than the Value Bot does (not measured): search averages win
  chances over Sampled Positions and the other Player's drawn Options, while the Value Bot mostly ranks Options.

**Matches:**
- New model as a Value Bot vs v006, 400 Games on seeds from 20,000: 53.6% (48.7–58.5%)
  (`.cache/ticket-16/h2h-w-short-v006.txt`).
- Pilot: Search Bot on it vs the v006 Value Bot, 200 Games from seed 3,200,000: 58.0% (51.1–64.6%), above the 55% bar
  set beforehand (`.cache/ticket-16/pilot-search-w-short.txt`).
- Final: see above. The run is `.cache/models/value-runs/warm-all-short` (`--warm-games all --warm-positions 800000
  --validation-share 1 --rounds 0 --minutes 0.1`, which stops after the warm start); it was registered with
  `--register`. Its provenance names commit 49ff2e2 with `uncommitted_changes: true`: the only uncommitted file then was
  the untracked `experiments/16/model_files.py`, which training doesn't read, so the run repeats from 49ff2e2.
- **The registered Value Bot** (now this model) against the Imitation Bot, 400 Games on seeds 0–199:
  **60.5% (55.6–65.2%)**, 242 to 158 (`.cache/models/runs/match-15-value-warm-all.txt`), against v006's 57.0%. So the
  Value Bot rung still holds with it.

**Code** (commit 49ff2e2, test-first):
- `--warm-games all` adds samples from Games without Prelude; validation stays on Prelude Games.
- `ai/value/evaluate.py` is the new command.
- `validated` (in `ai/value/train.py` since the review) is shared by the loop and the command.
- `budgeted` moved to `ai/value/samples.py`.
- Three new tests: Games without Prelude give samples only when asked for; the loop's warm start learns from them and
  still validates on Prelude Games; the command measures each model on the same positions.
- Model-file Controllers for these Matches are in `experiments/16/model_files.py` (run with
  `PYTHONPATH=.:.scratch/phase-2-ai-opponent/experiments/16`).

**Chosen by Claude** (on the user's standing instruction to take the recommendation after the first batch):
- **The seams** were `recorded_samples`, the loop's command line and the new command.
- **800k positions:** 400k scored the same, and 2.5M overfit.
- **Registering on the pilot.** The head to head (53.6%) didn't clearly beat v006 as planned. But box 3 is about
  search, so the pilot was the gate.
- **The final Match's opponent** is ticket 15's Controller, the Value Bot on v006, not the newly registered `value`.

**Code review** (`/code-review` against 627b75c, one standards and one spec subagent, read-only).

Fixed:
- **Standards:**
  - `validated` lived in the command module, so the loop depended on a command. It is now in `train.py`, beside
    `measured`.
  - A README line over 120 columns.
  - `W` in `model_files.py` is now `WARM_ALL`.
- **Spec:**
  - The README and ticket 15 still described the registered Value Bot as v006 after self-play. The rows now name
    v006 where it played, and the Value Bot rung shows the new model's 60.5%.
  - The README's "doesn't yet win" sentence and its ticket count.
  - The Search Bot rung's figure is labelled as against ticket 15's Value Bot (v006).
  - The causal claim about search is marked as not measured.
  - The validation numbers are saved to a result file.
  - The provenance's uncommitted-changes flag is explained.

Left as they are:
- **`prelude_only` travels with `split`, `size`, `buffer`, `seed` and `keep`** (Data Clumps), and
  `--warm-games` is a string turned into a bool. A sampling-settings type would collect them, for a later change.
- **Two tests build a similar three-Game dataset.**
- **The Search Bot hasn't played the new Value Bot.** Box 3 names ticket 15's Controller.

**The full suite:** 2,262 tests passed in 2.7 minutes. Ruff is clean on the touched files at 120 columns.

**Open points:**
- **Self-play from this warm start** should first fix the overconfidence: many more Games a round, or a calibration
  check (`ai.value.evaluate`) as part of the gate.
- **The Awards flip rate** of the new Value Bot hasn't been measured (ticket 15's box 4 check).

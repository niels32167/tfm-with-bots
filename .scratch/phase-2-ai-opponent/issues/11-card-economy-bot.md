# 11 — Card Economy Bot

**What to build:** A Controller that compares Options by their Prices, and a way to fit those Prices. This is the first strong benchmark, and it's explainable: for any pick, it can say what it thought each Option was worth.

**Prices:**
- Start from the published values in the spec, and check them against Recorded Games before trusting them. For setup, tfmstats.com's rating change per Corporation, Prelude Card and starting-hand card, and its lift for Corporation and Prelude pairs, give starting values to check the same way. Its Award flip rates (how often the funder doesn't win an Award) are a starting point for whether funding pays. Win rates when a card is played or a Milestone claimed mostly show who was already ahead, so they aren't Prices.
- They depend on the Generations left, estimated from the Global Parameters and the pace of play, and held fixed while comparing a Decision's Options. Otherwise the bot refuses to terraform, as the first quick bot did.
- A Victory Point's Price rises through the Game towards what it costs by Standard Project. MegaCredits lose their use at the end.
- A card's Price covers its printed effects, the payback of its Production, its Victory Points and its Tags in context: Requirements in hand that it brings closer, and what it triggers on played cards.
- Include the opportunity cost of spending now, and what a card held in hand is worth when it can't be played yet.

**Fitting:** tune the weights by Matches, for example with CMA-ES on the fast engine, and check them against what Recorded Games predict. Prelude Cards and the base Corporations are priced too.

Stay in Python unless speed forces otherwise. If it does, move the evaluation into the engine, since rollouts need it (ADR 0007). Lookahead uses Sampled Positions (ADR 0013).

**Blocked by:** 05 — Prelude exit checks; 06 — Matches and fair Controllers; 07 — Sampled Positions

**Status:** ready-for-agent

- [x] Two copies never stall: 1,000 Games between them finish, with the report showing none stalled.
- [x] It wins at least 99% of a 400-Game Match against the Random Bot.
- [x] It wins a Match, with the interval above 50%, against the fair flat playout Controller from ticket 07 at a budget of a few seconds per Decision or less, or the gap is recorded and explained under Comments.
- [x] Its Games against itself are recorded under Comments, beside the spec's human benchmark: Generations (humans about 10.7 with Prelude), Victory Points (about 106–87) and card Victory Points (about 28).
- [x] Its setup choices are compared with Players': how often it chooses each Corporation and keeps each Prelude Card, against the dataset or tfmstats.com, with the largest differences explained under Comments.
- [x] It can explain a pick: the Prices of the top Options and why, in the dev panel or a command.
- [x] Unit tests on Prices read like play, such as "Production is worth less with fewer Generations left", "a science Tag is worth more with a science Requirement in hand", and "terraforming isn't penalised for ending the Game sooner".
- [x] It is selectable in the GUI.

## Comments

### 2026-11-17 — implemented (Claude)

Every box is ticked. `ai/prices.py` holds the Prices and their weights. `ai/card_economy.py` is the Card Economy
Bot (registered as `card_economy`). `ai/fit_prices.py` fits the weights by Matches, `ai/explain.py` explains a
pick, `ai/recorded_games/price_check.py` checks Prices against Recorded Games, and `tools/setup_choices.py`
compares setup choices. The Bot imports nothing from `tm_engine` and looks ahead only on Sampled Positions;
`tests/ai/test_fair_play.py` passes unchanged.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **The seams:** Prices in their own module (`ai/prices.py`), the Bot on top of them.
- **Fitting:** regress Prices on Recorded Games as a check, then a short CMA-ES by Matches (1–2 hours on the
  laptop).
- **Explaining:** a Bot tab in the dev panel and a command.

**Chosen by Claude, on the user's instruction to take the recommendation after the first batch:**
- **One step ahead, on one sample.** Each Option is picked on the same Sampled Position (one seed per Decision).
  The Bot's own follow-ups are answered quickly: a payment by what gives up least, a Tile by its bonuses and
  neighbours, anything else by a one-ply price. Then the position is priced: the Bot's worth less the other
  Player's, times `opponent`. Choosing a Corporation or Prelude Cards, drafting, buying and selling are priced from
  the cards' data instead.
- **The Generations left are estimated once per Decision** from the root Player View, a blend of the default pace
  and the pace seen so far, and held for every Option. So terraforming is not penalised for ending the Game sooner
  (`test_terraforming_isnt_penalised_for_ending_the_game_sooner`).
- **Passing and ending a Turn are priced 0** without a sample. After a Pass the sample can run on through the
  Production phase, and those gains are not passing's.
- **Cards drawn in a sample are priced at a typical card drawn,** not their own Price, so a lucky draw in one
  sample doesn't sway the pick.
- **Fitness** in the CMA-ES is the win rate against the starting weights plus the mean margin over 200, on fresh
  seeds per generation, each played both ways. The weights are searched as log-shares of their starting values,
  with upper bounds where a weight stops making sense (`UPPER`).
- **The budget** was 14 generations of 10 candidates and 100 Games each (about 80 minutes). The first run, at
  20 × 12 × 160, stopped when the laptop ran out of memory (see below).
- **The Bot tab hides the reasons** unless the viewer is in the full view or it is their own Decision, so the
  dev panel doesn't show a human what the Bot thinks of cards they can't see.
- **tfmstats.com's tables weren't used.** The spec offers its rating changes per card, its Corporation and
  Prelude lifts and its Award flip rates as starting values. The setup prices come instead from the cards'
  own effects through the same Prices as every other Decision, and box 5 compares the outcome with the
  dataset, as the box allows. Funding an Award is priced from the count gap and `award_spread`, not from flip
  rates. The Imitation Model will learn setup from the dataset directly.
- **The Recorded-Games regression is a check only.** Nothing from it or from tfmstats.com feeds the fit. The
  only change it led to was raising the starting price of a card in hand (from 4 to 6 MegaCredits), which the
  fit then moved on.

**Found while building:**
- **Two copies stalled** (Generation 100+, Oceans unplaced, 600 MegaCredits kept). Diagnosed with a stall
  replay: the Bot priced every MegaCredit kept at more than 1, so an Aquifer for 18 lost it 3.1 MegaCredits. Money
  beyond what the worthwhile cards in hand cost is now priced at what the best Standard Project makes of it
  (`test_megacredits_beyond_what_the_hand_needs_are_worth_what_standard_projects_make_of_them`). A second bug made
  the same mistake on samples: the hand's needs were looked up by board identity, which a sample never matched.
  They are keyed by Player now.
- **Setup prices** missed several things, found by comparing with Players' choices: cards revealed into the hand,
  Excentric Sponsor's discount (capped now at a typical card's cost), Corporations' first actions and triggers
  that live in the engine's code (Valley Trust, Vitor, Robinson Industries), and a City's Greeneries to come.
  Each has a test.
- **The laptop ran out of memory** when `tools/setup_choices.py` loaded the whole dataset while the fit ran.
  It now streams each Game slimmed to its results and setup (`results_and_setups`), peaking at 0.3 GB.

**The fit.** The search's mean won 60% of its 100 Games in generation 1 and 68% (by +10.0 points) in
generation 14. On 1,000 fresh Games (seeds 5000 to 5499, each played both ways), the fitted weights won **63.3%
(60.3–66.2%)** against the starting ones, 111.5–102.5 Victory Points. They are now the defaults, each with its
starting value in a comment. The largest moves: a card drawn 6 → 9.7 MegaCredits, the share of a card's
worth that holding it is worth 0.8 → 0.56, the City bonus 6.5 → 9.7, a Milestone's bonus 6 → 9.5, the last
Generation's Victory Point 10 → 13.3, the opponent's weight 1 → 1.38, kept steel and titanium 0.7 → 0.37 of
what they pay, and plants and heat kept 0.85 → 0.6 of what they make. `discount` (0.97) and `end_megacredit`
(1.0) stopped at their bounds. With `end_megacredit` at 1, money kept for the worthwhile cards in hand keeps
its full price in the last Generation, as those cards can still be played. MegaCredits lose their use at the
end through the surplus price: money no card needs is worth only what Standard Projects make of it, about
0.55 each in the last Generation. `test_megacredits_lose_their_use_at_the_end` says so.

**Box 1 — two copies never stall.** `uv run python -m ai.match card_economy card_economy --games 1000`:
1,000 finished, **0 stalled**, 0 failed. Win rates 49.9% and 50.1%.

**Box 2 — against the Random Bot.** `uv run python -m ai.match card_economy random_bot --games 400 --threshold 0.99`:
**400 wins of 400, 100% (99.0–100%)**, 157.9–49.3 Victory Points, 15.1 Generations. Threshold met.

**Box 3 — against Flat Playout.** `uv run python -m ai.match card_economy flat_playout --games 1000 --first-seed 1000 --threshold 0.5`:
**96.4% (95.0–97.3%)**, 963 wins, 1 draw, 36 losses; 114.0–74.6 Victory Points, card Victory Points 18.4–5.8,
13.3 Generations. Threshold met. Its picks take **3.1 ms on average, 2.1 ms median, 18 ms at the 99th
percentile and 31 ms at most** (10,057 picks over 20 self-play Games, one process), far under a few seconds.
On the way: 48% at first, 76.5% after the stall fixes, 93.5% after the setup fixes, 96.5% after the City fix,
all on 200 Games.

**The gap at a larger budget, recorded as box 3 allows.** That Match gives Flat Playout its default of 20
playouts per Option, about 14 ms per pick. The code review asked what happens when Flat Playout also gets a
budget of seconds, so the Bot played it with more playouts (a scratchpad script with `run_match` makers):

| Flat Playout's playouts per Option | its time per pick | Games | Card Economy Bot's win rate | Victory Points | Terraform Rating |
| ---: | --- | ---: | --- | --- | --- |
| 20 (default) | about 14 ms | 1,000 | **96.4%** (95.0–97.3%) | 114.0–74.6 | 45.6–44.5 |
| 200 | about 0.14 s | 200 | **65.2%** (58.4–71.5%) | 98.9–91.8 | 42.0–47.9 |
| 1,000 | 0.70 s mean, 7.4 s max | 100 | **29.5%** (21.5–39.1%) | 93.0–103.7 | 40.6–48.9 |

So with a budget of seconds for both, **Flat Playout wins**. The Card Economy Bot spends 3 ms and can't
use more time: it looks one step ahead on one Sampled Position, with Prices fitted only against itself.
Given time, Flat Playout's random playouts see what one step can't. They see how fast the Game will end,
so it terraforms harder (Terraform Rating 48.9 against 40.6) and ends Games the Bot's Prices assume run
longer. Its random play is averaged over 1,000 playouts, so its picks no longer suffer from that randomness.
Neither Bot sees hidden cards. The ladder still holds at the budgets the README measures rungs at
(the rung below at its default). Using time well is the job of search at play time (ticket 16), which
can use these Prices to value positions in place of random playouts.


**Box 4 — Games against itself,** the same 1,000 Games:

| | Card Economy Bot vs itself | Humans with Prelude (spec) |
| --- | ---: | ---: |
| Mean Generations | 13.6 (median 14) | 10.7 |
| Mean Victory Points, winner–loser | 117.6–97.5 | 106–87 |
| Card Victory Points of the better Player | 20.1 | 28 |

Per Player: Terraform Rating 46.7, Greeneries 9.6 points, Cities 18.0 points, Milestones 7.5, Awards 7.5.
Its Games run about 3 Generations longer than humans'. So it scores more from the board (the longer Game adds
Terraform Rating, Greeneries and the City points next to them) and less from cards. It looks one step ahead,
so it doesn't plan a hand around a card's Victory Points or race the Global Parameters to end a Game it is
winning. Closing that gap is for the later rungs.

**Box 5 — setup choices,** `uv run python -m tools.setup_choices --setups 4000`: the Bot answers both Players'
setup in 4,000 Games (about 930 deals per card), against 31,942 Prelude Games in the dataset. Largest
differences:

| Corporation | Players | Bot | | Prelude Card | Players | Bot |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| United Nations Mars Initiative | 21% | 82% | | Supply Drop | 59% | 0% |
| Interplanetary Cinematics | 48% | 5% | | Great Aquifer | 80% | 23% |
| EcoLine | 63% | 23% | | Metal-Rich Asteroid | 58% | 3% |
| Vitor | 64% | 100% | | Biolabs | 51% | 100% |
| PhoboLog | 34% | 0% | | Galilean Mining | 54% | 95% |
| Mining Guild | 53% | 20% | | Orbital Construction Yard | 60% | 20% |
| Helion | 42% | 12% | | Nitrogen Shipment | 19% | 54% |
| Inventrix | 41% | 69% | | Power Generation | 40% | 74% |

**Why, tested by ablation.** The Bot's setup was played again on 1,000 other Games with one fitted weight put
back to its starting value at a time (a script in the session's scratchpad, not kept):

| Bot's rate | fitted | kept metal 0.7 | discount 0.9 | card 6, cards per Generation 2.5 | conversion 0.85 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Orbital Construction Yard | 21% | **46%** | 14% | 25% | 19% |
| Supplier | 16% | **27%** | 12% | 20% | 11% |
| Interplanetary Cinematics | 8% | **20%** | 17% | 8% | 8% |
| Metal-Rich Asteroid | 4% | **11%** | 3% | 4% | 4% |
| Galilean Mining | 92% | 89% | **53%** | 94% | 92% |
| Power Generation | 76% | 72% | **60%** | 87% | 76% |
| United Nations Mars Initiative | 80% | 80% | **45%** | 100% | 80% |
| Research Network | 97% | 97% | 100% | **49%** | 97% |
| Point Luna | 93% | 93% | 89% | **62%** | 93% |
| Vitor | 100% | 100% | 100% | **80%** | 100% |
| EcoLine | 29% | 25% | 36% | **62%** | **41%** |
| PhoboLog | 0% | 0% | 0% | 0% | 0% |
| Supply Drop | 0% | 4% | 0% | 0% | 0% |
| Great Aquifer | 21% | 14% | 29% | 24% | 21% |
| Biolabs | 100% | 100% | 100% | 98% | 100% |
| Inventrix | 68% | 68% | 94% | 70% | 68% |
| Helion | 13% | 8% | 13% | 13% | 13% |

- **Metal kept is cheap to it** (fitted 0.37 of what it pays, from 0.7): in its own Games a stock of metal often
  finds no card to pay for. Putting it back roughly doubles Orbital Construction Yard, Supplier, Interplanetary
  Cinematics and Metal-Rich Asteroid, though all stay below Players' rates.
- **Production pays more with its discount of 0.97** (from 0.9) over Games of 13–14 Generations. At 0.9,
  Galilean Mining falls from 92% to 53% (Players 54%), Power Generation to 60%, and United Nations Mars
  Initiative, whose action pays every Generation, from 80% to 45%.
- **Cards drawn and Triggers on cards played are priced high** (a card drawn 9.7, from 6; cards played per
  Generation 5.9, from 2.5). Put back, Research Network falls from 97% to 49% (Players 64%), Point Luna to 62%
  and Vitor to 80%. EcoLine rises to 62%, Players' 63%: the high card prices crowd it out. Plants kept at the
  starting conversion of 0.85 also raise it, to 41%.
- **Not from the fit:** PhoboLog (0%, Players 34%), Supply Drop (0%, 59%), Great Aquifer (21%, 80%), Biolabs
  (100%, 51%), Inventrix (68%, 41%) and Helion (13%, 42%) barely move under any one weight. With every
  weight at its starting value they are 0%, 23%, 13%, 100%, 100% and 8%: the gaps came before the fit,
  which only pushed Supply Drop further down. The Bot prices a stock of Resources or two Oceans in Generation 1 by what they are worth
  as they stand. Players use them for tempo: titanium for a big space card at once, Oceans that bring the
  placement bonuses and the end nearer. One step ahead doesn't see that. Biolabs and Inventrix bring 3 cards
  each, which the Bot prices high at any of these weights.

These are the Bot's own prices, fitted by playing itself, not mistakes against the rules. Where Players'
choices differ, the Imitation Model (tickets 13–14) learns them from Recorded Games.

**Check against Recorded Games** (`uv run python -m ai.recorded_games.price_check`, lower rating 400+): the
final Victory Point margin regressed on position differences, by Generations left. Below, each coefficient is
divided by a kept MegaCredit's, giving MegaCredits per unit, humans / the Bot. The regression shows association,
not cause: science Tags and cards in hand mark Players who were winning anyway.

| Generations left | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- |
| Terraform Rating | 8.8 / 12.1 | 7.2 / 11.0 | 7.4 / 10.5 | 7.3 / 9.9 | 6.9 / 9.7 |
| MegaCredit Production | 1.6 / 1.0 | 1.6 / 1.9 | 2.0 / 2.8 | 2.5 / 3.6 | 3.0 / 4.5 |
| steel Production | 1.5 / 1.8 | 2.3 / 3.5 | 4.0 / 5.2 | 5.2 / 6.6 | 5.8 / 8.3 |
| plants Production | 7.5 / 3.0 | 5.8 / 4.3 | 6.9 / 5.7 | 6.6 / 6.8 | 7.4 / 8.2 |
| energy Production | -0.1 / 1.2 | 0.3 / 2.4 | 1.1 / 3.6 | 1.7 / 4.6 | 2.4 / 5.7 |
| a card in hand | 3.8 / 1.2 | 4.6 / 2.4 | 5.7 / 3.6 | 6.3 / 4.8 | 6.2 / 5.3 |
| a science Tag | 7.8 / 0.3 | 8.1 / 0.6 | 9.0 / 0.9 | 9.6 / 1.2 | 10.7 / 1.5 |

The Bot prices Production and Terraform Rating above humans, consistent with its longer Games. Energy
Production stands out, at 2–3 times humans'. Before the fit, Terraform Rating agreed (7.5–8.5 both ways), and
a card in hand was 2.5 times too cheap, which led to the higher starting price.

**Box 6 — explaining a pick.** `uv run python -m ai.explain <replay file> --step N` prints the top Options with
their Prices and the reasons (the parts of the worth that changed). The dev panel's Bot tab shows the same
for any step of the Game. Checked in the browser pane: a Game against the Card Economy Bot, full view on,
Bot tab at step 5 showed "Buy Commercial District (3 MegaCredits) ← picked +0.8", with Card in hand +3.9 and
MegaCredits −3.1 as reasons; no console errors. `tests/server/test_dev_panel.py` and `tests/ai/test_explain.py`
cover both.

**Box 7 — Prices tests.** `tests/ai/test_prices.py` (12 tests) and `tests/ai/test_card_economy.py` read like play:
"Production is worth less with fewer Generations left", "a Victory Point is worth more near the end, up to what
a Standard Project charges", "MegaCredits lose their use at the end", "a science Tag is worth more with a
science Requirement in hand", "terraforming isn't penalised for ending the Game sooner", "a card that pays back
is worth more in hand early than late", and so on.

**Box 8 — selectable in the GUI.** The setup screen lists "Card Economy Bot" for each Player (from
`ai/controllers.py`); checked in the browser pane.

**Checks:** `timeout 1800 uv run pytest` 2,160 passed; ruff format and check on the touched files;
`npm --prefix gui run build` passed. The engine didn't change. Matches ran on mains in the "performance"
profile, one at a time.

**The code review** (`/code-review` against 2f05d32, Standards and Spec reviewed apart) found, and I fixed:
- **CONTEXT.md avoids "worth" in code and keeps "value" for the Value Model.** `Worth` is now `PricedPosition`,
  `Prices.worth` is `Prices.position`, `persisting_worth` is `persisting_price`, `cube_value` is `cube_price`, and
  an Option's `value` is its `price` (in the dev view's JSON and the GUI too).
- **The claim that every number in `ai/prices.py` is a fitted weight** wasn't true. The module now says the
  rules' own numbers stay inline, and names the rough guesses left out of the fit (`TAG_CHANCE`,
  `HARM_SHARE`, the Trigger rates and others).
- **The MegaCredits-at-the-end test was loose** after the fit. It now checks that money no card needs is worth
  less than 0.75 each in the last Generation.
- **Box 5's reasons were argued, not measured.** They are now tested by the ablation above, which refuted
  two of them as first written.
- **Flat Playout ran only at its default budget.** See the gap above.
- **Smaller fixes:** a misused `_` in `tools/setup_choices.py`, unclear names (`when`, `OPEN`, `rows_`) and a
  missing class docstring. The guide now says a check may move a starting weight but is never a fitting
  target.

Left as they are, by judgement:
- `placed()` in the Bot repeats part of `Prices.tiles` as a quick heuristic for choosing an Area.
- `trigger_rate` and `triggered_by` branch on the same Trigger kinds.
- `server_random` lives in `ai/explain.py`, which the server imports, so that both make the same random
  numbers.
- `ruff format` reformatted the whole of `tests/server/test_dev_panel.py`, which wasn't formatted at 120
  columns before. It also unquoted two return annotations in `server/session.py` for `ruff check`.

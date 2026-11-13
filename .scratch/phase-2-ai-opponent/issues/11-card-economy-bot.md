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

- [ ] Two copies never stall: 1,000 Games between them finish, with the report showing none stalled.
- [ ] It wins at least 99% of a 400-Game Match against the Random Bot.
- [ ] It wins a Match, with the interval above 50%, against the fair flat playout Controller from ticket 07 at a budget of a few seconds per Decision or less, or the gap is recorded and explained under Comments.
- [ ] Its Games against itself are recorded under Comments, beside the spec's human benchmark: Generations (humans about 10.7 with Prelude), Victory Points (about 106–87) and card Victory Points (about 28).
- [ ] Its setup choices are compared with Players': how often it chooses each Corporation and keeps each Prelude Card, against the dataset or tfmstats.com, with the largest differences explained under Comments.
- [ ] It can explain a pick: the Prices of the top Options and why, in the dev panel or a command.
- [ ] Unit tests on Prices read like play, such as "Production is worth less with fewer Generations left", "a science Tag is worth more with a science Requirement in hand", and "terraforming isn't penalised for ending the Game sooner".
- [ ] It is selectable in the GUI.

## Comments

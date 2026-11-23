# Learn from Recorded Games first, then self-play

The AI starts by learning to predict what strong Players do in Recorded Games, and improves past them by self-play. This narrows the spec's original "train by self-play" (ADR 0004 still holds: self-play is where speed pays off).

Pure self-play has to rediscover from nothing what humans already know. A quick test showed how far bots are from them: the best took 15 Generations and scored 8 card Victory Points, where Players in Recorded Games without Prelude take about 12 Generations and the better one scores about 28. With only 12 GB of RAM and a 6 GB laptop GPU, starting from competent play is worth the cost of parsing logs. Imitation alone can't beat the Players it copies, so self-play still has to take over.

**What the data allows.** Recorded Games name every Player's dealt, drafted and drawn cards, so:
- the model must only ever see what that Player could see: the opponent's hand and the deck are hidden before training, and a test checks it;
- Draft and buy Decisions are usable straight away, while Action-phase imitation first needs each Player's hand rebuilt.

**Terms of use.** The scraper names no licence: it says educational and research use, and asks users to respect Board Game Arena's terms and player privacy. So the logs and anything derived from them stay out of git, player names are dropped from what we derive, and nothing is published. This project is private (ADR 0003); a public release would have to revisit this. The models the bots play with are published in the hosted Space since 2026-11-23 (ADR 0014); the rest still is not.

# Add Prelude to the engine before training the AI

This revises ADR 0003, which left Prelude out of v1. We add it before any training, as a setting of each Game like the Draft, and the AI trains and plays with it on.

Nearly all the human play we can learn from uses it. Among 2-player Tharsis Games with Corporate Era and the Draft, the Board Game Arena logs hold 51,422 with Prelude and 7,622 without, and at the top level (both Players rated 600 or more, finished Games) about 1,400 against 42. It also shortens Games, from 12.4 Generations to 10.7 on average, which speeds up training.

The cost is 47 more cards (35 Prelude Cards, 5 Corporations, 7 Project Cards), a new setup step and another round of fuzzing and play-testing, all before AI work starts. Only base Prelude is added: the card list's promo cards (Corporate Archives, Double Down, Merger, New Partner, Head Start) never appear in these Games.

Games and Replays without Prelude keep working unchanged, so the rules tests and old Replays stay valid. A later AI for Games without Prelude is possible, but isn't a goal.

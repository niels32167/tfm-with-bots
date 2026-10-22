# Engine speed: 1,000 Games per second and cheap state copies

The engine must play at least 1,000 complete 2-player Games between Random Bots per second across the development machine's 16 cores, and copy a game state in microseconds. A 2-player Game with Draft is roughly 800 Decisions.

Self-play training needs millions of Games on modest hardware (12 GB RAM, an RTX 3050 6 GB laptop GPU), and cheap copies keep a tree-search AI possible later. This rules out a pure-Python engine, which we estimate would manage only 200–400 Games per second.

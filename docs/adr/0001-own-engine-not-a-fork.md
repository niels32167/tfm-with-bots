# Own engine; the open-source game is only a rules reference

We write our own game engine instead of forking the open-source Terraforming Mars game (terraforming-mars/terraforming-mars, TypeScript, GPL-3.0). That game is a web server built around a large web of linked objects. It isn't designed to copy game states cheaply or run millions of moves, which self-play training and later tree search both need.

It stays useful as a reference. When a rule is unclear, the order of authority is: the official rulebook, then the official FryxGames FAQ and corrections, then the open-source game's behaviour as tiebreaker. Each such judgment call is written down in `docs/rules-notes.md`. No code is copied from it.

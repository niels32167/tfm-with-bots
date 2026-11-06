# 06 — Matches and fair Controllers

**What to build:** The new `ai/` package with the Controller seam, and one command that plays a Match. The Random Bot becomes the first Controller using the seam. Every later rung is judged by this tool, so it comes first.

**The seam:** a Controller is given a read-only handle and returns an Option's index. The handle offers the Player View and the Decision, and Sampled Positions once ticket 07 adds them. It never gives access to the Game (ADR 0013).

**A Match:** two Controllers play N seeds, each Controller taking each Player on every seed. Each Game runs in its own process on all cores, and failures are saved as Replays.

**In the GUI:** the setup screen lists registered Controllers for each Player, as well as human and Random Bot, and the server asks the Controller for its pick. A slow Controller must not freeze the server's event loop.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] `uv run python -m ai.match <a> <b> --games N` reports each Controller's win rate with a 95% interval, mean Victory Points, Generations, card Victory Points and Terraform Rating, and which Player won more often.
- [ ] It exits with a chosen status when a threshold is missed, so that a ladder step can be checked by a command.
- [ ] A guard ends a Game that doesn't finish within a pick limit, and the report counts these as stalled.
- [ ] The same seeds and Controllers give the same results, for Controllers that use only their given random source.
- [ ] Test: nothing reachable from the handle gives the Game, its copies, or another Player's hidden cards.
- [ ] The first Match is recorded under Comments: Random Bot against itself, as a check that the tool shows about 50% (and how far first player and Player order shift that).
- [ ] The GUI can play a Game with a registered Controller as a Player, at a usable speed, and undo and Replays still work.

## Comments

# 16 — Search at play time

**What to build:** A Controller that searches during play: it builds a tree over Sampled Positions, using the model to narrow Options and the Value Model to judge positions, within a time budget per Decision.

This is where spare seconds become strength. Decide:
- how samples are shared across the tree, or whether each sample gets its own (information set MCTS, or one tree per Sampled Position);
- how to treat the opponent's Decisions and chance, such as card draws;
- how to spend the budget, since many Decisions don't need much of it.

The quick test showed that playout counts matter a lot: going from 5 to 100 per Option took a bot from 3% to 84% against the same opponent. But random playouts undervalue engine building, so check how much rollouts and the Value Model each contribute.

**Blocked by:** 15 — Self-play and the Value Model

**Status:** ready-for-agent

- [ ] The time budget is a setting, and the Controller keeps to it in the GUI, with the default chosen so that a Game is pleasant to play.
- [ ] Strength against budget is recorded under Comments, for example 0.1, 1 and 5 seconds per Decision, against the Controller from ticket 15.
- [ ] It wins a Match against the Controller from ticket 15, with the interval above 50%, at the default budget.
- [ ] Test: it plays only through the fair handle, and its picks are equal for equal Player Views given the same seed.
- [ ] It is selectable in the GUI.

## Comments

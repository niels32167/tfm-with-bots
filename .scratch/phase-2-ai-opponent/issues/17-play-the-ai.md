# 17 — Play the AI

**What to do:** Decide whether phase 2 is finished, by playing the final Controller in the GUI. The goal is that it beats me in most Games with no peeking at hidden cards.

Before playing, fix how many Games count and what result counts, so that the bar can't move afterwards. Ten Games with at least six AI wins is the suggested start, and I choose the final number. The seed of each Game is fixed in advance, and I play as first player in half of them. Use Prelude, Draft and 2 Players, as the AI trained.

If it falls short, look at what beat it (the Replays and its explanations will show where it plays badly) and go back down the ladder. If it gets there, playing further is optional.

**Blocked by:** 16 — Search at play time

**Status:** ready-for-human

- [ ] The number of Games and the winning bar are written here before the first Game.
- [ ] Each Game's Replay file is kept and named under Comments, with the result, seed and my notes.
- [ ] Any rule bug gets its own ticket with a Replay and a regression test, and the Game is replayed if it affected the result.
- [ ] I note where the AI played strangely, even in Games it won.
- [ ] The result is recorded, and the README and project status are updated.

## Comments

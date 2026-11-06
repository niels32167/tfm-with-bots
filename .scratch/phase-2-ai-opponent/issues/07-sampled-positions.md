# 07 — Sampled Positions

**What to build:** An engine operation that makes a Sampled Position for a Player at any Decision, exposed through the Python engine module and through the Controller handle.

It deals the cards that Player can't see at random: the deck and other Players' hidden cards, including cards under way in Draft, buying or Prelude setup. It uses only what the Player's own Player View holds, including what they passed in the Draft. Hand sizes and deck size stay right, and all Decisions still in progress stay answerable.

Decide with care what happens to a Decision belonging to another Player while the sample is made, since its Options depend on cards that are now different. A sample may need to start from the last point where the Decision is the Player's own.

This must be fast, because search calls it thousands of times per Decision. Aim to stay in the microseconds, like a copy (ADR 0004).

**Blocked by:** 02 — The Prelude setting and setup; 06 — Matches and fair Controllers

**Status:** ready-for-agent

- [ ] Test: two Games that differ only in hidden cards, with equal Player Views, give equal Sampled Positions for the same seed. This is the proof of fairness, and it covers every Decision kind reachable in a fuzz run.
- [ ] Test: a Sampled Position's Player View for that Player equals the real one.
- [ ] Test: card count is conserved, no card appears twice, and cards the Player passed in the Draft stay with the Player they went to unless played or otherwise accounted for.
- [ ] Fuzzed: a Sampled Position taken at any Decision can be played to the end with `play_randomly`, without error, over a large run.
- [ ] Cards known to be with a specific Player, such as ones they drew through a public effect, are handled, or the limits are listed in the rules notes with why they are acceptable.
- [ ] The benchmark reports the time per Sampled Position.
- [ ] A flat playout Controller using Sampled Positions runs a Match against the cheating version in `experiments/bots_experiment.py`, and the cost of playing fair is recorded under Comments.

## Comments

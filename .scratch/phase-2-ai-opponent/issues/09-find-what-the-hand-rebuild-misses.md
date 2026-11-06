# 09 — Find what the hand rebuild misses

**What to answer:** Can each Player's hand be rebuilt accurately at every Decision in a Recorded Game, and what does it take?

`experiments/logs_hands2.py` finds 99.5% of played cards in the rebuilt hand without Prelude (98.6% with), but the hand runs about 2 cards too large, and matches the `Hand Counter` tracker at only about 48% of checks after a card is played. In one Game traced by hand it was exact every time the counter refreshed, so the error is uneven and something specific is being missed.

Start by finding Games where the rebuild drifts, and read those moves. Suspects to check, none of them confirmed: Sell Patents wording, discard effects, Research wording in other scraper versions, "cancels their move" lines, the Prelude cases behind that lower 98.6%, and how stale the `Hand Counter` is, since it isn't a perfect reference either.

The answer decides how much Action-phase imitation can use. Some hidden removals may not be named at all, in which case the honest result is a hand with some uncertainty, and that may be good enough.

**Blocked by:** 08 — Recorded Game importer

**Status:** ready-for-agent

- [ ] The cause or causes of the drift are found and recorded under Comments, with example Games by table id.
- [ ] A rebuild on at least 3,000 Games reports: played cards found, hand size against a reference that was shown to be fresh, and the share of Games with every check exact.
- [ ] The result says which Games can be trusted and how to recognise them, and how many Games of each kind that leaves.
- [ ] The accuracy needed is decided, with reasons, and tickets 10 and 14 are updated to match.

## Comments

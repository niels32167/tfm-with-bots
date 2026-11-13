# 10 — Recorded Games in the engine

**What to build:** Replay Recorded Games through the engine: the cards dealt and drawn taken from the log, and each move matched to one of the Options offered. This gives two things:

1. **Action-phase training data.** Each Decision then has the engine's own Options and Player View, the same inputs a trained Controller sees in play, with the Player's real pick marked.
2. **A test of the rules on real play.** Where the engine refuses a move or disagrees about the result, either we have a bug or Board Game Arena has its own ruling.

It needs a way to start a Game with a chosen deal and draw order; find the smallest change to the engine or Scenario that allows it, since a Scenario currently starts in the Action phase. Compare trackers after each move, and stop that Game at its first difference, so that one difference doesn't cascade.

Expect many differences at first, mostly from parsing. Group them by cause and work down the largest groups. Stop when what remains is rare or isn't worth chasing, and record the decision.

**From ticket 09:**
- **Hands.** Take them from `ai.recorded_games.hands.HandReader` with `resync=True`. Replay first the 42,431 "named" Games, whose versions name both Players' cards; ticket 09's Comments say how to recognise them.
- **Sold cards.** Sell Patents and Mars University discards never name their cards. Choose them in hindsight from the named cards in hand that the Player never plays later. Any such choice replays the same; it is possible for 99% of Players.
- **Cards that entered unnamed** take their names from their plays.
- **Parser differences, not engine bugs:** a play `HandReader` finds "missing" (0.57%), a Hand Counter mismatch at a fresh check, or an `unread` line (a renamed account, 710 Games).

**Blocked by:** 05 — Prelude exit checks; 09 — Find what the hand rebuild misses

**Status:** ready-for-agent

- [ ] One command replays a sample or all suitable Games on all cores, and reports the share that replay fully, how far the others get, and differences grouped by cause.
- [ ] Each difference group is called parser, engine bug, or Board Game Arena's ruling. Engine bugs get a regression test and the usual rules note; rulings get a rules note saying why the rulebook stands.
- [ ] The share of Games replayed fully, and how many that gives at each rating, is recorded under Comments. A Game that replays partly can still give the Decisions before its first difference, and the dataset says so.
- [ ] The dataset gains Action-phase Decisions with Options and the pick, from the importer's format (ticket 08).
- [ ] Test on small hand-written Recorded Games, including one with a known difference. These tests need no archive.

## Comments

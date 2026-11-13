# 14 — Imitation Model for all Decisions

**What to build:** Extend the Imitation Model to every Decision, using the Action-phase data from ticket 10. Payment, Area and target Decisions are all Options like any other (ADR 0002).

Consider how much to learn at each kind of Decision. Payment has up to 166 Options, though few choices matter. A model may be poor at rare Decision kinds, so check that it still does something sensible there.

Humans also make Decisions in ways the engine's chain may split differently, so ticket 10 decides how those map onto Options.

**Blocked by:** 10 — Recorded Games in the engine; 12 — Position encoding; 13 — Imitation Model for Draft and buy

**Status:** ready-for-agent

- [ ] On held-out Games, it predicts picks better than a random pick and the Card Economy Bot, reported by Decision kind, Generation and rating.
- [ ] A Controller using only this model plays complete Games with none stalled.
- [ ] It beats the Controller from ticket 13 in a Match with the interval above 50%.
- [ ] Its Games against itself are recorded beside the human benchmark: Generations, Victory Points and card Victory Points, and which Milestones it claims and Awards it funds, in which Generation, and how often it loses an Award it funded (tfmstats.com's flip rate). This is the first check that it plays like the Players it learned from.
- [ ] It is selectable in the GUI, and a pick takes well under a second.

## Comments

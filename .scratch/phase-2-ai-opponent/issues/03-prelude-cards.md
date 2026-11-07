# 03 — The Prelude Cards

**What to build:** All 35 Prelude Cards, working as printed. Simple effects go in the card's effect data; triggers, ongoing effects and unusual cards get Rust code (ADR 0009).

**Blocked by:** 02 — The Prelude setting and setup

**Status:** ready-for-agent

- [ ] Every Prelude Card has at least one scenario test through the Python engine module, and the coverage check counts them.
- [ ] Each card's own "can't pay" or "can't carry out" cases are tested.
- [ ] Rules calls are in the rules notes.
- [ ] Each card is playable in the GUI, and the short fuzz run stays clean with them in play.

## Comments

### 2026-11-06 — from ticket 01 (Claude)

The coverage check counts a card once it has `"effects"`, so each card needs `tests/cards/test_<id>.py` from then on. Excentric Sponsor is spelled as printed (`excentric_sponsor`). The wild Tag isn't in `Tag::COUNTED` yet. See ticket 01's Comments.

### 2026-11-07 — from ticket 02 (Claude)

26 Prelude Cards already have effect data and tests. 9 are left: Business Empire, Galilean Mining, Huge Asteroid and Aquifer Turbines ("Pay X M€": decide on Helion's heat and on a Player who can't pay, see "A Prelude Card that can't be played" in the rules notes), Acquired Space Agency and Experimental Forest (reveal until found), Ecology Experts, Excentric Sponsor, and Research Network (the wild Tag). Only Prelude Cards with effect data are dealt, so each one added changes what a Game with Prelude deals. A Scenario plays a Prelude Card with `player(prelude_cards=[...])` and `prelude=True`. See ticket 02's Comments.

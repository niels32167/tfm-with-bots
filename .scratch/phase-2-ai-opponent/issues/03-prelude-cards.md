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

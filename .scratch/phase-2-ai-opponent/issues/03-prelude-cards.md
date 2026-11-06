# 03 — The Prelude Cards

**What to build:** All 35 Prelude Cards, working as printed. Simple effects go in the card's effect data; triggers, ongoing effects and unusual cards get Rust code (ADR 0009).

**Blocked by:** 02 — The Prelude setting and setup

**Status:** ready-for-agent

- [ ] Every Prelude Card has at least one scenario test through the Python engine module, and the coverage check counts them.
- [ ] Each card's own "can't pay" or "can't carry out" cases are tested.
- [ ] Rules calls are in the rules notes.
- [ ] Each card is playable in the GUI, and the short fuzz run stays clean with them in play.

## Comments

# 02 — The Prelude setting and setup

**What to build:** A Prelude setting for each Game, off by default for now, with the setup step it adds: Prelude Cards dealt, chosen and played. A few simple Prelude Cards and the 7 Project Cards' place in the deck land here, enough to play a whole Game with Prelude.

Research the rules first, in the usual order of authority (ADR 0001), and record each call in the rules notes. At least these need settling: how many are dealt and kept, when they are played and in what order, what happens when a Player can't pay for or carry out a Prelude Card, how it interacts with a Corporation's first action, and whether they count as cards played or Tags for other cards' effects. Recorded Games show 4 dealt per Player. Board Game Arena's behaviour can be checked against them, but doesn't outrank the rulebook.

**Blocked by:** 01 — Prelude cards in the catalog

**Status:** ready-for-agent

- [ ] `Game` takes a `prelude` setting; it goes into Replays and Scenarios, and old Replays load as without Prelude.
- [ ] Setup deals Prelude Cards and takes each choice through Decisions, hidden from other Players until the rules reveal them; the Player View test covers this.
- [ ] The deck includes Prelude's Project Cards only in Games with Prelude.
- [ ] The setup screen has a Prelude switch, and the GUI shows Prelude Cards while choosing and once played.
- [ ] At least three Prelude Cards work end to end, each with a scenario test.
- [ ] The rules notes hold every call made.
- [ ] The short fuzz run also covers Prelude Games, with invariants updated (card count conserved, and so on).

## Comments

### 2026-11-06 — from ticket 01 (Claude)

Ticket 01's Comments list what this ticket must change: the deck's size and range, the `card >= PROJECT_CARDS` checks in `game.rs`, the base-box filters in `tests/helpers.py` and `StateEditor.tsx`, and `find_project_card`. A card without `"effects"` can't be played, so any Prelude card dealt here needs effect data and a scenario test.

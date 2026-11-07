# 04 — Prelude's Corporations and Project Cards

**What to build:** Prelude's 5 Corporations (Cheung Shing Mars, Point Luna, Robinson Industries, Valley Trust, Vitor) and 7 Project Cards (House Printing, Lava Tube Settlement, Martian Survey, Psychrophiles, Research Coordination, SF Memorial, Space Hotels), working as printed.

Valley Trust's first action draws on Prelude Cards, so it depends on the setup step. Decide whether the Corporations are dealt only in Games with Prelude; Recorded Games show all 17 together in those Games.

**Blocked by:** 02 — The Prelude setting and setup

**Status:** ready-for-agent

- [ ] Each card and Corporation has at least one scenario test, and the coverage check counts them.
- [ ] Rules calls are in the rules notes.
- [ ] Each is playable in the GUI, and the Corporations show on the player board with their abilities.
- [ ] The short fuzz run stays clean with them in play.

## Comments

### 2026-11-06 — from ticket 01 (Claude)

The coverage check counts a card once it has `"effects"`. The mismatch report compares a Corporation's starting MegaCredits once it has effect data, and Vitor will then differ: 45 as printed, 48 in the open-source game, which adds its own effect's 3. Psychrophiles may need `CARDS_HOLDING_CARD_RESOURCES` raised. See ticket 01's Comments.

### 2026-11-07 — from ticket 02 (Claude)

Prelude's 7 Project Cards are in the deck of a Game with Prelude, unplayable until they get effect data, and a Scenario with `prelude=True` may name them. Prelude's Corporations aren't dealt and `find_corporation` still means the base box. For Valley Trust, the Prelude Cards not dealt aren't kept anywhere yet. See ticket 02's Comments.

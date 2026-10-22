# 19 — Card Resources: microbes and science

**What to build:** Cards that use microbe or science Card Resources. This brings in Card Resources: adding them to and removing them from cards, and Victory Points per Card Resource. The GUI shows Card Resources on played cards.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 15 — Active cards with actions; 16 — Ongoing effects

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [ ] Test: Card Resources count for Victory Points as printed.

**Cards in this batch (12):**

- [ ] #005 Search for Life
- [ ] #033 Regolith Eaters
- [ ] #034 GHG Producing Bacteria
- [ ] #035 Ants
- [ ] #049 Tardigrades
- [ ] #095 Physics Complex
- [ ] #131 Decomposers
- [ ] #133 Symbiotic Fungus
- [ ] #134 Extreme-Cold Fungus
- [ ] #157 Nitrite Reducing Bacteria
- [ ] #170 Aerobraked Ammonia Asteroid
- [ ] #185 Olympus Conference

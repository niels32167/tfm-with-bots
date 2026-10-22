# 18 — Special Tiles and reserved Areas

**What to build:** Cards that place special Tiles or use a reserved Area (Noctis City, Phobos Space Haven, Ganymede Colony). Special Tiles count as Tiles for adjacency and Landlord as the rules say.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [ ] Test: each reserved Area is used only by its card.

**Cards in this batch (10):**

- [ ] #017 Noctis City
- [ ] #021 Phobos Space Haven
- [ ] #044 Natural Preserve
- [ ] #064 Mining Area
- [ ] #067 Mining Rights
- [ ] #081 Ganymede Colony
- [ ] #085 Commercial District
- [ ] #097 Nuclear Zone
- [ ] #140 Lava Flows
- [ ] #142 Mohole Area

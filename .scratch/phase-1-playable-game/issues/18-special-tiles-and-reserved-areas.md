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

**Cards in this batch (12):**

- [ ] #008 Capital — moved here from ticket 11 (2026-10-27): its City Tile is a special Tile, scored by the Oceans next to it
- [ ] #017 Noctis City
- [ ] #021 Phobos Space Haven — a City off Mars: Martian Rails (ticket 15) counts only Cities on Mars (`{"tiles_on_mars": "city"}`), so test that it leaves this one out
- [ ] #044 Natural Preserve
- [ ] #064 Mining Area — Robotic Workforce (ticket 12) copies the Production this card's Tile gave, steel or titanium (FAQ)
- [ ] #066 Land Claim — moved here from ticket 14 (2026-10-29): an Event that reserves a non-reserved Area for its Player, so only they may place a Tile there
- [ ] #067 Mining Rights — Robotic Workforce (ticket 12) copies the Production this card's Tile gave, steel or titanium (FAQ)
- [ ] #081 Ganymede Colony — a City off Mars: Martian Rails (ticket 15) counts only Cities on Mars (`{"tiles_on_mars": "city"}`), so test that it leaves this one out
- [ ] #085 Commercial District
- [ ] #097 Nuclear Zone
- [ ] #123 Industrial Center — moved here from ticket 15 (2026-10-31): its special Tile goes next to a City. Its action ("spend 7 MC to increase your steel production 1 step") is ticket 15's effect data, `"action": {"resources": {"megacredits": -7}, "production": {"steel": 1}}`; its production box is that action's, which Robotic Workforce doesn't copy: add it to `PRODUCTION_BOX_IN_THE_ACTION` in `tests/rules/test_playing_cards.py`
- [ ] #140 Lava Flows
- [ ] #142 Mohole Area — on an Area reserved for Oceans, like Mangrove's `"on": "ocean_areas"` (ticket 11)
- [ ] #199 Restricted Area — moved here from ticket 15 (2026-10-31): its special Tile goes on any land. Its action ("spend 2 MC to draw a card") is ticket 15's effect data, `"action": {"resources": {"megacredits": -2}, "draw": 1}`

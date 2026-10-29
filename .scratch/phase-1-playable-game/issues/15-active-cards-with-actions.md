# 15 — Active cards with actions

**What to build:** Active (blue) cards whose text is an action. Using a card's action becomes an Action, available once per Generation for each card; the GUI shows which actions have been used this Generation.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [ ] Test: each card's action can be used only once per Generation, and becomes available again in the next one.

**Cards in this batch (20):**

- [ ] #006 Inventors' Guild
- [ ] #007 Martian Rails
- [ ] #012 Water Import from Europa
- [ ] #013 Space Elevator — Robotic Workforce (ticket 12) copies its lower panel's production box, so keep that box as `production` data
- [ ] #014 Development Center
- [ ] #015 Equatorial Magnetizer — its production box is part of its action, which Robotic Workforce (ticket 12) doesn't copy: narrow `test_every_implemented_building_card_has_its_printed_production_box_as_production_data` for it
- [ ] #069 Electro Catapult — Robotic Workforce (ticket 12) copies its lower panel's production box, so keep that box as `production` data
- [ ] #076 Space Mirrors
- [ ] #101 Ironworks
- [ ] #103 Steelworks
- [ ] #104 Ore Processor
- [ ] #110 Business Network
- [ ] #123 Industrial Center — its production box is part of its action, which Robotic Workforce (ticket 12) doesn't copy: narrow `test_every_implemented_building_card_has_its_printed_production_box_as_production_data` for it
- [ ] #154 Caretaker Contract
- [ ] #177 Water Splitting Plant
- [ ] #187 Aquifer Pumping
- [ ] #194 Power Infrastructure
- [ ] #199 Restricted Area
- [ ] #202 Underground Detonations — its production box is part of its action, which Robotic Workforce (ticket 12) doesn't copy: narrow `test_every_implemented_building_card_has_its_printed_production_box_as_production_data` for it
- [ ] #208 AI Central — Robotic Workforce (ticket 12) copies its lower panel's production box, so keep that box as `production` data

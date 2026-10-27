# 12 — Automated cards #065–#130

**What to build:** The Automated (green) cards numbered #065–#130 that weren't sorted into a mechanism batch.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (30):**

- [ ] #065 Building Industries
- [ ] #068 Sponsors
- [x] #077 Solar Wind Power — done in ticket 08 (to test the central rules)
- [ ] #082 Callisto Penal Mines
- [ ] #083 Giant Space Mirror
- [ ] #084 Trans-Neptune Probe
- [ ] #086 Robotic Workforce
- [x] #087 Grass — done in ticket 08 (starter set)
- [ ] #088 Heather
- [ ] #089 Peroxide Power
- [ ] #090 Research
- [ ] #091 Gene Repair
- [x] #092 Io Mining Industries — done in ticket 08 (to test the central rules)
- [ ] #093 Bushes
- [ ] #098 Tropical Resort
- [ ] #100 Fueled Generators
- [ ] #102 Power Grid — effect data `"production_per"` from ticket 11
- [ ] #106 Acquired Company
- [ ] #108 Open City
- [x] #113 Solar Power — done in ticket 08 (starter set)
- [ ] #114 Breathing Filters
- [ ] #115 Artificial Photosynthesis
- [ ] #116 Artificial Lake — an Ocean on land: add a variant to `board::Areas` (ticket 11), which `place_ocean` already takes
- [ ] #117 Geothermal Power
- [ ] #118 Farming
- [x] #119 Dust Seals — done in ticket 08 (to test the central rules)
- [ ] #120 Urbanized Area
- [ ] #122 Moss
- [ ] #126 GHG Factories
- [ ] #130 Worms — effect data `"production_per"` from ticket 11

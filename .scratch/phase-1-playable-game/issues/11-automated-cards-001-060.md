# 11 — Automated cards #001–#060

**What to build:** The Automated (green) cards numbered #001–#060 that weren't sorted into a mechanism batch.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (25):**

- [ ] #001 Colonizer Training Camp
- [ ] #003 Deep Well Heating
- [ ] #008 Capital
- [ ] #016 Domed Crater
- [ ] #018 Methane from Titan
- [x] #022 Black Polar Dust — done in ticket 08 (starter set)
- [ ] #029 Cupola City
- [ ] #030 Lunar Beam
- [ ] #032 Underground city
- [ ] #040 Asteroid Mining
- [ ] #041 Food Factory
- [ ] #042 Archaebacteria
- [ ] #043 Carbonate Processing
- [x] #045 Nuclear Power — done in ticket 08 (starter set)
- [ ] #046 Lightning Harvest
- [ ] #047 Algae
- [ ] #048 Adapted Lichen
- [ ] #051 Miranda Resort
- [x] #053 Lake Marineris — done in ticket 08 (starter set)
- [ ] #055 Kelp Farming
- [x] #056 Mine — done in ticket 08 (starter set)
- [ ] #057 Vesta Shipyard
- [ ] #058 Beam from a Thorium Asteroid
- [ ] #059 Mangrove
- [x] #060 Trees — done in ticket 08 (starter set)

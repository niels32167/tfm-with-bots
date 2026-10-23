# 13 — Automated cards #132–#207

**What to build:** The Automated (green) cards numbered #132–#207 that weren't sorted into a mechanism batch.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (33):**

- [x] #132 Fusion Power — done in ticket 08 (to test the central rules)
- [ ] #135 Advanced Ecosystems
- [ ] #136 Great Dam
- [ ] #137 Cartel
- [x] #138 Strip Mine — done in ticket 08 (starter set)
- [x] #139 Wave Power — done in ticket 08 (to test the central rules)
- [x] #141 Power Plant — done in ticket 08 (starter set)
- [x] #144 Titanium Mine — done in ticket 08 (starter set)
- [ ] #145 Tectonic Stress Power
- [ ] #146 Nitrophilic Moss
- [ ] #148 Insects
- [ ] #152 Insulation
- [ ] #155 Designed Microorganisms
- [ ] #158 Industrial Microbes
- [ ] #159 Lichen
- [ ] #164 Micro-Mills
- [ ] #165 Magnetic Field Generators
- [x] #168 Windmills — done in ticket 08 (starter set)
- [ ] #169 Tundra Farming
- [ ] #171 Magnetic Field Dome
- [ ] #174 Protected Valley
- [ ] #175 Satellites
- [ ] #176 Noctis Farming
- [ ] #179 Soil Factory
- [ ] #180 Fuel Factory
- [ ] #182 Corporate Stronghold
- [x] #186 Rad-Suits — done in ticket 08 (to test the central rules)
- [ ] #193 Plantation
- [x] #196 Lagrange Observatory — done in ticket 08 (to test the central rules)
- [ ] #197 Terraforming Ganymede
- [ ] #203 Soletta
- [x] #205 Rad-Chem Factory — done in ticket 08 (to test the central rules)
- [ ] #207 Medical Lab

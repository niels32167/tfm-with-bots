# 01 — Prelude cards in the catalog

**What to build:** Import the printed data of Prelude's 47 cards into the card file, so that the catalog, the card gallery and the mismatch report know them, without any Game dealing them yet (ADR 0011).

The saved card list holds them all. Recorded Games confirm which belong: 35 Prelude Cards, 5 Corporations and 7 Project Cards. The card list's other Prelude-marked entries (Corporate Archives, Double Down, Merger, New Partner, Head Start) never appear in those Games and stay out.

- **Prelude Cards:** Acquired Space Agency, Allied Banks, Aquifer Turbines, Biofuels, Biolab, Biosphere Support, Business Empire, Dome Farming, Donation, Early Settlement, Ecology Experts, Eccentric Sponsor, Experimental Forest, Galilean Mining, Great Aquifer, Huge Asteroid, Io Research Outpost, Loan, Martian Industries, Metal-Rich Asteroid, Metals Company, Mining Operations, Mohole, Mohole Excavation, Nitrogen Shipment, Orbital Construction Yard, Polar Industries, Power Generation, Research Network, Self-Sufficient Settlement, Smelting Plant, Society Support, Supplier, Supply Drop, UNMI Contractor.
- **Corporations:** Cheung Shing Mars, Point Luna, Robinson Industries, Valley Trust, Vitor.
- **Project Cards:** House Printing, Lava Tube Settlement, Martian Survey, Psychrophiles, Research Coordination, SF Memorial, Space Hotels.

Sources spell some names differently (Allied Bank/Allied Banks, Excentric/Eccentric Sponsor, Biolab/Biolabs). Settle each by the printed card, and record it as ticket 07 of phase 1 did.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] The card import brings in exactly these 47 cards, and running it again changes nothing.
- [ ] The catalog has a Prelude Card type, and a Game without Prelude never deals any of the 47 cards.
- [ ] Each card records its expansion, so that the deck for a Game can be built from it.
- [ ] The card gallery draws them, filterable by type, using the card list's layout and icons.
- [ ] The mismatch report compares them with the open-source game's definitions, downloading those into `.cache/`, and has no open entries.
- [ ] Games without Prelude are unchanged: the benchmark shows no meaningful slowdown, and old Replays load.

## Comments

# 17 — Attacks and effects on other Players

**What to build:** Cards that affect another Player, such as removing their Resources or lowering their Production. This brings in the choose-a-target-Player Decision, including the choices the rules allow when nobody has anything to lose.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [ ] Test: a target-Player Decision offers exactly the targets the rules allow.

**Cards in this batch (23):**

- [ ] #002 Asteroid Mining Consortium
- [ ] #004 Cloud Seeding
- [ ] #009 Asteroid
- [ ] #010 Comet
- [ ] #011 Big Asteroid
- [ ] #039 Deimos Down
- [ ] #061 Great Escarpment Consortium
- [ ] #063 Mining Expedition
- [ ] #080 Giant Ice Asteroid
- [ ] #096 Greenhouses
- [ ] #099 Toll Station
- [ ] #107 Media Archives
- [ ] #121 Sabotage
- [ ] #124 Hired Raiders
- [ ] #125 Hackers
- [ ] #129 Zeppelins
- [ ] #160 Power Supply Consortium
- [ ] #178 Heat Trappers
- [ ] #183 Biomass Combustors
- [ ] #188 Flooding
- [ ] #189 Energy Saving
- [ ] #198 Immigration Shuttles
- [ ] #201 Energy Tapping

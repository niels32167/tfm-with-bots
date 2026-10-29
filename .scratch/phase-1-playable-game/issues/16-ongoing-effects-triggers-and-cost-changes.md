# 16 — Ongoing effects: triggers and cost changes

**What to build:** Active (blue) cards whose text is an ongoing effect. This brings in the trigger machinery (for example when any Player plays a Tag or places a Tile), cost discounts, changes to how much steel and titanium are worth, Requirement modifiers, and Standard Project refunds.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [ ] Test: triggers fire for the right Player, once per qualifying event, including when the triggering card is played.

**Cards in this batch (17):**

- [ ] #020 Research Outpost
- [ ] #023 Arctic Algae
- [ ] #025 Space Station
- [ ] #031 Optimal Aerobraking
- [ ] #038 Rover Construction
- [ ] #070 Earth Catapult
- [ ] #071 Advanced Alloys
- [ ] #073 Mars University — Research (ticket 12) counts as playing 2 science Tags, so it triggers this twice
- [ ] #079 Quantum Extractor
- [ ] #094 Mass Converter
- [ ] #105 Earth Office
- [ ] #109 Media Group
- [ ] #150 Anti-gravity Technology
- [ ] #153 Adaptation Technology
- [ ] #156 Standard Technology
- [ ] #166 Shuttles
- [ ] #200 Immigrant City — Robotic Workforce (ticket 12) copies only its lower production box (-1 energy, -2 MegaCredits), not its effect's (FAQ)

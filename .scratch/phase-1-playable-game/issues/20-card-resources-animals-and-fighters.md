# 20 — Card Resources: animals and fighters

**What to build:** Cards that use animal or fighter Card Resources, including protection effects and the cards that remove animals from other Players.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 15 — Active cards with actions; 16 — Ongoing effects; 17 — Attacks

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (17):**

- [ ] #019 Imported Hydrogen
- [ ] #024 Predators
- [ ] #026 Eos Chasma National Park
- [ ] #028 Security Fleet
- [ ] #050 Virus
- [ ] #052 Fish
- [ ] #054 Small Animals
- [ ] #072 Birds
- [ ] #074 Viral Enhancers — the open-source game offers Nitrophilic Moss (ticket 13, "lose 2 plants") with only 1 plant while Viral Enhancers is in play, as its plant Tag gains a plant first; Moss (#122, lose 1) likewise with none. Decide whether the plant loss is checked before or after the "when you play" effect, and update "Production at its limit" in docs/rules-notes.md
- [ ] #128 Ecological Zone
- [ ] #143 Large Convoy
- [ ] #147 Herbivores
- [ ] #163 Imported Nitrogen
- [ ] #172 Pets
- [ ] #173 Protected Habitats
- [ ] #184 Livestock
- [ ] #190 Local Heat Trapping

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

CEO's Favorite Project (#149, ticket 19, moved from ticket 14) adds 1 Card Resource to any card with at least 1: check that it can target this batch's animal and fighter cards too.

- [ ] #019 Imported Hydrogen
- [ ] #024 Predators — "remove 1 animal from any card" can share ticket 17's target Decision (`Waiting::Target`, `targets::target_options`): see "Taking from any Player" in docs/rules-notes.md
- [ ] #026 Eos Chasma National Park
- [ ] #028 Security Fleet
- [ ] #050 Virus — "remove up to 2 animals or 5 plants from any player" is ticket 17's `"any_player": {"remove": [...]}` once a Card Resource can be an alternative
- [ ] #052 Fish
- [ ] #054 Small Animals
- [ ] #072 Birds
- [ ] #074 Viral Enhancers — the open-source game offers Nitrophilic Moss (ticket 13, "lose 2 plants") with only 1 plant while Viral Enhancers is in play, as its plant Tag gains a plant first; Moss (#122, lose 1) likewise with none. Decide whether the plant loss is checked before or after the "when you play" effect, and update "Production at its limit" in docs/rules-notes.md
- [ ] #128 Ecological Zone — a `"when"` Trigger (ticket 16) on several Tags with a Card Resource gain, as Decomposers (ticket 19)
- [ ] #143 Large Convoy
- [ ] #147 Herbivores — a `"when"` Trigger (ticket 16): `{"tile_placed": {"tile": "greenery", "by": "you"}}`, with a Card Resource gain
- [ ] #163 Imported Nitrogen
- [ ] #172 Pets — a `"when"` Trigger (ticket 16): `{"tile_placed": {"tile": "city", "by": "anyone"}}`, with a Card Resource gain
- [ ] #173 Protected Habitats — "opponents may not remove your plants, animals or microbes": `targets::target_options` must leave its Player out of plant removals (Asteroid, Comet, Big Asteroid, Deimos Down, Mining Expedition, Giant Ice Asteroid, ticket 17), and the fuzz invariant `targets_offered_are_those_the_rules_allow` must know it. It doesn't protect Production
- [ ] #184 Livestock
- [ ] #190 Local Heat Trapping

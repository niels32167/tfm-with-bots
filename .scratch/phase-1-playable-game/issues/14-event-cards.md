# 14 — Event cards

**What to build:** The Event (red) cards without attacks, special Tiles or Card Resources. After use, an Event lies face down and its Tags stop counting, except at the moment it is played, as the rules say.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [ ] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [ ] Rules judgment calls are recorded in the rules notes.
- [ ] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [ ] Test: an Event's Tags stop counting after it has been played.

**Cards in this batch (21):**

- [ ] #027 Interstellar Colony Ship
- [ ] #036 Release of Inert Gases
- [ ] #037 Nitrogen-Rich Asteroid
- [ ] #062 Mineral Deposit
- [ ] #066 Land Claim
- [ ] #075 Towing a Comet
- [ ] #078 Ice Asteroid
- [ ] #111 Business Contacts
- [ ] #112 Bribed Committee
- [ ] #127 Subterranean Reservoir
- [ ] #149 CEO's Favorite Project
- [ ] #151 Investment Loan
- [ ] #161 Convoy From Europa
- [ ] #162 Imported GHG
- [ ] #167 Import of Advanced GHG
- [ ] #181 Ice Cap Melting
- [ ] #191 Permafrost Extraction
- [ ] #192 Invention Contest
- [ ] #195 Indentured Workers
- [ ] #204 Technology Demonstration
- [ ] #206 Special Design

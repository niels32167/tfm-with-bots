# 14 — Event cards

**What to build:** The Event (red) cards without attacks, special Tiles or Card Resources. After use, an Event lies face down and its Tags stop counting, except at the moment it is played, as the rules say.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [x] Test: an Event's Tags stop counting after it has been played.

**Cards in this batch (21):**

- [x] #027 Interstellar Colony Ship
- [x] #036 Release of Inert Gases
- [x] #037 Nitrogen-Rich Asteroid
- [x] #062 Mineral Deposit
- [ ] #066 Land Claim — moved to ticket 18 (2026-10-29): reserves an Area
- [x] #075 Towing a Comet
- [x] #078 Ice Asteroid
- [x] #111 Business Contacts
- [x] #112 Bribed Committee
- [x] #127 Subterranean Reservoir
- [ ] #149 CEO's Favorite Project — moved to ticket 19 (2026-10-29): Card Resources; note on ticket 20
- [x] #151 Investment Loan
- [x] #161 Convoy From Europa
- [x] #162 Imported GHG
- [x] #167 Import of Advanced GHG
- [x] #181 Ice Cap Melting
- [x] #191 Permafrost Extraction
- [x] #192 Invention Contest
- [ ] #195 Indentured Workers — moved to ticket 16 (2026-10-29): cost change on the next card
- [x] #204 Technology Demonstration
- [ ] #206 Special Design — moved to ticket 16 (2026-10-29): Requirement modifier on the next card

## Comments

### 2026-10-29 — implemented (Claude); close-out unfinished (usage limit)

**Decisions made with the user** (one round; every recommended option chosen): Business Contacts and
Invention Contest use effect data `"look_at": {"cards": N, "keep": K}` and a new `keep_cards`
Decision, one card at a time; Nitrogen-Rich Asteroid uses new effect data `production_at_least`;
Indentured Workers and Special Design move to 16, Land Claim to 18, CEO's Favorite Project to 19
(note on 20); seams as tickets 11-13 plus an engine view test and a server test.

**Calls made by Claude** (recorded in `docs/rules-notes.md`): "Looking at cards to keep some of
them", "Nitrogen-Rich Asteroid's plant Production", titanium paying for an Event's space Tag (under
"Tags on played Events"), and the Ocean Events at 8-9 Oceans (under "A card's Oceans once 9 are
placed").

**Design notes:** 17 cards implemented (105 in all: 88 Automated, 17 Events; README updated).
Engine: `cards::LookAt`, `cards::ProductionAtLeast`, `card_flow::Keeping` and `Game::keeping`,
`DecisionKind::KeepCards`, `DecisionOption::KeepCard`, log lines "looks at the top 4 cards of the
deck" / "keeps 2 cards and discards 2", `PlayerBoard.keeping` (own view and full view only).
`play_card` now runs `look_at_cards`, then `choose_production_change`, then the Tiles. GUI: the
buying panel shows the cards to keep with a Kept strip; the status bar names the card. Fuzz
invariant `every_card_in_exactly_one_place` counts the cards looked at and kept. 789 tests pass.
Browser check (1440x900, Hotseat): all 17 offered; Business Contacts and Invention Contest kept
through the panel; Nitrogen-Rich Asteroid with 3 plant Tags gave 1 + 3; Towing a Comet highlighted
the 12 Ocean Areas; no console errors. Fuzz: 20,000 Games, 13,695,964 Decisions in 231 s, no
failures ("performance" profile, not charging, battery 80 %).

**Still open (the session hit its usage limit):**
- Benchmark (`uv run python -m tools.benchmark`) and the 300-Game play count per new card not run.
- Code review findings not yet applied: doc lines over width in `tm_engine.pyi` (3) and the
  effect-order note in `docs/rules-notes.md`; `look_at_cards` hides that it continues to the
  Production change and Tiles (rename or move the continuation into `play_card`); mixed i32/usize
  in `LookAt`/`Keeping`/log; `keeping_options` could be `Keeping::options`; the StatusBar text can
  render "undefined"; untested note claims (a reshuffle mid-look, fewer than `keep` cards left).
- Left as is for now: `Game`'s waiting fields grew to a 6-tuple (one enum, tickets 15-17);
  `ProductionAtLeast` repeats `ProductionPer`'s fields.

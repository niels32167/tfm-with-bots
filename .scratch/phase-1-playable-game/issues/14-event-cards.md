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

### 2026-10-29 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **Business Contacts and Invention Contest are effect data**, `"look_at": {"cards": 4, "keep":
  2}` (and 3 / 1), with a new `keep_cards` Decision that keeps one card at a time.
- **Nitrogen-Rich Asteroid is effect data**: `"production": {"plants": 1}` plus a new
  `"production_at_least": {"resource": "plants", "steps": 3, "at_least": 3, "of": {"tag":
  "plant"}}`.
- **Four cards move**, each noted on both tickets: Indentured Workers (#195) and Special Design
  (#206) to ticket 16 (cost and Requirement changes on the next card), Land Claim (#066) to ticket
  18 (a reserved Area), CEO's Favorite Project (#149) to ticket 19 (Card Resources), with a note
  on ticket 20 for animals and fighters.
- **Test seams** as in tickets 11-13, plus an engine view test for the hidden cards and a server
  test for the new Decision.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Cards"):
- **"Looking at cards to keep some of them"**: the cards are taken once the card is paid for; the
  Options come in card-number order; the kept cards go into the hand together and the rest face
  down to the discard pile; only that Player sees them, and the log gives counts, not names; the
  deck running out reshuffles the discard pile as for any draw; with no more cards than the
  number kept, there is no Decision.
- **"Nitrogen-Rich Asteroid's plant Production"**: 4 with 3 or more plant Tags, logged as a raise
  of 1 and then of 3.
- **Titanium pays for an Event with a space Tag** (Imported GHG), added to "Tags on played Events":
  its Tags count while it is being played.
- **The Ocean Events follow "A card's Oceans once 9 are placed"** (Ice Asteroid with 8, Subterranean
  Reservoir with 9, Towing a Comet and Convoy From Europa with 9 still do the rest).
- **Investment Loan** is not offered at −5 MegaCredit Production ("Production at its limit").
- **The ticket's criterion "an Event's Tags stop counting after it has been played"** was covered by
  `tests/rules/test_tags.py` with Events set up as played; a new test plays Technology
  Demonstration during the Game and checks its science and space Tags don't count afterwards.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): 14 Events use only `resources`, `production`,
  `oxygen`, `terraform_rating`, `draw` and `tiles`; Interstellar Colony Ship has `{}` (its
  Requirement and 4 Victory Points are printed data); Nitrogen-Rich Asteroid adds
  `production_at_least`; Business Contacts and Invention Contest use `look_at`. Bribed Committee's
  −2 Victory Points needed no change. 105 cards are now implemented, 88 Automated and 17 Events
  (the README says so).
- **Engine:**
  - `cards::ProductionAtLeast` and `Effects::production_at_least`, carried out right after
    Production per Tag or Tile; `cards::LookAt` and `Effects::look_at`, after the cards drawn. The
    order is in the `Effects` doc and the rules notes.
  - `card_flow::Keeping { card, looking_at, kept, keep }` and `Game::keeping`, with
    `Keeping::options`, `Game::look_at_cards` (returns whether the Game now waits on the keep) and
    `Game::keep_card`. `play_card` carries out the data, then looks at cards, and only once
    keeping is done makes the Production change (`choose_production_change`, split out of
    `play_card`) and places the Tiles.
  - `DecisionKind::KeepCards` ("keep_cards"), `DecisionOption::KeepCard` (label "Keep Mine",
    details `{"type": "keep_card", "card": "mine"}`), log lines "Player 1 looks at the top 4 cards
    of the deck." and "Player 1 keeps 2 cards and discards 2."
  - `PlayerBoard.keeping` (`{"card", "looking_at", "kept", "keep"}`), only in the Player's own view
    and the full view.
- **GUI:** the buying panel shows the cards to keep, as in the Draft, with a "Kept" strip; the status
  bar says "Player 1 must keep 2 of the cards above for Business Contacts and discard the rest".
- **`engine/tm_engine.pyi`** documents `production_at_least`, `look_at`, the `keep_cards` Decision and
  the `keeping` view field.
- **Tests** (791 in all, up from 734): 17 card files; `tests/engine/test_views.py` (no other Player
  sees the cards looked at, and the log names none); `tests/server/test_keeping_cards.py`; two
  invariant tests; `keeping` in `tests/helpers.py`. The Investment Loan limit test was checked by
  breaking the Production check for a moment. The 9-Ocean tests stay green with the Ocean exception
  in `can_take_action_placing` broken, since 3 Ocean Areas are still free at 9 Oceans; they pin
  "places none", and Aquifer's tests pin the exception.
- **Fuzzer:** `every_card_in_exactly_one_place` counts the cards looked at and kept. In 300 random
  Games with the implemented cards first, every new card was played (Invention Contest 107 times,
  Mineral Deposit 104, Bribed Committee and Investment Loan 92, Business Contacts 88, Imported GHG 85,
  Import of Advanced GHG 84, Technology Demonstration 83, Convoy From Europa 68, Subterranean
  Reservoir 66, Release of Inert Gases 59, Ice Asteroid 43, Towing a Comet 42, Permafrost Extraction
  41, Ice Cap Melting 31, Nitrogen-Rich Asteroid 23) except Interstellar Colony Ship: only once did a
  Player reach its 5 science Tags, at the end of the Game.
- **Checked in the browser** (1440×900, Hotseat, a Scenario with all 17 cards in hand loaded through
  a second WebSocket): all 17 were offered; Business Contacts showed its 4 cards in the panel, kept
  two one at a time with the "Kept" strip and the status text counting down, then closed the panel;
  Invention Contest offered 3 and kept 1; Nitrogen-Rich Asteroid with 3 plant Tags raised plant
  Production by 1 and by 3; Towing a Comet gained its plants and Oxygen step and highlighted the 12
  Ocean Areas; no console errors. Vite had cached the old `StatusBar.tsx` until the file was touched.
- **Game length and speed** (on mains, battery at 80 % and not charging, "performance" profile):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,695,964 Decisions in 231 s, with no failures; the
    longest Game lasted 37 Generations. After the code review's engine changes, another 20,000 Games
    (13,710,470 Decisions, 225 s) were also clean.
  - Benchmark: 88,196 Games/s on 16 processes and 8,580 in 1, against ticket 13's 92,238 and 8,399.
    Copies take 0.17, 0.56 and 0.88 µs at the start, halfway (346 picks) and at the end (692 picks).
    Every target is met.

**Code review** (`/code-review`, standards and spec; nothing blocking):
- Fixed:
  - `look_at_cards` used to carry on into the Production change and the Tiles, hidden by its name;
    `play_card` now shows that order itself.
  - `keeping_options` never read the Game; it is now `Keeping::options`.
  - The status bar could have shown "undefined" without a `keeping` view; it now falls back.
  - Over-width lines in `tm_engine.pyi` (3) and the "order of a card's effects" note.
  - The rules notes claimed untested cases: tests now cover the deck running out mid-look, only 1
    card left, and Convoy From Europa at 9 Oceans. The Nitrogen-Rich Asteroid note no longer claims
    when the Tags are counted, which this card can't show.
- Left as is:
  - **`Game`'s waiting fields** grew to six (`decision()` matches a 6-tuple). One enum for "what the
    Decision waits on" stays a refactor for tickets 15-17, as tickets 12 and 13 noted.
  - **`ProductionAtLeast`** repeats `ProductionPer`'s `resource`, `steps` and `of`, as
    `TerraformRatingPer` does; bundling them would change how `production_per` is read.
  - **Number types**: `LookAt`'s counts are `i32` like every `Effects` field, while the Game counts
    cards in `usize` like `CardSet::len`, so `look_at_cards` converts once.
  - **The GUI's `BuyingPanel`** now also shows cards to keep; renaming it is not worth the churn, and
    its doc says so.
  - **A Random Bot keeping cards pauses** between its picks like any other pick in its Turn: the
    picks are random and in its own Turn, so the timing reveals nothing (only simultaneous picks
    skip the pause).
  - Repeated Scenarios in test files: test files write their facts out on purpose.

**Open points:**
- **Moved cards** wait on tickets 16 (Indentured Workers, Special Design), 18 (Land Claim) and 19
  (CEO's Favorite Project; ticket 20 checks it can target animals and fighters).
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities apart
  (ticket 22); `Game`'s waiting fields could become one enum (tickets 15-17); Viral Enhancers' plant
  check (ticket 20).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

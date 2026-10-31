# 16 — Ongoing effects: triggers and cost changes

**What to build:** Active (blue) cards whose text is an ongoing effect. This brings in the trigger machinery (for example when any Player plays a Tag or places a Tile), cost discounts, changes to how much steel and titanium are worth, Requirement modifiers, and Standard Project refunds.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [x] Test: triggers fire for the right Player, once per qualifying event, including when the triggering card is played.

**Cards in this batch (19):**

- [x] #020 Research Outpost
- [x] #023 Arctic Algae
- [x] #025 Space Station
- [x] #031 Optimal Aerobraking
- [x] #038 Rover Construction
- [x] #070 Earth Catapult
- [x] #071 Advanced Alloys
- [x] #073 Mars University — Research (ticket 12) counts as playing 2 science Tags, so it triggers this twice
- [x] #079 Quantum Extractor
- [x] #094 Mass Converter
- [x] #105 Earth Office
- [x] #109 Media Group
- [x] #150 Anti-gravity Technology
- [x] #153 Adaptation Technology
- [x] #156 Standard Technology
- [x] #166 Shuttles
- [x] #195 Indentured Workers — moved here from ticket 14 (2026-10-29): an Event whose effect is a cost change on the next card played this Generation
- [x] #200 Immigrant City — Robotic Workforce (ticket 12) copies only its lower production box (-1 energy, -2 MegaCredits), not its effect's (FAQ)
- [x] #206 Special Design — moved here from ticket 14 (2026-10-29): an Event whose effect is a Requirement modifier (±2 steps of Global Parameters) on the next card played this Generation

## Comments

### 2026-10-31 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **Ongoing effects are effect data**, as actions were in ticket 15: `"discount"`, `"cube_values"`,
  `"requirement_steps"`, an Event's `"next_card"`, and Triggers in `"when"`. Rust code only for Mars
  University's Decision and Immigrant City's order (ADR 0009's "triggers get Rust code" is thus
  narrowed, as it was for actions).
- **Mars University's discard comes after the card's other effects**, its Tiles included, one
  Decision per science Tag: one Option per card in hand and Done, none with an empty hand.
- **The GUI shows the discounted cost on the hand's cards**, the printed cost struck through; a
  player-board badge shows what waits on the next card; Mars University's discard is picked in the
  hand, with a Done button.
- **Test seams** as in tickets 11–15, plus `tests/rules/test_triggers.py` and
  `test_cost_changes.py`, an engine view test, a server test and invariant tests.
- No card moved to another ticket: Research Outpost's City "next to no other tile" is a new
  `Areas` value, like Urbanized Area's.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Cards"):
- **"Discounts"**: they add up and never take a cost below 0; a card's own discount doesn't apply
  to itself; only cards played get cheaper, not Standard Projects, actions or cards bought; an
  Event's Tags count (Space Station on Ice Asteroid). Per Tag or per card gives the same costs, as
  no v1 card has two space or two Earth Tags (a test checks this).
- **"What steel and titanium are worth with Advanced Alloys"**: 3 and 4, for cards and for Aquifer
  Pumping's and Water Import from Europa's actions.
- **"Requirement steps"**: always in the Player's favour, with no Decision; Adaptation Technology
  and Special Design add up to 4 steps; a Temperature step is 2 °C.
- **"An Event's effect on the next card played"**: used up by whatever card comes next, lost at the
  end of the Generation; Special Design after Indentured Workers costs 0 and uses it up.
- **"Triggers"**: for the card's own Player, whoever sets them off; once per Tile, card or Tag; the
  card itself counts when it matches ("including this"); fired once the card played is paid for,
  before its effects; in player number order, which never changes the outcome.
- **"Immigrant City's own City"**: City first, then the Production decrease, so it is playable at
  −4 MegaCredit Production (the dominant order, and the open-source game's). The FAQ itself could
  not be fetched (both copies refused the download).
- **"Mars University's discard"**, **"Standard Technology"** (after paying, not Sell Patents) and
  **"Research Outpost's City"** (no Tile of any kind next to it, Oceans included).

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): the 19 cards. 142 cards are now implemented: 88
  Automated, 35 Active and 19 Events (the README says so).
- **Engine:**
  - `cards::Effects` gains `discount: Option<Discount>`, `cube_values: Option<CubeValues>`,
    `requirement_steps`, `next_card: Option<NextCard>` and `when: Vec<Trigger>`; a `Trigger` is a
    `TriggerCondition` (`TilePlaced { tile, by }`, `CardPlayed { card_type, tag }`,
    `TagPlayed(tag)`, `StandardProject`) with `resources` and `production` gained.
    `cards::CARDS_WITH` holds the cards with each kind of ongoing effect, so the hot paths look
    only at `played.intersection(...)` (new `CardSet::intersection`).
  - `playing_cards.rs`: `card_cost` (discounts and the next card's), `cube_values` (read by
    `spendable` and `ways_to_pay`, so actions too), `meets` with `requirement_steps`, and
    `next_card_effect`. `play_card` sets `Player::next_card` once paid for.
  - New `triggers.rs`: `Happened` (a Tile placed, a card played, a Standard Project paid for) and
    `Game::set_off`, called from `place_tile`, `play_card` and the Standard Projects. Log line
    "Player 2's Arctic Algae takes effect."
  - `card_code.rs`: `IMMIGRANT_CITY` (`can_carry_out_immigrant_city`, `finish_immigrant_city`,
    with `play_card` skipping its data until `place_next_card_tile` has placed its City) and
    `MARS_UNIVERSITY` (`Game::discards_to_draw`, `offer_discard_to_draw` from
    `finish_unless_placing`, `discard_to_draw`). New `Waiting::DiscardToDraw`,
    `DecisionKind::DiscardToDraw` ("discard_to_draw"), `DecisionOption::DiscardCard` ("Discard Mine
    to draw a card", `{"type": "discard_card", "card": "mine"}`), log "Player 1 discards a card to
    draw one."
  - `board::Areas::NextToNoOtherTile` ("next_to_no_other_tile").
  - Views: `PlayerBoard.card_costs` (with the hand only) and `next_card` (everyone's); the
    `play_card` Option's label and cost are the discounted cost.
- **GUI:** `PrintedCard` takes a `cost` and strikes the printed one through below the coin; the hand
  passes `card_costs`; `HAND_OPTIONS` (HandDock) lists play, sell and discard with their hints and
  the status bar reads it; the "Next card: −8 MegaCredits" / "±2 steps on global Requirements"
  badge on the player board; status texts for the discard, the isolated City and the discounted
  payment.
- **`engine/tm_engine.pyi`** documents the new forms, the "discard_to_draw" Decision,
  `"next_to_no_other_tile"`, `card_costs` and `next_card`.
- **Tests** (1,053 in all, up from 923): 19 card files; `tests/rules/test_triggers.py` (right
  Player, once per Tile, the 0 °C Ocean, both Players' Triggers on one City, the card played
  setting off its own, Research twice, and a catalog check that only "including this" cards can
  match themselves); `tests/rules/test_cost_changes.py`; a view test; a server test
  (`tests/server/test_discard_to_draw.py`); six invariant tests. `test_starting_a_game.py` and the
  full-view test know the two new view fields.
- **Fuzzer:** new invariants `cards_cost_what_the_discounts_leave` (the printed discounts written
  out in `DISCOUNTS` and `NEXT_CARD_DISCOUNTS`; the view's costs and the Options' agree; a next card
  only waits on such an Event, in the Action phase) and `discard_to_draw_offers_every_card_in_hand`;
  `legal_areas` knows `"next_to_no_other_tile"`.
- **In 300 random Games with the implemented cards first** (2–5 Players): played Indentured Workers
  112 times, Special Design 109, Earth Office 104, Media Group 102 (fired 77), Mars University 100
  (143 discards), Optimal Aerobraking 98 (fired 27), Advanced Alloys 94, Standard Technology 88
  (fired 1,448), Space Station 87, Rover Construction 80 (fired 468), Adaptation Technology 60,
  Research Outpost 58, Immigrant City 56 (fired 354), Arctic Algae 46 (fired 305), Earth Catapult 46,
  Shuttles 37, Quantum Extractor once; Mass Converter and Anti-Gravity Technology never (5 and 7
  science Tags, as AI Central in ticket 15). 563 cards were played at a discount, and 12 only
  thanks to Adaptation Technology's steps (none with Special Design's).
- **Checked in the browser** (1440×900, Hotseat, a Scenario loaded through a second WebSocket):
  discounted costs on the hand (Sponsors 3 with Earth Office, Satellites 8 with Space Station, the
  printed cost struck through); Indentured Workers' badge and costs 8 lower; Research Outpost paid
  with steel at 3 (Advanced Alloys), its City offered only away from Tiles, then Mars University's
  discard picked in the hand; Rover Construction, Arctic Algae, Standard Technology and Immigrant
  City logged as they fired, Immigrant City's Production lowered after its City; Special Design's
  badge and Breathing Filters offered at 5 % Oxygen. The struck-through cost was first clipped by
  the card's frame and moved below the coin. No console errors.
- **Game length and speed** (2026-10-31, on mains, battery at 80 % and not charging, "performance"
  profile):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,594,676 Decisions in 260 s, with no failures;
    the longest Game lasted 34 Generations.
    After the code review's engine changes, another 20,000 Games (13,567,887 Decisions, 247 s,
    longest 34 Generations) were also clean.
  - Benchmark: 70,813 Games/s on 16 processes and 7,156 in 1 (69,186 and 7,169 after the code
    review), against ticket 15's 82,567 and 7,665. The Game now ends after 690 picks, against 789,
    so picks per second fell by about a quarter: with 142 cards implemented rather than 123, more
    cards in each hand get the full check at every Action Decision. Making `meets` count
    Requirement steps only for global Requirements, and `can_play` work out the cost only after the
    Requirements, changed nothing measurable. Copies take 0.17, 0.57 and 0.88 µs. Every target is
    met.

**Code review** (`/code-review`, standards and spec; nothing blocking):
- Fixed:
  - `set_off`'s doc said "Players in turn from the first" and that every Trigger only gains
    something (Mars University's doesn't); the status bar's comment left out discarding.
  - `CARDS_WITH` had no doc; an invariant docstring was over-wide and computed a cost twice.
  - Names: `Happening` became `TriggerCondition` (beside `Happened`), `CardSet::and`
    `intersection`, `offers_discard_to_draw` `offer_discard_to_draw` (it acts); the discard button
    has its own `discardable` class.
  - Immigrant City's late Production change moved into `card_code::finish_immigrant_city`.
  - The hand Options are listed once (`HAND_OPTIONS`, with each one's hint), which the status bar
    reads, instead of twice.
  - The spec review found Quantum Extractor's and Mass Converter's "too few science Tags" tests one
    Tag looser than they claimed (2 and 3); they now have 3 and 4. The view test moved to
    `tests/engine/test_views.py`.
- Left as is:
  - **`can_carry_out_immigrant_city` repeats `can_carry_out`'s Production and Tile checks**:
    `Effects` isn't `Copy`, so adjusting its Production for the shared check would mean cloning it
    at every Action Decision.
  - **Card ids in generic code** (`IMMIGRANT_CITY` in `can_play`, `play_card` and
    `place_next_card_tile`; `MARS_UNIVERSITY` in `set_off`), as `ROBOTIC_WORKFORCE` and
    `INSULATION` already are; the bodies live in `card_code`.
- **Glossary:** "Trigger" and "Discount" are used as domain terms but are not in `CONTEXT.md`: a gap
  to settle with `/domain-modeling`.

**Open points:**
- **Hand-offs** are on the card lines of tickets 18 (Cities off Mars and special Cities set off
  Rover Construction and Immigrant City), 19 (Decomposers needs several Tags and a Card Resource
  gain; Olympus Conference and Mars University are due on the same science Tag), 20 (Pets,
  Herbivores, Ecological Zone as `"when"` Triggers) and 21 (which Corporation abilities fit the
  forms, which need more, and `CARDS_WITH` covering only Project Cards).
- **Mass Converter and Anti-Gravity Technology** were never played in random Games; their scenario
  tests cover them.
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities
  apart (ticket 22); Viral Enhancers' plant check (ticket 20); Martian Rails must leave out the
  Cities off Mars (ticket 18).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

# 12 — Automated cards #065–#130

**What to build:** The Automated (green) cards numbered #065–#130 that weren't sorted into a mechanism batch.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (30):**

- [x] #065 Building Industries
- [x] #068 Sponsors
- [x] #077 Solar Wind Power — done in ticket 08 (to test the central rules)
- [x] #082 Callisto Penal Mines
- [x] #083 Giant Space Mirror
- [x] #084 Trans-Neptune Probe
- [x] #086 Robotic Workforce
- [x] #087 Grass — done in ticket 08 (starter set)
- [x] #088 Heather
- [x] #089 Peroxide Power
- [x] #090 Research
- [x] #091 Gene Repair
- [x] #092 Io Mining Industries — done in ticket 08 (to test the central rules)
- [x] #093 Bushes
- [x] #098 Tropical Resort
- [x] #100 Fueled Generators
- [x] #102 Power Grid — effect data `"production_per"` from ticket 11
- [x] #106 Acquired Company
- [x] #108 Open City
- [x] #113 Solar Power — done in ticket 08 (starter set)
- [x] #114 Breathing Filters
- [x] #115 Artificial Photosynthesis
- [x] #116 Artificial Lake — an Ocean on land: add a variant to `board::Areas` (ticket 11), which `place_ocean` already takes
- [x] #117 Geothermal Power
- [x] #118 Farming
- [x] #119 Dust Seals — done in ticket 08 (to test the central rules)
- [x] #120 Urbanized Area
- [x] #122 Moss
- [x] #126 GHG Factories
- [x] #130 Worms — effect data `"production_per"` from ticket 11

## Comments

### 2026-10-29 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **Robotic Workforce (#086) is implemented here**, as Rust code of its own: a Production
  Decision over the Player's played building cards whose production box they can carry out in
  full. It is not offered without one, and with only one it copies at once. The card lines of
  tickets 13, 15, 16, 17, 18 and 21 say what their building cards need, and a catalog test
  fails if a building card's printed production box isn't Production data.
- **Artificial Photosynthesis (#115) is effect data**, `"production_choice": [{"plants": 1},
  {"energy": 2}]`, carried out by one new Production Decision that Robotic Workforce shares.
- **Test seams** as in ticket 11: per-card tests in `tests/cards/test_<id>.py` through
  `tm_engine`, rules tests, and the fuzz invariants. No server test: the server forwards the new
  Decision as the engine gives it.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Cards"):
- **Artificial Lake's Ocean** goes on any free Area reserved for nothing, so not on Noctis City's
  Area. From then on it is an Ocean like any other. The card needs such an Area, unless 9
  Oceans are placed: then it is played and places none.
- **Urbanized Area's City** goes on free land next to at least 2 Cities, whoever owns them.
  Later Cities keep apart from it, as from any City.
- **A Production change to choose** comes after the card's other effects and before its Tiles,
  with one Option for each change the Player can carry out. With only one, there is no
  Decision.
- **Robotic Workforce:**
  - one Option per card, in card-number order, even when two boxes are the same;
  - Production per Tag or Tile is counted again as it is copied;
  - Events and other Players' cards never count;
  - only the box is copied (Open City's plants and City are not).
- **Moss** is not offered without a plant to lose. The existing check on Resources covers it.
- **Research's two science Tags** both count, for the Scientist Award too.
- **The batch had 25 open cards.** The ticket lists 30, 5 of them done in ticket 08, not "4 of
  29" as the hand-off brief said. All 25 are implemented here; none moved.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`):
  - 21 cards use only `resources`, `production`, `draw`, `production_per` (Power Grid, and Worms
    at 1 per 2 microbe Tags) and the usual `"city"` (Open City); Trans-Neptune Probe and
    Breathing Filters have none;
  - two use new Area rules: `{"tile": "ocean", "on": "land"}` and
    `{"tile": "city", "on": "next_to_two_cities"}`;
  - Artificial Photosynthesis uses `production_choice`;
  - Robotic Workforce has `"effects": {}` plus its Rust code.

  64 cards are now implemented, all Automated (the README says so).
- **Engine:**
  - `board::Areas` gains `Land` and `NextToTwoCities`, in `areas_for` and `has_area_for`.
    `OceanAreas` became `ReservedForOceans`, because clippy objects to a variant ending in the
    enum's name once there are 3 or more. `#[serde(rename = "ocean_areas")]` keeps the data and
    the protocol as they were.
  - `Effects::production_choice: Vec<Resources>`.
  - `DecisionKind::Production` ("production") and
    `DecisionOption::ChangeProduction { card, change }`, where `ProductionChange` is
    `Alternative(index)` (the card's own) or `CopyBox(card)` (Robotic Workforce).
    `Game::choosing_production` holds the card while the Decision waits.
  - `play_card` carries out the data, then offers the Production change: none places the Tiles,
    one is made at once, more wait on the Decision. `can_play` checks
    `can_make_a_production_change`, which stops at the first possible change, like
    `has_area_for`.
  - **`engine/src/card_code.rs` is the first per-card Rust code** (ADR 0009). A card is named by
    a constant holding its catalog index (`ROBOTIC_WORKFORCE = 85`, its number minus 1).
    `CARDS_WITH_CODE` lists each constant with its id, and the catalog asserts them when it is
    first read. Later per-card code can follow this pattern.
  - `Card::has_production_box` and `Card::production_alternative`. A new log line: "Player 1
    copies the production box of Carbonate Processing."
  - Option details: `{"type": "choose_production", "card", "production"}` and
    `{"type": "copy_production_box", "card"}`. Labels: "Raise energy Production by 2", "Copy the
    production box of Mine".
- **GUI:** the status bar names the new Area rules ("…the Ocean on an Area reserved for
  nothing", "…the City next to at least 2 Cities") and the Production Decision ("…must choose
  how Artificial Photosynthesis changes their Production:", "…which of their building cards'
  production box Robotic Workforce copies:"). Its Options are status-bar buttons.
- **`engine/tm_engine.pyi`** documents `production_choice`, the three `"on"` values and the
  `"production"` Decision.
- **Tests** (657 in all, up from 561):
  - 25 card files;
  - eight new invariant tests, and a new case for an Ocean on Noctis City's Area;
  - `tests/rules/test_playing_cards.py::test_every_implemented_building_card_has_its_printed_production_box_as_production_data`,
    checked to fail with Geothermal Power's data blanked.

  The tests that pin behaviour already there were checked by breaking the engine check for a
  moment: Moss without its plant loss, Artificial Lake with no free land, and at 9 Oceans.
- **Fuzzer:**
  - `tiles_only_on_legal_areas` allows one Ocean on land per Artificial Lake played by anyone
    (Oceans belong to nobody).
  - The new `cities_apart` lets a Player's City lie next to at least 2 others, once per Urbanized
    Area they played. It reports the touching pairs left over after the best such choice.
  - `legal_areas` knows `"land"` and `"next_to_two_cities"`.
  - The new invariant `robotic_workforce_copies_only_your_building_cards` checks against the
    printed face.
  - In 300 random Games with the implemented cards first, Robotic Workforce was played 45 times,
    Artificial Photosynthesis 70, Urbanized Area 40 and Artificial Lake 21.
- **Checked in the browser** (1440×900, Hotseat, a Scenario with all 25 cards in hand loaded
  through a second WebSocket):
  - all 25 were offered;
  - Artificial Lake highlighted exactly the 46 free Areas reserved for nothing and drew its
    Ocean on J1, paying its steel;
  - Artificial Photosynthesis showed both Production buttons and raised energy Production by 2;
  - Robotic Workforce offered Carbonate Processing and Mine and copied the first;
  - Urbanized Area highlighted only C4, between the Cities on C3 and C5;
  - no console errors.
- **Game length and speed** (2026-10-29, on mains, charging at 72 %, "performance" profile):
  - Fuzzing: 20,000 Games with 2–5 Players and 14,298,150 Decisions in 244 s, with no failures.
    The longest Game lasted 40 Generations. After the code review's engine changes, another
    5,000 Games (3,565,431 Decisions) were also clean.
  - Benchmark: 88,459 Games/s on 16 processes and 8,499 in 1, against ticket 11's 94,472 and
    9,020. That is about 6 % down, with 25 more cards playable. Copies take 0.16, 0.51 and
    0.80 µs at the start, halfway (292 picks) and at the end (584 picks). Every target is met.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - **Glossary:** a rules note said "City spaces" ("space" is an _Avoid_ word for Area).
    `ProductionChange::Choice` became `Alternative`, since "choice" is an _Avoid_ word for
    Option.
  - **Repeated code:**
    - `can_play` built every Production Option to check for one; `can_make_a_production_change`
      stops at the first. The helper `offers_production_changes` is gone.
    - The chain `CARD_CATALOG[card].implemented_effects().production_choice[index]`, repeated
      three times, is now `Card::production_alternative`.
    - "Has a production box" is `Card::has_production_box` in Rust and
      `has_printed_production_box` in `tests/helpers.py`, shared by the fuzzer and the catalog
      test.
  - **The catalog test** moved from Robotic Workforce's file to
    `tests/rules/test_playing_cards.py`, next to the other test across the catalog.
  - **`cities_apart`** names its steps (`picks_per_player`, `left_over_with`).
  - **The spec review found rules-note claims untested**, and each got a test:
    - Robotic Workforce copies only the box (Open City) and lists every card in card-number order,
      even two with the same box (Solar Power, Power Plant);
    - Artificial Lake pays 2 MegaCredits for an adjacent Ocean, and is offered at 9 Oceans with
      no free land;
    - later Cities keep apart from Urbanized Area's;
    - Research counts twice for Scientist.
  - **Hand-offs:** the Research note named only ticket 16. Mars University (16) and Olympus
    Conference (19) now both have card-line notes.
  - The Production note now says that playability is checked before the card's other effects.
- Left as is:
  - **`Game`'s waiting fields** (`placing`, `paying_for`, `choosing_production`, `selling`) are
    separate `Option`s, so `decision()` matches a 5-tuple. One `Copy` enum for "what the Decision
    waits on" would be tidier, but it is a refactor of its own, best done when tickets 15–17 add
    more Decisions.
  - `areas_for` and `has_area_for`, and now `production_options` and
    `can_make_a_production_change`, are parallel matches kept for speed (ticket 06's note).
  - `TWO_CITIES` is written in both test files that use it, and the fuzzer's `OTHER_AREAS` repeats
    the GUI's status text. Test files and the fuzzer write their facts out on purpose.
  - The rename of `OceanAreas` was not asked for, but clippy required it.

**Open points:**
- **Scenarios** still refuse an Ocean on land, and don't check that Cities keep apart. Ticket 22
  now has both as Comments.
- **Robotic Workforce on later cards**, noted on their card lines:
  - Medical Lab's recount (13);
  - the lower panels of Space Elevator, Electro Catapult and AI Central, and the action boxes
    the catalog test must allow for (15);
  - Immigrant City (16);
  - Heat Trappers and Biomass Combustors picking a victim again (17);
  - Mining Area and Mining Rights (18);
  - Mining Guild's printed steel Production (21, in its Comments).
- **No rules test of the Production Decision on its own:** no card yet has both a choice and
  Tiles or fixed Production, so the two card files cover it.
- **Glossary:** "production box" (the brown box of Production changes on a card) is a new term,
  like "Placement" and the Area rules from ticket 11. All three are candidates for
  `/domain-modeling`.
- **Still open from ticket 08:** resource losses are checked before paying (Moss loses a plant
  and costs no steel); the Production Requirement has no test (#002 and #061, ticket 17).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

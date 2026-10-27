# 11 — Automated cards #001–#060

**What to build:** The Automated (green) cards numbered #001–#060 that weren't sorted into a mechanism batch.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (24, after Capital moved to ticket 18):**

- [x] #001 Colonizer Training Camp — done in ticket 08 (to test the central rules)
- [x] #003 Deep Well Heating — done in ticket 08 (to test the central rules)
- [ ] ~~#008 Capital~~ — moved to ticket 18 (its City is a special Tile scored by adjacent Oceans)
- [x] #016 Domed Crater — done in ticket 11
- [x] #018 Methane from Titan — done in ticket 11
- [x] #022 Black Polar Dust — done in ticket 08 (starter set)
- [x] #029 Cupola City — done in ticket 11
- [x] #030 Lunar Beam — done in ticket 11
- [x] #032 Underground City — done in ticket 11
- [x] #040 Asteroid Mining — done in ticket 11
- [x] #041 Food Factory — done in ticket 11
- [x] #042 Archaebacteria — done in ticket 08 (to test the central rules)
- [x] #043 Carbonate Processing — done in ticket 11
- [x] #045 Nuclear Power — done in ticket 08 (starter set)
- [x] #046 Lightning Harvest — done in ticket 11
- [x] #047 Algae — done in ticket 11
- [x] #048 Adapted Lichen — done in ticket 11
- [x] #051 Miranda Resort — done in ticket 11
- [x] #053 Lake Marineris — done in ticket 08 (starter set)
- [x] #055 Kelp Farming — done in ticket 11
- [x] #056 Mine — done in ticket 08 (starter set)
- [x] #057 Vesta Shipyard — done in ticket 11
- [x] #058 Beam from a Thorium Asteroid — done in ticket 11
- [x] #059 Mangrove — done in ticket 11
- [x] #060 Trees — done in ticket 08 (starter set)

## Comments

### 2026-10-27 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **Capital (#008) moved to ticket 18.** Its City is a special Tile scored by the Oceans next to it,
  which needs the card-Tile machinery ticket 18 builds (Commercial District also counts the Tiles
  next to it). The move is noted in both tickets.
- **Production per Tag and a Tile's Area rule are effect data**, each carried out in one place in
  Rust (ADR 0009), not per-card code:
  - `"production_per": {"resource": "megacredits", "steps": 1, "per": 1, "of": {"tag": "earth"}}`,
    the shape of Victory Points per Tag. Nine later cards use it; their ticket lines now say so.
  - `"tiles": [{"tile": "greenery", "on": "ocean_areas"}]` for a Tile on other Areas than usual,
    while the usual Areas stay written as `"city"`.
- **Test seams:** per-card tests through `tm_engine` in `tests/cards/test_<id>.py`, rules tests in
  `tests/rules/test_playing_cards.py`, and the fuzz invariants. There is no server test, because
  the protocol only gains an optional `"on"` in Area Option details.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Cards"):
- **Mangrove's Greenery** goes on any free Area reserved for Oceans, whether or not it is next to
  the Player's own Tiles. From then on it is a Greenery like any other: it raises Oxygen and
  Terraform Rating, collects the Area's printed bonus and 2 MegaCredits per adjacent Ocean, scores,
  counts for Gardener and Landlord, and the Player's later Greeneries may go next to it. The
  rulebook, the card text and the open-source game agree.
- **The 0 °C Ocean and Aquifer need no free-Area check** beyond "fewer than 9 placed" (the open
  point from ticket 08). Of the 12 Areas reserved for Oceans, other Tiles take at most 3
  (Mangrove, Protected Valley, Mohole Area), and Artificial Lake's Ocean goes on land. So fewer
  than 9 Oceans always leaves one free. `place_ocean`'s doc comment says so, and the fuzzer's
  `every_decision_has_an_option` would catch an Ocean with nowhere to go.
- **Production per Tag** counts once the card is played, so its own Tags count ("including this"
  on Power Grid and Satellites). Tags on played Events don't count. With nothing to count,
  Production stays as it is and the log is silent.
- **A card's City or Greenery needs an Area:** tested with Domed Crater. No v1 card places two
  Cities or two Greeneries, so the open point "as many Areas as Tiles of one kind" doesn't arise.
  A test now fails if effect data ever gives a card two.
- **The batch had 17 open cards, not 18:** the ticket already ticked 8 of its 25 as done in ticket
  08. 16 are implemented here and Capital moved.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): 14 cards use only `resources`, `production` and
  `tiles`; Miranda Resort uses `production_per`; Mangrove uses an Area rule. 39 cards are now
  implemented (the README says so).
- **Engine:**
  - `cards::ProductionPer { resource, steps, per, of: Counted }` is `Effects::production_per`,
    carried out right after the fixed Production. `Game::for_every` serves it and Victory Points
    per Tag alike.
  - `board::Placement { tile, on: Areas }`, with `Areas::Usual | OceanAreas`, is what a card's
    `tiles` list holds. Effect data writes it as `"city"` or `{"tile", "on"}` (the private
    `WrittenPlacement`; an unknown field still makes the catalog panic).
  - `Game::placing` is an `Option<Placement>`. `DecisionOption::PlaceTile { placement, area }`.
    `Board::areas_for` and `has_area_for` take a Placement. `place_ocean(on)` keeps an Ocean's
    Area rule for Artificial Lake later. A Placement is 2 bytes and `Copy`, so a Game is still a
    plain value copy.
  - Area Option details gain `"on": "ocean_areas"` when the Tile doesn't go on its usual Areas.
    The label stays "Place the Greenery on E4".
- **GUI:** the status bar says "…where to place the Greenery on an Area reserved for Oceans". A
  Greenery on an Area reserved for Oceans already draws as a Greenery.
- **`engine/tm_engine.pyi`** documents `production_per`, the `{"tile", "on"}` form and `"on"` in
  Area details.
- **Tests** (561 in all):
  - 16 card files, each covering the Requirement (or the Production that must be there to lower),
    the effect and the Victory Points;
  - `test_a_card_with_a_city_tile_is_not_offered_without_an_area_for_the_city`, which was checked
    to fail without the Area check;
  - `test_no_card_places_two_cities_or_two_greeneries_so_one_area_for_each_is_enough`;
  - in `test_mangrove.py`: the Areas offered, the placement bonus, Gardener, Landlord, the next
    Greenery's Areas and final scoring.
- **Fuzzer:**
  - `tiles_only_on_legal_areas` allows a Player one Greenery on an Area reserved for Oceans for each
    card in `GREENERY_ON_AN_OCEAN_AREA_CARDS` they played (now Mangrove).
  - `legal_areas` reads the Area Decision's `"on"`.
  - `counted()` takes an irregular plural.
  - Three new invariant tests.
- **Checked in the browser** (1440×900, Hotseat, a Scenario loaded through a second WebSocket):
  - all 16 cards were offered;
  - Mangrove highlighted exactly the 6 free Areas reserved for Oceans, with the new status text,
    and its Greenery on E4 paid the bonus and the adjacent Ocean;
  - Domed Crater's City Decision left out the Areas next to the City on C3;
  - Lunar Beam, then Miranda Resort, raised MegaCredit Production by 1 for Lunar Beam's Earth Tag;
  - no console errors.

  The Scenario stood in for "Deal the implemented cards first", since it reaches every card at
  once.
- **Game length and speed** (2026-10-27, on mains at 80 % and not charging, "performance" profile,
  unlike ticket 10's power-saver):
  - Benchmark: 94,472 Games/s on 16 processes and 9,020 in 1. Copies take 0.15, 0.48 and 0.77 µs at
    the start, halfway (276 picks) and at the end (553 picks). Every target is met.
  - Fuzzing: 20,000 Games with 2–5 Players and 14,387,024 Decisions in 236 s, with no failures. The
    longest Game lasted 39 Generations. After the code review's engine changes, another 5,000
    Games (3,594,201 Decisions) were also clean.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - **Glossary:** a rules note said "Ocean space" ("space" is an _Avoid_ word for Area).
  - **Wording:** the order of effects is worded one way everywhere ("fixed, then per Tag or Tile").
    `Counted`'s doc now covers Production. A re-wrapped paragraph was evened out.
  - **An Ocean's Area rule was dropped:** a card's Ocean always went through `place_ocean()`, losing
    `on`. `place_ocean` now takes the Areas.
  - **Duplicated code:** `amount * (count_of / per)` for Victory Points and Production is
    `Game::for_every`. The fuzzer's inline plurals use `counted()`, and its owner check runs once.
  - **Names:**
    - `area_option(**on)` became `on: str | None`;
    - `domed_crater = player(...)` became `holding_domed_crater`;
    - a shortened card label in a test was spelled out.
  - `test_mangrove.py` checked `"on"` through `offered()` instead of digging into the details.
  - **The spec review** found the Mangrove note's claims (Gardener, Landlord, the next Greenery)
    untested, and the two-Tiles rule unguarded. Both got tests.
  - **Ticket lines:** the ticket's card count; hand-off notes on the later cards that reuse
    `production_per` or an Area rule (tickets 12, 13, 17, 18).
- Left as is:
  - `areas_for` and `has_area_for` repeat one match on the Placement. `has_area_for` stops at the
    first Area and skips the Greenery's next-to-own search, which is why both exist (ticket 06's
    speed note).
  - `ProductionPer::steps` is 1 for every v1 card. It was kept because it is the shape the user
    chose, and it reads like Victory Points' `points`. `of: Counted` also accepts Card Resources
    and adjacent Tiles, which count 0 when a card is played.
  - "Greenery only on the usual Areas needs an Area" has no test of its own yet. No implemented
    card places one; the first is Plantation (#193, ticket 13).

**Open points:**
- **Scenarios** still refuse a Greenery on an Area reserved for Oceans, so they can't describe a
  position after Mangrove. Ticket 22's state editor will need it: allow one per card in
  `GREENERY_ON_AN_OCEAN_AREA_CARDS` its owner played.
- **Later cards on this machinery:**
  - Protected Valley (ticket 13) reuses `"on": "ocean_areas"` and must join the fuzzer's list;
  - Mohole Area (ticket 18) also goes on an Area reserved for Oceans;
  - Artificial Lake (ticket 12) needs an `Areas` variant for land;
  - Toll Station counts opponents' Tags and Zeppelins only Cities on Mars (ticket 17): two new
    kinds of count for `production_per`.
- **Glossary:** "Placement" and the Area rules (`Areas`) are new terms not in CONTEXT.md. They are
  candidates for `/domain-modeling`, like "discard pile" and "Research phase".
- **Still open from ticket 08:**
  - resource losses are checked before paying; no card here loses Resources;
  - the Production Requirement has no test (#002 and #061, in ticket 17).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

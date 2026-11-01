# 18 — Special Tiles and reserved Areas

**What to build:** Cards that place special Tiles or use a reserved Area (Noctis City, Phobos Space Haven, Ganymede Colony). Special Tiles count as Tiles for adjacency and Landlord as the rules say.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [x] Test: each reserved Area is used only by its card.

**Cards in this batch (14):** (it said 12 before Capital, Land Claim, Industrial Center and Restricted Area moved in)

- [x] #008 Capital — moved here from ticket 11 (2026-10-27): its City Tile is a special Tile, scored by the Oceans next to it. Its City sets off Rover Construction and Immigrant City (ticket 16), as any City does: test it.
- [x] #017 Noctis City — Its City sets off Rover Construction and Immigrant City (ticket 16), as any City does: test it.
- [x] #021 Phobos Space Haven — a City off Mars: Martian Rails (ticket 15) counts only Cities on Mars (`{"tiles_on_mars": "city"}`), so test that it leaves this one out. Rover Construction and Immigrant City (ticket 16) count every City Tile placed, off Mars too (the open-source game does), and `place_tile` already sets them off. Greenhouses and Energy Saving (ticket 17) count it, as every City in play (`{"tiles_in_play": "city"}`); Zeppelins doesn't (`{"tiles_on_mars": "city"}`): test both
- [x] #044 Natural Preserve — like every special Tile with an owner, Flooding (ticket 17) may remove 4 MegaCredits from its owner when its Ocean goes next to it (`targets::target_options` reads the Tile's owner): test it once for a special Tile
- [x] #064 Mining Area — Robotic Workforce (ticket 12) copies the Production this card's Tile gave, steel or titanium (FAQ)
- [x] #066 Land Claim — moved here from ticket 14 (2026-10-29): an Event that reserves a non-reserved Area for its Player, so only they may place a Tile there
- [x] #067 Mining Rights — Robotic Workforce (ticket 12) copies the Production this card's Tile gave, steel or titanium (FAQ)
- [x] #081 Ganymede Colony — a City off Mars: Martian Rails (ticket 15) counts only Cities on Mars (`{"tiles_on_mars": "city"}`), so test that it leaves this one out. Rover Construction and Immigrant City (ticket 16) count every City Tile placed, off Mars too, as for Phobos Space Haven
- [x] #085 Commercial District
- [x] #097 Nuclear Zone
- [x] #123 Industrial Center — moved here from ticket 15 (2026-10-31): its special Tile goes next to a City. Its action ("spend 7 MC to increase your steel production 1 step") is ticket 15's effect data, `"action": {"resources": {"megacredits": -7}, "production": {"steel": 1}}`; its production box is that action's, which Robotic Workforce doesn't copy: add it to `PRODUCTION_BOX_IN_THE_ACTION` in `tests/rules/test_playing_cards.py`
- [x] #140 Lava Flows
- [x] #142 Mohole Area — on an Area reserved for Oceans, like Mangrove's `"on": "ocean_areas"` (ticket 11)
- [x] #199 Restricted Area — moved here from ticket 15 (2026-10-31): its special Tile goes on any land. Its action ("spend 2 MC to draw a card") is ticket 15's effect data, `"action": {"resources": {"megacredits": -2}, "draw": 1}`

## Comments

### 2026-11-01 — implemented (Claude)

**Decisions made with the user** (one round of questions; both recommended options were chosen):
- **Each special Tile is drawn with its card's symbol** on a brown hex with its owner's disc, and
  its card's name in the tooltip; Capital's City gets a star over its skyline.
- **Land Claim's reservation is a marker, not a Tile**: an Area Decision ("Claim A1") on a free
  Area of Mars reserved for nothing, shown as a dashed ring in the Player's colour. From then on only
  that Player may place a Tile there, Oceans on land included; the marker counts for no adjacency,
  for Landlord or for "next to no other Tile".
- **Test seams** as in tickets 11–17, plus `tests/rules/test_reserved_areas.py`. No card moved to
  another ticket.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Special Tiles", "The Areas reserved for a card's City" and
"Land Claim"):
- **Special Tiles are effect data**: `"tiles": ["special"]`, with `"on"` for a card's own Areas
  (`"next_to_no_other_tile"`, `"next_to_a_city"`, `"volcanoes"`, `"ocean_areas"`,
  `"steel_or_titanium_bonus"`, `"steel_or_titanium_bonus_next_to_own_tile"`). The card being played
  prints its symbol on the Tile, so Capital's data is a plain `"city"` and its City is still a City
  everywhere (Mayor, Martian Rails, Rover Construction, Immigrant City, Commercial District, City
  scoring). With no restriction printed, a special Tile goes on any free land, next to a City too.
- **The reserved Areas** are `"on": "noctis_city"`, `"phobos_space_haven"` and `"ganymede_colony"`.
  Noctis City's City ignores the City rule (as printed), but later Cities keep away from it. The
  Cities off Mars count as Cities in play and for Mayor and Landlord, but not on Mars (Martian Rails,
  Zeppelins); this settles ticket 05's open point.
- **Mining Area and Mining Rights** raise the steel or titanium of their Area's bonus without a
  Decision (no Tharsis Area has both), and Robotic Workforce copies that step. They are the only
  cards here with Rust code (`card_code::MINING_AREA`, `MINING_RIGHTS`).
- **Land Claim is effect data**, `"claim_area": true`: a one-card flag rather than code, since the
  claim is a plain Area Decision. The board holds at most one claim, as there is one Land Claim.
- **Landlord** counts special Tiles and the Cities off Mars, as the open-source game's
  `Landlord.ts` does; the engine already did.
- The *Comprehensive FAQ* could not be fetched (the PDF and BoardGameGeek refuse the download), so
  the Robotic Workforce/Mining ruling rests on the ticket's citation and the open-source game.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): the 14 cards. 178 cards are now implemented: 111
  Automated, 37 Active and 30 Events (the README says so).
- **Engine:**
  - `board.rs`: `TileKind::Special`; `SpecialTile` (the ten special Tiles, each with its card index,
    checked against the catalog when it is read); `Placement::special` (filled in by
    `place_card_tile`) and `Tile::special`; new `Areas` values; `mining_resource`; `Board::area_of`;
    `Claim`, `Board::claim`, `claim_area` and `claimable_areas`. `areas_for` and `has_area_for` now
    share one per-Area check, `allows`, which also keeps other Players off a claimed Area, so
    `has_area_for` and `can_take_action_placing` take the Player.
  - `playing_cards.rs`: Victory Points count Tiles next to the card's own Tile (`count_for_card`,
    for Capital and Commercial District); `place_card_tiles` waits on `Waiting::ClaimArea`.
  - `game.rs`: `DecisionOption::ClaimArea(area)` (details `{"type": "claim_area", "area": "A1"}`,
    label "Claim A1", log "Player 1 claims A1 with Land Claim."), `is_placing` covers the claim, and
    `place_tile` takes the whole Placement and raises the Mining cards' Production.
  - Labels and the log name special Tiles: "Place the Nuclear Zone Tile on C4", "Player 1 places
    the Nuclear Zone Tile on C4."
  - The view: a Tile's `"card"` for a special Tile, an Area's `"claimed_by"`, and the Area Option's
    `"card"`. Scenarios take special Tiles, the reserved Areas' Cities, Mohole Area's Tile on an
    Ocean Area and `"land_claim"`.
- **GUI:** `MarsBoard.tsx` draws the symbols (`SPECIAL_SYMBOLS`), the claim ring and clickable
  claim Options, and names special Tiles and claims in the tooltips; the status bar names the
  special Tile and its Areas, and Land Claim's Decision.
- **`engine/tm_engine.pyi`** documents `"special"`, the new `"on"` values, `"claim_area"`,
  `{"adjacent": ...}`, the Scenario's special Tiles and `"land_claim"`, the claim Option and the
  board's `"card"` and `"claimed_by"`.
- **Tests** (1,249 in all, up from 1,146): 14 card files, each card's ticket note among them (Martian
  Rails and Zeppelins leave the Cities off Mars out, Greenhouses and Energy Saving count them; Rover
  Construction and Immigrant City set off by Capital, Noctis City, Phobos Space Haven and Ganymede
  Colony; Flooding takes from Natural Preserve's owner; Robotic Workforce copies the Mining cards;
  Industrial Center in `PRODUCTION_BOX_IN_THE_ACTION`; Capital scored by its Oceans; Land Claim);
  `tests/rules/test_reserved_areas.py` (no other Tile is offered a reserved Area, by any of 18 placing
  Actions: three Standard Projects, converting plants and 14 cards; each reserved Area's card offers only it; in 40 random Games each reserved Area
  held only its card's City and the claimed Area only its Player's Tiles); Mayor and Landlord tests;
  Scenario tests; the production-box test knows `PRODUCTION_BOX_FROM_THE_TILE`.
- **Fuzzer:** two new invariants, `each_reserved_area_used_only_by_its_card` and
  `special_tiles_where_their_cards_put_them`; `tiles_only_on_legal_areas`, `legal_areas` (the new
  Areas and claims, and Land Claim's Decision), `cities_apart` (Noctis City's City may touch
  others), card Victory Points (Tiles next to the card's Tile) and the Robotic Workforce check (not
  a box inside an action) learned the rest. This settles ticket 06's open point for ticket 18.
- **In 300 random Games with the implemented cards first** (2–5 Players), the cards were played:
  Land Claim 118, Mining Rights 92, Nuclear Zone 79, Industrial Center 73, Restricted Area 65,
  Mohole Area 59, Commercial District 58, Noctis City 57, Mining Area 57, Ganymede Colony 57, Lava
  Flows 53, Natural Preserve 52, Phobos Space Haven 35, Capital 20. Restricted Area's action was used
  301 times and Industrial Center's 203; a claimed Area was later built on by its Player 18 times;
  Robotic Workforce copied a Mining card 4 times.
- **Checked in the browser** (1440×900, Hotseat, a Scenario loaded through a second WebSocket): all
  14 cards played from the hand dock, each Area Decision highlighted only the legal Areas (the
  reserved Areas for their cards, the volcanoes for Lava Flows, and so on), the board showed each
  special Tile's symbol, Capital's star and Land Claim's ring, and the tooltips named them. No
  console errors.
- **Game length and speed** (2026-11-01, on battery, 49 % down to 21 % and discharging,
  "performance" profile, as for ticket 17):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,755,283 Decisions in 344 s, with no failures;
    the longest Game lasted 36 Generations. After the code review's fixes, another 20,000 (13,750,353
    Decisions, 309 s, longest 35 Generations), and after the speed fix a last 20,000 (13,728,804
    Decisions, 306 s, longest 36 Generations), were also clean.
  - Benchmark: 5,947 Games/s in 1 process and 60,974 on 16, against ticket 17's 6,764 and 68,478
    (and 6,873 and 71,366 for 4403a7c measured today). The Game now ends after 751 picks, against
    746. Of the gap, about 4 % is this engine's code and the rest the 14 new cards, whose Area checks
    run at every Action Decision (see the speed fix under Code review). Copies take 0.20 and 1.00 µs.
    Every target is met.
- **Card mismatch report:** 0 differences.

**Code review** (`/code-review`, standards and spec; no rules bugs found):
- Fixed:
  - "space" in the rules notes (an _Avoid_ word) became "Area"; two doc comments wider than 110
    columns, four long lines in the invariants, a short README line and a stray `,` line in Nuclear
    Zone's card entry; missing doc comments on `SpecialTile::ALL`, `Board::claim`, `Claim` and
    `LandClaim`.
  - The reserved-Areas map is one, `RESERVED_FOR_CARDS` in `tests/helpers.py`, and
    `put_special` builds on `helpers.special`.
  - **Speed** (found by the benchmark, not the reviewers): the one per-Area placement check walked
    all 63 Areas and cost about 9 % of Random Bot playouts. Measured as this engine with the 14 new
    cards' data removed, against 4403a7c in the same power state, with identical Games (746 picks):
    6,255 against 6,883 Games/s on 1 process. `board.rs` now walks only the candidate Areas (land,
    the Areas reserved for Oceans, or the cards' reserved Areas), which gave 6,584 against 6,873, a
    gap of about 4 % left for the claim check and the special-Tile plumbing.
  - The spec review asked for the reserved-Area test to cover every placement rule (it now plays
    all 14 placing cards), a board-state invariant for where special Tiles lie, and the Robotic
    Workforce invariant to refuse a box inside an action (Industrial Center).
- Left as is:
  - **The special Tile's name in three places** (`Placement::tile_name`, the log line, the
    invariant): the label says "the City", the log "a City", and the invariant must not read the
    engine.
  - **`VictoryPoints::Per` inlines `for_every`'s shape**: `for_every` counts without a card, and
    only Victory Points need the card's own Tile.
  - **The Mining cards in four places** (`mining_resource`, `card_code`, a hook in `place_tile`,
    Robotic Workforce): ADR 0009's card code, as Flooding's.
  - **`Areas::reservation()` and the arm in `allows`** name the same three values; one map would only
    move the match.
  - **`claim_area` in the effect language for one card**: a flag, recorded as a call above.
  - **`cities_apart` skips pairs with Noctis City**: the view can't tell which City came first; the
    Area Decisions are checked instead.

**Open points:**
- **Hand-offs:** ticket 20's Ecological Zone needs a `SpecialTile` value, a symbol and a placement
  rule (noted on its card line); ticket 22's state editor can describe special Tiles and Land Claim
  now, but doesn't check the Tile's card (noted in its Comments); Protected Habitats (ticket 20) must
  still leave its Player out of plant removals.
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities apart
  (ticket 22); Viral Enhancers' plant check (ticket 20); `CARDS_WITH` covers only Project Cards
  (ticket 21); "target", "taking", "Trigger", "Discount" and now "claim" are not in `CONTEXT.md`, a
  gap to settle with `/domain-modeling`.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

# 13 — Automated cards #132–#207

**What to build:** The Automated (green) cards numbered #132–#207 that weren't sorted into a mechanism batch.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (33):**

- [x] #132 Fusion Power — done in ticket 08 (to test the central rules)
- [x] #135 Advanced Ecosystems
- [x] #136 Great Dam
- [x] #137 Cartel — effect data `"production_per"` from ticket 11
- [x] #138 Strip Mine — done in ticket 08 (starter set)
- [x] #139 Wave Power — done in ticket 08 (to test the central rules)
- [x] #141 Power Plant — done in ticket 08 (starter set)
- [x] #144 Titanium Mine — done in ticket 08 (starter set)
- [x] #145 Tectonic Stress Power
- [x] #146 Nitrophilic Moss
- [x] #148 Insects — effect data `"production_per"` from ticket 11
- [x] #152 Insulation
- [x] #155 Designed Microorganisms
- [x] #158 Industrial Microbes
- [x] #159 Lichen
- [x] #164 Micro-Mills
- [x] #165 Magnetic Field Generators
- [x] #168 Windmills — done in ticket 08 (starter set)
- [x] #169 Tundra Farming
- [x] #171 Magnetic Field Dome
- [x] #174 Protected Valley — `{"tile": "greenery", "on": "ocean_areas"}` as Mangrove (ticket 11); add it to the fuzzer's `GREENERY_ON_AN_OCEAN_AREA_CARDS`
- [x] #175 Satellites — effect data `"production_per"` from ticket 11
- [x] #176 Noctis Farming
- [x] #179 Soil Factory
- [x] #180 Fuel Factory
- [x] #182 Corporate Stronghold
- [x] #186 Rad-Suits — done in ticket 08 (to test the central rules)
- [x] #193 Plantation
- [x] #196 Lagrange Observatory — done in ticket 08 (to test the central rules)
- [x] #197 Terraforming Ganymede
- [x] #203 Soletta
- [x] #205 Rad-Chem Factory — done in ticket 08 (to test the central rules)
- [x] #207 Medical Lab — effect data `"production_per"` from ticket 11; Robotic Workforce (ticket 12) recounts the building Tags when it copies this box: add that test

## Comments

### 2026-10-29 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **Insulation (#152) is Rust code** in `engine/src/card_code.rs`, like Robotic Workforce. It
  shares the Production Decision: one Option per number of steps.
- **Insulation trades 1 up to all of the heat Production.** It is not offered without heat
  Production, as in the open-source game; trading 0 would only spend the card.
- **Terraforming Ganymede (#197) is effect data:** a new field, `"terraform_rating_per": {"steps":
  1, "per": 1, "of": {"tag": "jovian"}}`, shaped like `production_per`.
- **Test seams as in tickets 11 and 12**, and no card moves: none of the 24 needs a trigger, an
  action, Card Resources or an effect on other Players.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Cards"):
- **A card's own Tags never meet its Requirements** (Advanced Ecosystems, printed with all three
  Tags it requires). A new note, "A card's own Tags and its Requirements".
- **Insulation's Options** go from the fewest steps to the most; with 1 heat Production the trade
  is made without a Decision.
- **Protected Valley's Greenery** is Mangrove's: any free Area reserved for Oceans, a Greenery like
  any other from then on. The note is now "Mangrove's and Protected Valley's Greenery".
- **Terraforming Ganymede counts its own jovian Tag**, under "Production and Terraform Rating per
  Tag" (renamed from "Production per Tag").
- **Nitrophilic Moss** is not offered with fewer than 2 plants, by the existing check on Resources
  ("Production at its limit").
- **Plantation** is the first card with a Greenery on the usual Areas; it is not offered without
  free land ("A card's City or Greenery needs an Area").
- **The batch had 24 open cards**, as the brief said: 33 listed, 9 done in ticket 08. All 24 are
  implemented here; none moved.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`):
  - 14 cards use only `resources`, `production` and `terraform_rating`. Corporate Stronghold adds
    the usual `"city"`, Plantation the usual `"greenery"`, and Advanced Ecosystems has `{}`;
  - Cartel, Insects, Satellites and Medical Lab (1 per 2 building Tags) use `production_per`;
  - Protected Valley uses `{"tile": "greenery", "on": "ocean_areas"}`, as Mangrove does;
  - Terraforming Ganymede uses the new `terraform_rating_per`;
  - Insulation has `"effects": {}` plus its Rust code.

  88 cards are now implemented, all Automated (the README says so).
- **Engine:**
  - `cards::TerraformRatingPer { steps, per, of }` and `Effects::terraform_rating_per`, carried out
    right after the fixed Terraform Rating, through the new `raise_terraform_rating_by` (which the
    fixed Terraform Rating now uses too). The order is in the `Effects` doc and the rules notes.
  - `card_code::INSULATION = 151` joins `CARDS_WITH_CODE`, with `insulation_change(steps)` and
    `Game::insulation_steps`. `ProductionChange::HeatForMegaCredits(steps)` is a third kind of
    Production change, offered by `production_options` and checked by
    `can_make_a_production_change`.
  - Option label "Raise MegaCredit Production by 2 and lower heat Production by 2" (the existing
    `production_change` text, in Resource order), details `{"type": "choose_production", "card":
    "insulation", "production": {...}}`, so the GUI needed no change.
- **`engine/tm_engine.pyi`** documents `terraform_rating_per` and names Insulation among the cards
  with Rust code.
- **Tests** (734 in all, up from 657):
  - 24 card files;
  - Medical Lab's file has `test_robotic_workforce_copying_medical_lab_counts_the_building_tags_again`
    (4 building Tags give 2 steps);
  - a new invariant test with Mangrove's and Protected Valley's Greeneries both on Ocean Areas.

  The tests that pin checks already there were checked by breaking each check for a moment: the
  Resources check (Nitrophilic Moss), the Production check (Soil Factory, Fuel Factory, Corporate
  Stronghold and both Magnetic Field cards) and the Area check (Plantation).
  `test_every_implemented_building_card_has_its_printed_production_box_as_production_data` stays
  green with the 11 new building cards.
- **Fuzzer:** `GREENERY_ON_AN_OCEAN_AREA_CARDS` gains Protected Valley. In 300 random Games with the
  implemented cards first, every new card was played (Micro-Mills 75 times, Insulation 40,
  Protected Valley 32, Terraforming Ganymede 17, Plantation 5) except Advanced Ecosystems: no card
  with an animal Tag is implemented yet (ticket 20).
- **Checked in the browser** (1440×900, Hotseat, a Scenario with all 24 cards in hand loaded through
  a second WebSocket):
  - 23 were offered, and Tundra Farming correctly not at −14 °C;
  - Insulation showed the status "…must choose how Insulation changes their Production:" and three
    buttons, and the second traded 2 steps;
  - Protected Valley highlighted the 8 free Ocean Areas;
  - Plantation then highlighted only the land next to that Greenery (D3, D4, F3, F4);
  - Terraforming Ganymede raised Terraform Rating by 1;
  - Corporate Stronghold placed its City;
  - Medical Lab counted 4 building Tags and raised MegaCredit Production by 2;
  - no console errors from the GUI.
- **Game length and speed** (2026-10-29, on mains, battery at 80 % and not charging, "performance"
  profile):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,753,003 Decisions in 228 s, with no failures. The
    longest Game lasted 36 Generations. After the code review, another 5,000 Games (3,439,872
    Decisions) were also clean.
  - Benchmark: 92,238 Games/s on 16 processes and 8,399 in 1, against ticket 12's 88,459 and 8,499.
    Copies take 0.16, 0.57 and 0.91 µs at the start, halfway (368 picks) and at the end (736
    picks). Every target is met.

**Code review** (`/code-review`, standards and spec; nothing blocking):
- Fixed:
  - ragged wrapping in the `Effects` doc, `tm_engine.pyi` and four rules notes;
  - "None is never offered" in `insulation_steps`' doc read like `Option::None`;
  - "The order of a card's effects" now says "Terraform Rating (fixed, then per Tag)", as the
    `Effects` doc does, and the per-Tag note's heading names Terraform Rating;
  - the Terraforming Ganymede test played Business Contacts as "an Event with none", which tests
    nothing (no Event has a jovian Tag), so it is gone;
  - Viral Enhancers' hand-off (below).
- Left as is:
  - **The card-id `if`s** in `production_options` and `can_make_a_production_change` now name two
    cards. They stay parallel for speed, as ticket 12 noted; a lookup table is worth it once a
    third card joins.
  - **Three matches on `ProductionChange`** (carrying it out, its label, its details) each have one
    arm per kind. A shared "Resources of this change" method would need a panicking arm for a
    copied box, while the exhaustive matches make the compiler point at every site.
  - **`TerraformRatingPer`** repeats `ProductionPer`'s `steps`, `per` and `of`. Bundling them would
    change how `production_per` is read, for one card.

**Open points:**
- **Viral Enhancers (ticket 20):** the open-source game offers Nitrophilic Moss with 1 plant, and
  Moss with none, while Viral Enhancers is in play. Its card line says so.
- **Advanced Ecosystems** can't be played in a real Game until a card with an animal Tag is
  implemented (ticket 20).
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities apart
  (ticket 22); `Game`'s waiting fields could become one enum (tickets 15–17).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

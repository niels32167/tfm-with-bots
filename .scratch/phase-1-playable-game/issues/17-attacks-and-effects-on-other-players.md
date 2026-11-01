# 17 — Attacks and effects on other Players

**What to build:** Cards that affect another Player, such as removing their Resources or lowering their Production. This brings in the choose-a-target-Player Decision, including the choices the rules allow when nobody has anything to lose.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [x] Test: a target-Player Decision offers exactly the targets the rules allow.

**Cards in this batch (23):**

- [x] #002 Asteroid Mining Consortium
- [x] #004 Cloud Seeding
- [x] #009 Asteroid
- [x] #010 Comet
- [x] #011 Big Asteroid
- [x] #039 Deimos Down
- [x] #061 Great Escarpment Consortium
- [x] #063 Mining Expedition
- [x] #080 Giant Ice Asteroid
- [x] #096 Greenhouses
- [x] #099 Toll Station — effect data `"production_per"` from ticket 11, with a new count of opponents' Tags (`{"tags_of_opponents": "space"}`)
- [x] #107 Media Archives — `"resources_per"` with a new count, `"events_played"`
- [x] #121 Sabotage
- [x] #124 Hired Raiders
- [x] #125 Hackers
- [x] #129 Zeppelins — effect data `"production_per"` from ticket 11; it counts Cities on Mars only, while `TilesInPlay` counts off Mars too
- [x] #160 Power Supply Consortium
- [x] #178 Heat Trappers — Robotic Workforce (ticket 12) copies this box, and its Player picks whose Production to lower again (FAQ)
- [x] #183 Biomass Combustors — Robotic Workforce (ticket 12) copies this box, and its Player picks whose Production to lower again (FAQ)
- [x] #188 Flooding
- [x] #189 Energy Saving — effect data `"production_per"` from ticket 11
- [x] #198 Immigration Shuttles — done in ticket 08 (to test the central rules)
- [x] #201 Energy Tapping

## Comments

### 2026-11-01 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **"Any Player" effects are effect data**: an `"any_player"` block, `{"production": {"heat": -2}}`,
  `{"remove": [{"plants": 3}]}` (Sabotage lists three alternatives) or `{"steal": [...]}` (Hired
  Raiders). Rust code only for Flooding, which takes only from the owners of Tiles next to its Ocean.
  The counting cards get two new `Counted` values.
- **The target Decision never offers an Option that only does worse**: lowering Production offers
  each opponent who can lose every step, the Player themselves only when no opponent can (without a
  Decision), and the card isn't offered with nobody; removing Resources offers each opponent with
  some, the full amount up to what they have, plus "Remove nothing", never the Player themselves and
  no partial amounts. One Option means no Decision.
- **The GUI picks the target with status-bar buttons**, like the Production Decision.
- **Test seams** as in tickets 11–16, plus `tests/rules/test_targets.py`; the Decision comes after the
  card's Tiles (Comet's Ocean can give an opponent plants through Arctic Algae) and before Mars
  University's discard. No card moved to another ticket.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Taking from any Player", "What the counting cards count"
and "Robotic Workforce"):
- **The rulebook settles the targets** (as rules.dized.com and rulespal.com quote it): any Player,
  the Player included; removing Resources may be done "partly, or not at all"; lowering Production
  "must be performed", on the Player's own if no opponent has it, or the card can't be played. The
  *Comprehensive FAQ* could not be fetched (the PDF and BoardGameGeek refuse the download).
- **The Player's own Production is checked after the card raises it** (the user's rule on
  simultaneous effects, as for Immigrant City): Hackers is playable at −5 MegaCredit Production when
  no opponent is at −3 or more, and Energy Tapping and Power Supply Consortium with nobody having
  energy Production. The open-source game refuses these few positions.
- **Mining Expedition's "Remove 2 plants"** is up to 2, or none, as every red-bordered removal.
- **Flooding** removes up to 4 MegaCredits from an opponent who owns a Tile next to its Ocean and
  has some; once 9 Oceans are placed, nothing.
- **Robotic Workforce** copying Heat Trappers or Biomass Combustors raises the Player's energy
  Production and asks for a target again; the box is offered only while someone can lose it.
- **Counting cards**: Toll Station counts opponents' space Tags (none on Events); Media Archives
  every Event played by anyone; Greenhouses and Energy Saving every City in play; Zeppelins Cities
  on Mars only (`Counted::TilesOnMars`, as the card line asked).
- **No fifth `{n, per, of}` shape** came: Toll Station and Energy Saving use `"production_per"`, so
  the shared-type refactor stays left as is.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): the 22 cards. 164 cards are now implemented: 101
  Automated, 35 Active and 28 Events (the README says so).
- **Engine:**
  - `cards::AnyPlayer` (an enum: `Production`, `Remove`, `Steal`) on `Effects::any_player`;
    `Effects::any_player_production` is part of the production box (`has_production_box`, Robotic
    Workforce). `Counted::TagsOfOpponents(tag)` ("tags_of_opponents") and `Counted::EventsPlayed`
    ("events_played"). `Resources::is_zero`.
  - New `targets.rs`: `Targeting { card, next_to }`, `Taking`, `someone_can_lose_production` (read
    by `can_carry_out` and Robotic Workforce's `copyable_production_boxes`), `target_options`,
    `offer_target` (from `finish_unless_placing`, after the Tiles and before the discard),
    `taking`, `take_from`, `take_as_picked`, `remove_nothing`, `opponents`.
  - `Game::targeting` holds the taking due; `play_card` sets it (except for Flooding), and so does
    `copy_production_box`. `card_code::FLOODING` sets it from `place_tile` with its Ocean's Area
    (`take_next_to_floodings_ocean`).
  - New `Waiting::Target`, `DecisionKind::Target` ("target"), `DecisionOption::Target { card,
    player, alternative }` and `RemoveNothing(card)`. Details `lower_production`,
    `remove_resources` (with `stolen`) and `remove_nothing`; labels "Lower Player 2's heat
    Production by 2", "Remove 3 plants from Player 2", "Steal 2 steel from Player 2", "Remove
    nothing" / "Steal nothing". Log lines "Player 1 lowers Player 3's heat Production by 2." (or
    "their own"), "Player 1 removes 3 plants from Player 2.", "Player 1 steals 2 steel from Player
    2.", "Player 1 removes nothing with Asteroid."
  - `view::label` and `details` now take the Game and the deciding Player, as the takings need
    the target's Resources.
- **GUI:** the status bar's text for the target Decision ("Player 1 must choose whose Production
  Heat Trappers lowers:", "… may choose whom Sabotage removes Resources from:"); the Options are its
  buttons.
- **`engine/tm_engine.pyi`** documents `"any_player"`, the two counts and the "target" Decision.
- **Tests** (1,146 in all, up from 1,053): 22 card files; `tests/rules/test_targets.py` (exactly
  the opponents who can lose every step; the Player's own only without one; not offered with
  nobody; the full amount up to what each has, plus Remove nothing; no Decision with nobody to take
  from; after the Tiles; for the Player who played the card), checked by breaking the playability
  check for a moment; four invariant tests; the production-box test knows `any_player`.
- **Fuzzer:** a new invariant, `targets_offered_are_those_the_rules_allow`, with the printed takings
  written out (`PRODUCTION_TAKEN`, `RESOURCES_TAKEN`); for Flooding it checks only that the targets
  are among those allowed, as the view doesn't say where its Ocean went.
- **In 300 random Games with the implemented cards first** (2–5 Players), the cards were played
  (target Decisions in brackets): Sabotage 119 (118), Energy Tapping 115 (64), Hired Raiders 112
  (112), Greenhouses 98, Hackers 80 (66), Media Archives 79, Flooding 79 (8), Toll Station 72,
  Asteroid 71 (63), Energy Saving 66, Heat Trappers 60 (14), Mining Expedition 59 (50), Comet 51
  (45), Cloud Seeding 49 (21), Biomass Combustors 44 (13), Big Asteroid 36 (33), Zeppelins 30,
  Deimos Down 28 (27), Giant Ice Asteroid 28 (27), Power Supply Consortium 24 (18), Asteroid Mining
  Consortium 15 (0), Great Escarpment Consortium 14 (0). A Player lowered their own Production 56
  times and removed nothing 153 times. The two Consortiums never had two opponents with the
  Production at once; their scenario tests cover the Decision.
- **Checked in the browser** (1440×900, Hotseat, a Scenario loaded through a second WebSocket):
  Heat Trappers offered Players 2 and 3; Sabotage listed each opponent's steel, titanium and
  MegaCredits up to what they had, then Remove nothing; Hired Raiders "Steal …"; Comet's Ocean set
  off Player 2's Arctic Algae before the removal (3 of 7 plants offered); Flooding on A2 offered only
  the owners of A1 and B3; Asteroid Mining Consortium took from the only opponent without a
  Decision; Toll Station counted an opponent's space Tag. No console errors.
- **Game length and speed** (2026-11-01, on battery, 53–44 % and discharging, "performance"
  profile; ticket 16's numbers were on mains):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,612,144 Decisions in 261 s, with no failures;
    the longest Game lasted 35 Generations.
    After the code review's engine changes, another 20,000 Games (13,571,858 Decisions, 255 s,
    longest 35 Generations) were also clean.
  - Benchmark: 68,478 Games/s on 16 processes and 6,764 in 1, against ticket 16's 69,186 and 7,169.
    The Game now ends after 746 picks, against 690, so picks per second rose a little; the extra
    cards (Asteroid-style Events, Sabotage) lengthen Games rather than slow each pick. Copies take
    0.25, 0.75 and 0.99 µs. Every target is met.
- **Card mismatch report:** 0 differences.

**Code review** (`/code-review`, standards and spec; nothing blocking, no rules bugs found):
- Fixed:
  - Wrong docs: `offer_target` and the pyi said one *target* means no Decision, but a removal always
    adds "Remove nothing" (now "one Option"); the rules notes counted 21 card files; two lines were
    wrapped too wide.
  - Names: `TakeNothing`, `TookNothing` and `take_nothing` became `RemoveNothing`,
    `RemovedNothing` and `remove_nothing`, after the "remove_nothing" details.
  - `AnyPlayer` became an enum (the same JSON), so "one of the three" is enforced and the
    production-or-removal `if`s became matches; `removals()` and its tuple went.
  - `someone_can_lose_production` lost its redundant `own` parameter; `TagsOfOpponents` uses
    `opponents`; `Resources::is_zero` replaced the `!= Resources::default()` comparisons in the new
    code.
  - The invariant's set arithmetic for `stolen` is a plain `any`.
  - The spec review asked for Energy Tapping's own test with nobody having energy Production.
- Left as is:
  - **Flooding in four places** (`place_tile`, `play_card`, `card_code`, the invariant): ADR 0009's
    card code, as Immigrant City's; the card id in generic code was left as is in ticket 16 too.
  - **`(card, target, alternative)` travelling together**: an Option is a plain `Copy` value, and a
    struct would only rename the three fields.
  - **"their own" / "your own"**: the log and the label word it differently, so there is nothing to
    share.
  - **The Flooding invariant checks a subset**: the view doesn't name the Area of its Ocean;
    `tests/cards/test_flooding.py` checks the adjacency.
  - **Zeppelins' "on Mars only"** can't be told apart until ticket 18 adds Cities off Mars; its card
    line asks for that test.
- **Glossary:** "target" and "taking" are new domain terms not in `CONTEXT.md`, as "Trigger" and
  "Discount" from ticket 16: a gap to settle with `/domain-modeling`.

**Open points:**
- **Hand-offs** are on the card lines of tickets 18 (Phobos Space Haven: Greenhouses and Energy
  Saving count it, Zeppelins doesn't; Natural Preserve: Flooding takes from a special Tile's owner),
  19 (Ants can share the target Decision) and 20 (Predators and Virus can share it; Protected
  Habitats must leave its Player out of plant removals, and the invariant must know it).
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities
  apart (ticket 22); Viral Enhancers' plant check (ticket 20); Martian Rails must leave out the
  Cities off Mars (ticket 18); `CARDS_WITH` covers only Project Cards (ticket 21).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

# 15 — Active cards with actions

**What to build:** Active (blue) cards whose text is an action. Using a card's action becomes an Action, available once per Generation for each card; the GUI shows which actions have been used this Generation.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [x] Test: each card's action can be used only once per Generation, and becomes available again in the next one.

**Cards in this batch (20):**

- [x] #006 Inventors' Guild
- [x] #007 Martian Rails
- [x] #012 Water Import from Europa
- [x] #013 Space Elevator — Robotic Workforce (ticket 12) copies its lower panel's production box, so keep that box as `production` data
- [x] #014 Development Center
- [x] #015 Equatorial Magnetizer — its production box is part of its action, which Robotic Workforce (ticket 12) doesn't copy: narrow `test_every_implemented_building_card_has_its_printed_production_box_as_production_data` for it
- [x] #069 Electro Catapult — Robotic Workforce (ticket 12) copies its lower panel's production box, so keep that box as `production` data
- [x] #076 Space Mirrors
- [x] #101 Ironworks
- [x] #103 Steelworks
- [x] #104 Ore Processor
- [x] #110 Business Network
- [ ] #123 Industrial Center — moved to ticket 18 (2026-10-31): it places a special Tile next to a City. Its production box is part of its action, which Robotic Workforce (ticket 12) doesn't copy
- [x] #154 Caretaker Contract
- [x] #177 Water Splitting Plant
- [x] #187 Aquifer Pumping
- [x] #194 Power Infrastructure
- [ ] #199 Restricted Area — moved to ticket 18 (2026-10-31): it places a special Tile
- [x] #202 Underground Detonations — its production box is part of its action, which Robotic Workforce (ticket 12) doesn't copy: narrow `test_every_implemented_building_card_has_its_printed_production_box_as_production_data` for it
- [x] #208 AI Central — Robotic Workforce (ticket 12) copies its lower panel's production box, so keep that box as `production` data

## Comments

### 2026-10-31 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **Actions are effect data**: an `"action"` block on a card's `"effects"`, in the same shapes as
  its play effects, with the action's cost as Resources lost (Ironworks: `{"resources":
  {"energy": -4, "steel": 1}, "oxygen": 1}`). New forms: `pay` (MegaCredits that steel or
  titanium may pay), `resources_per` (Martian Rails), `resources_choice` (Electro Catapult) and a
  `buy` count on `look_at` (Inventors' Guild, Business Network). Only Power Infrastructure's "any
  amount" is Rust code.
- **The waiting fields became one enum first**, as its own commit (923b55f) that changed no
  behaviour.
- **The GUI offers actions on the played cards**: outlined and clicked to use, as hand cards are;
  a card whose action is used this Generation is dimmed and marked "Used", for every Player.
- **Two cards move to ticket 18**, noted on both tickets: Industrial Center (#123) and Restricted
  Area (#199) place special Tiles. Their action data is written out on ticket 18's card lines.
- **Test seams** as in tickets 11–14, plus a rules file for card actions, an engine view test and
  a server test.

**Calls made by Claude** (on the user's instruction to make the remaining calls without asking;
recorded in `docs/rules-notes.md` under "Cards"):
- **"Card actions"**: usable once per Generation from the Generation the card is played, by its
  own Player only; offered after the cards to play, in card-number order; one of the Turn's two
  Actions, ending once its Tile is placed; offered only if it can be carried out in full. Every
  action is unused again after the Production phase, which ends the Generation, so the next
  Research phase shows none used.
- **"Actions that raise a Global Parameter at its maximum"** stay open, as Asteroid and Aquifer do
  (the rulebook: "You may still play cards and actions that increase the parameter").
- **"Paying for an action with steel or titanium"**: Water Import from Europa and Aquifer Pumping
  share the card payment Decision (details with `"action": true`).
- **"A Resource change to choose for an action"**: Electro Catapult asks only with both a plant and
  a steel; Power Infrastructure offers 1 up to all of its Player's energy, fewest first.
- **"Buying the card looked at"**: 3 MegaCredits, or Done to discard; with fewer than 3
  MegaCredits the card is discarded without a Decision; hidden from the other Players.
- **"Martian Rails' Cities on Mars"**: everyone's Cities on Mars, not those off Mars (ticket 18).
- **Robotic Workforce** copies Space Elevator's, Electro Catapult's and AI Central's printed box,
  and not Equatorial Magnetizer's or Underground Detonations', which are their action's (added to
  the "Robotic Workforce" note).

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): 18 cards, each with an `"action"` block; Space
  Elevator, Electro Catapult, AI Central and Business Network also keep their play effects
  (`production`). Power Infrastructure has `"action": {}` plus its Rust code. 123 cards are now
  implemented, 88 Automated, 18 Active and 17 Events (the README says so).
- **Engine:**
  - `Game::waiting: Option<Waiting>` replaced the five waiting fields (commit 923b55f), set
    through `wait_on`, which asserts that nothing sets up a second Decision while one waits.
    `place` and `is_placing` stand for the old `placing` field. New variants:
    `Waiting::ActionPayment(card)` and `Waiting::Resources(card)`.
  - `engine/src/card_actions.rs` holds the rules: `usable_actions`, `use_action`,
    `carry_out_action` (payment, then `carry_out`, then `look_at_cards`, then the Resource
    change, then `finish_card_action`'s Tile), and `ResourceChange { Alternative,
    EnergyForMegaCredits }`.
  - `Player::used_actions: CardSet`, cleared in the Production phase.
  - `cards::Effects` gains `pay: Option<ActionCost>`, `resources_per: Option<ResourcesPer>`,
    `resources_choice: Vec<Resources>` and `action: Option<Box<Effects>>`; `LookAt` gains `buy`;
    `Counted::TilesOnMars` and `Board::on_mars` count Martian Rails' Cities.
  - `Keeping` gains `price` (0, or the card price to buy) and `for_action`, so `finish_keeping`
    ends the action or carries on with the card's Production change.
  - Shared helpers: `usable_cubes`/`spendable` (cards and actions), `ways_to_pay`, `pay`,
    `change_resources` and `place_card_tile`.
  - `card_code::POWER_INFRASTRUCTURE = 193` joins `CARDS_WITH_CODE`, with
    `energy_for_megacredits`.
  - Decisions and Options: `DecisionOption::UseAction` ("Use the action of Space Elevator",
    `{"type": "use_action", "card": ...}`), `PayForAction` (the "payment" kind, details with
    `"action": true`), `ChangeResources` (a new "resources" kind, "Spend 1 plant to gain 7
    MegaCredits", `{"type": "choose_resources", "card", "resources"}`), and `BuyCard`/`Done` in a
    "keep_cards" Decision for buying. Log lines "Player 1 uses the action of X.", "Player 1 pays
    …", "Player 1 buys 1 card for 3 MegaCredits and discards 0." / "buys none of them and
    discards 1.", and "looks at the top card of the deck."
  - Views: `PlayerBoard.used_actions` (everyone's) and `KeepingView.price`.
- **GUI:** `PlayedCards` outlines each card whose action is offered and picks it on a click; a
  used card is dimmed with a "Used" badge at its top, between cost and Tags, in view when the
  cards overlap; the card whose action is under way gets the dashed outline. The status bar names
  the action being paid for, the Resource change and the card to buy, and its hint lists "played
  card's action". The buying panel shows the card to buy, with a "Bought" strip.
- **`engine/tm_engine.pyi`** documents the action block, the new forms, the "resources" Decision,
  `use_action`, the action payment, buying, `used_actions` and `price`.
- **Tests** (923 in all, up from 791): 18 card files; `tests/rules/test_card_actions.py`
  (offering, once per Generation, available again in the next, for every card with an action,
  checked by breaking the used mark for a moment; catalog shape); two view tests; two server tests
  (`tests/server/test_card_actions.py`); four invariant tests. The production-box test now names
  the two cards whose box is their action's (`PRODUCTION_BOX_IN_THE_ACTION`).
- **Fuzzer:** a new invariant, `card_actions_used_once_per_generation`: used actions are the
  Player's own played cards with an action, only in the Action phase, and never offered again. In
  300 random Games with the implemented cards first, every card's action was used (Business
  Network 523 times, Power Infrastructure 481, Space Mirrors 410, Inventors' Guild 408, Equatorial
  Magnetizer 405, Development Center 399, Underground Detonations 279, Martian Rails 277,
  Ironworks 179, Aquifer Pumping 172, Electro Catapult 155, Water Splitting Plant 154, Ore
  Processor 132, Steelworks 122, Water Import from Europa 90, Space Elevator 59, Caretaker
  Contract 55) except AI Central's: it was never played, as no Player had 3 science Tags in play,
  the card in hand and energy Production to lower at once (15 science Tags are implemented).
- **Checked in the browser** (1440×900, Hotseat, a Scenario with all 18 played, loaded through a
  second WebSocket): all 18 actions were offered on the played cards; Electro Catapult asked plant
  or steel; Water Import from Europa's payment picker stepped titanium and paid 9 + 1, then
  highlighted the Ocean Areas; Inventors' Guild showed its card to buy with "Buy" and Done, and
  the card went into the hand; Power Infrastructure offered 1 to 10 energy; the used cards showed
  "Used". Two GUI bugs were found and fixed there: the badge escaped its card while the card's
  payment was pending, and it covered the title. No console errors once vite reloaded App.tsx.
- **Game length and speed** (2026-10-31, on mains, battery at 80 % and not charging, "performance"
  profile):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,588,258 Decisions in 225 s, with no failures;
    the longest Game lasted 38 Generations. After the code review's engine changes, another
    20,000 Games (13,610,682 Decisions, 225 s, longest 37 Generations) were also clean.
  - Benchmark: 82,567 Games/s on 16 processes after the review (81,647 before it) and 7,665 in 1
    (before it; the rerun's line was cut off), against ticket 14's 88,196 and 8,580. Games are
    longer now, since actions add picks: the benchmark's Game ends after 789 picks, against 692.
    Copies take 0.18, 0.62 and 1.00 µs at the start, halfway (394 picks) and at the end. Every
    target is met.

**Code review** (`/code-review`, standards and spec; nothing blocking):
- Fixed:
  - **Glossary**: "choice" is an _Avoid_ word for Option, so `ActionChoice`, `ChooseForAction`
    and the "action_choice" Decision became `ResourceChange`, `ChangeResources` and "resources",
    after `ProductionChange` and the "production" Decision; `Keeping::is_a_choice` became
    `needs_a_decision`. The data field keeps the name `resources_choice`, after
    `production_choice`.
  - An inaccurate doc (`can_make_a_resource_change`), a circular one (`ways_to_pay`), missing docs
    (`action_payments`, `can_buy_one_more`, `ActionCost`'s fields), `TilesOnMars` naming only one
    City off Mars, and `tm_engine.pyi` naming only Inventors' Guild for the price.
  - Duplicated code: one `usable_cubes`/`spendable` for cards and actions, and one
    `place_card_tile` for a card's Tiles and an action's.
  - "looks at the top 1 card" now reads "looks at the top card".
  - The card whose action is under way has its own GUI class, `action-under-way`.
  - The spec review asked for the once-per-Generation test over every card with an action (now
    parametrized), the production-box test narrowed to the two cards by name, and a Business
    Network Done test; the rules notes now say what Inventors' Guild does with both piles empty.
  - `test_electro_catapult.py` built a Scenario dict by hand; it uses `player(megacredits=9, …)`.
- Left as is:
  - **Keeping by price**: `price == 0` means keep and a price means buy, read in a few places
    (`Keeping::options`, `needs_a_decision`, the log, the GUI). The price is data the payment,
    the view and the GUI need anyway; an enum would add a second field saying the same.
  - **`BuyCard` and `Done`** mean different things by what the Game waits on, as `Done` already
    did for Sell Patents and the final Greenery conversion.
  - **`ResourcesPer`** is a fourth `{n, per, of}` shape. Sharing one would change how the other
    three are written in cards.json; worth it if a fifth comes.
  - **`resource_change_options` / `can_make_a_resource_change`** stay a parallel pair for speed,
    like the Production pair.
  - **`OptionDetails::Payment`'s `action` flag**: one Decision kind for both payments keeps the
    GUI's payment picker as it is.
  - **The recursive `Effects::action`**: the user's choice; tests check that only Active cards
    have one, that no action nests another, and that only actions have `pay` or
    `resources_choice`.
  - **Commit 923b55f** said it changed no behaviour; it also added `wait_on`'s assert, which no
    position reaches (the fuzzer runs with it).
  - Ticket 18's notes on Phobos Space Haven and Ganymede Colony (Martian Rails) go beyond the two
    moves, as a hand-off.

**Open points:**
- **Moved cards**: Industrial Center and Restricted Area wait on ticket 18, with their action data
  on its card lines; Industrial Center joins `PRODUCTION_BOX_IN_THE_ACTION`.
- **Martian Rails** must leave out the Cities off Mars once ticket 18 adds them (its card lines
  say so).
- **AI Central** was never played in random Games; its scenario tests cover it.
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities
  apart (ticket 22); Viral Enhancers' plant check (ticket 20).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done"
  label.

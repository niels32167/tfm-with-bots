# 08 — Playing Project Cards (starter set)

**What to build:** The machinery every card batch builds on, proven with a starter set of 11 simple Automated cards:
- #022 Black Polar Dust
- #045 Nuclear Power
- #053 Lake Marineris
- #056 Mine
- #060 Trees
- #087 Grass
- #113 Solar Power
- #138 Strip Mine
- #141 Power Plant
- #144 Titanium Mine
- #168 Windmills

This ticket covers:
- **Playing a card.** "Play a Project Card" becomes an Action, offered only when the Player meets the card's Requirements and can pay.
- **Payment Decision.** One Option per distinct legal split between MegaCredits, steel (2 each, for cards with a building Tag) and titanium (3 each, for cards with a space Tag). The GUI shows these as a payment picker.
- **Effect data (ADR 0009).** Primitives: gain or lose Resources, change Production, place a Tile, raise a Global Parameter, draw cards, gain Terraform Rating.
- **Central rules.** Requirement checks (Global Parameter minimums and maximums, Tag counts, Production) and Tag counting live in one central place.
- **Scoring.** Victory Points printed on cards count in final scoring.
- **Deck.** There is now a deck: placement bonuses that draw cards take effect. Until ticket 09, a new Game simply deals each Player a few cards so the starter set can be played in the GUI.
- **GUI.** It shows the hand and each Player's played cards, grouped by type.

**Blocked by:** 04 — Resources, Production and the end of the Game; 07 — Card import and card gallery

**Status:** ready-for-agent

- [x] A card is offered only when it is legal to play: its Requirements are met and it is affordable with the allowed Resources.
- [x] Payment Options cover every legal split, and the GUI payment picker uses them.
- [x] Each starter-set card has a scenario test covering its Requirements, its effect and its Victory Points.
- [x] Scenarios can put specific cards in a Player's hand and among their played cards.
- [x] Scenario tests now cover Builder, Planner and Scientist (ticket 05).
- [x] A coverage check lists every catalog card without a scenario test. It only reports for now; ticket 24 makes it fail on gaps.
- [x] Card-draw placement bonuses work.
- [x] Final scoring includes card Victory Points.

## Comments

### 2026-10-23 — implemented (Claude)

**Decisions made with the user** (three rounds of questions; every recommended option was
chosen, and the user then asked Claude to make the remaining calls without asking):
- **Effect data** is one `"effects"` object per card in `engine/cards/cards.json`, keyed by
  primitive: `resources` and `production` (the Resources shape, below zero to lose),
  `temperature` and `oxygen` (steps), `terraform_rating`, `draw` and `tiles` (a list). They
  are carried out in that fixed order, Tiles last. A card is implemented once it has
  `"effects"` (`{}` for one with no effect, or later all Rust code); a card without it is
  never offered. Rust: `cards::Effects`, `Card::effects: Option<Effects>`.
- **Card state:** a card is its catalog index (a Project Card's number minus 1). The deck is
  a fixed 208-byte array plus its size (`deck::Deck`, top card last); each Player's hand and
  played cards are 256-bit sets (`card_set::CardSet`), in card-number order. A Game stays a
  plain value copy and nothing depends on hash-map order.
- **Payment:** a `"payment"` Decision comes only when there is more than one way to pay. It
  offers one Option per split, the most MegaCredits first, leaving out splits with a steel or
  titanium cube the others make unneeded. Details: `{"type": "payment", "card": "mine",
  "megacredits": 2, "steel": 1, "titanium": 0}`. The GUI shows steel and titanium steppers
  that reach only offered splits.
- **Event Tags:** no Tag on a played Event counts, the Event Tag included (rulebook: Events lie
  face down; the open-source game gives the same results).
- **Scenarios:** `players[i].hand` and `players[i].played_cards` list catalog ids, and a
  top-level `"deck"` puts cards on top in drawing order, with every other Project Card shuffled
  beneath them, so all 208 are always somewhere. Option details and Replays name cards by id
  (`{"type": "play_card", "card": "mine", "cost": 4}`).
- **The deal until ticket 09:** the 11 starter-set cards are shuffled and dealt round-robin
  from the first player; every other Project Card goes into the deck.
- **GUI:** the hand and played cards sit below the board (the page scrolls). Played cards are
  grouped Automated / Active / Events, and player boards show hand size and Tag counts.
- **The tie for the win** stays MegaCredits only.
- **Test seams:** `tm_engine` throughout (`tests/cards/test_<id>.py` per card, `tests/rules/`,
  `tests/engine/`), the fuzz invariants, and one server test. The coverage check counts a
  card as tested once it has its own test file.

**Calls made by Claude** (recorded in `docs/rules-notes.md`):
- **12 cards beyond the starter set**, data only, so every central rule is tested through a
  real card. Each is marked done in its own ticket:
  - Solar Wind Power: titanium;
  - Colonizer Training Camp and Archaebacteria: Oxygen and Temperature maximums;
  - Wave Power and Dust Seals: Ocean minimum and maximum;
  - Fusion Power: a Tag Requirement;
  - Rad-Suits: a Tiles Requirement;
  - Deep Well Heating: a Temperature step;
  - Rad-Chem Factory: Terraform Rating;
  - Lagrange Observatory: drawing a card;
  - Io Mining Industries and Immigration Shuttles: Victory Points per Tag and per Cities in play.
- **A card is not offered** if it would take its Player's own Production below its limit or
  their Resources below 0, or if one of its Tiles has no Area (an Ocean always has one, as
  with Aquifer).
- **A card's Oceans once 9 are placed:** the card can still be played, and places what is left.
- **The order of a card's effects** is fixed. A Tile from a track bonus (the 0 °C Ocean) comes
  before the card's own Tiles, and Strip Mine's second Oxygen step comes before that Ocean;
  every order gives the same outcome for these cards.
- **An empty deck** draws nothing, and the log says so, until ticket 09 reshuffles the
  discard pile.

**Design notes:**
- **Engine:**
  - `engine/src/playing_cards.rs` holds the central card rules as one place, an `impl Game`:
    - Tag counting (`tags`) and Requirements (`meets`);
    - whether a card can be played (`can_play`) and how it can be paid for (`payments`);
    - playing a card, carrying out its effects, placing its Tiles one at a time
      (`placing_for: Option<CardTiles>`), drawing, and card Victory Points (fixed, per Tag,
      per Tiles in play; Card Resources and Tiles of cards count 0 until tickets 19 and 18).
  - Builder counts building Tags in play, Planner cards in hand, Scientist science Tags in play.
  - The play flow is: `PlayCard(card)`, then `Pay { card, payment }` (only with a choice), then
    the effects, then `finish_unless_placing()`, which now also starts the card's next Tile.
    The card stays in the hand until it is paid for, so the card count holds throughout.
  - Card placement bonuses draw from the deck. The log says "Player 1 draws 2 cards from the
    placement bonus." and never names the cards.
  - New log lines:
    - "Player 1 plays Mine, paying 2 MegaCredits and 1 steel.";
    - "… gains 1 plant." and "… loses …";
    - "… lowers their MegaCredit Production by 2.";
    - "… raises their Terraform Rating by 2.";
    - "… draws 1 card.".
- **View:**
  - Each player board has `hand_size`, `hand` (null except in the viewer's own board and in the
    full view), `played_cards` and `tags` (the ten Tags that count).
  - The view has `deck_size`, and `deck` (top first) in the full view only.
- **Tests:**
  - 23 card files in `tests/cards/`.
  - `tests/rules/test_deck.py`, `test_payment.py`, `test_playing_cards.py` and `test_tags.py`.
  - Builder, Planner (it stays claimed after the hand shrinks) and Scientist tests.
  - Cards in the Scenario Replay test, and the server test of hidden hands.
  - New helpers: `hand()`, `played_cards()`, `final_scores()`, `index_of()`, `PROJECT_CARDS`
    and `TAGS_THAT_COUNT`.
- **Fuzzer:**
  - `every_card_in_exactly_one_place` (deck, hands, played cards, and sizes that agree) runs after
    every Decision.
  - The `cards` score part is checked against the played cards' printed Victory Points,
    worked out in Python from the catalog.
- **Coverage report:** `uv run python -m tools.card_coverage` lists the 197 cards still without
  a test file. The suite shows the count as a warning, and ticket 24 makes it fail.
- **GUI:**
  - `gui/src/cards/PlayerCards.tsx`:
    - playable cards are outlined and clicked to play;
    - the card being paid for has a dashed outline;
    - cards not implemented yet are dimmed;
    - played cards overlap so each shows its cost, title and Tags;
    - hovering enlarges any card.
  - `gui/src/components/PaymentPicker.tsx` is the picker.
  - Player boards show "Hand n" and Tag icons with counts.
  - The status bar leaves out the play-card buttons and says "or click a highlighted card in
    the hand".
- **Benchmark** (2026-10-23, on battery, power-saver):
  - 104,153 Games/s on 16 processes and 5,544 in 1;
  - copies take 0.19, 0.38 and 0.65 µs.

  Ticket 06 measured 124k–130k Games/s on battery, so this is within power-saver's swings. A
  2-player Game is still about 190 Decisions, since few cards are playable yet.
- **Fuzzing:** 20,000 Games and 3,933,341 Decisions in 75 s, no failures. The longest Game
  lasted 27 Generations.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - a card with a City or Greenery Tile could have been offered with no legal Area.
    `can_carry_out` now checks each Tile with `can_take_action_placing`. Its first test comes
    with ticket 11's Domed Crater;
  - duplicated lookups became `Card::project_cost()` and `Card::implemented_effects()`;
  - the test lists of Project Cards and Tags moved to `tests/helpers.py`;
  - the GUI's card-being-paid-for lookup became one shared helper, and the status bar's
    "disabled" now comes from `App.tsx`'s `picking`;
  - names:
    - `counted` became `count_of`;
    - `held` became `own` or `resources`;
    - `held_cards` became `cards_outside_the_deck`;
    - `place_cards` became `cards_named` ("place" means Tiles);
    - `ResourcesChanged` became `ResourceChanged`;
    - a `printed` that shadowed `board::printed` was renamed;
  - `(usize, usize)` became `CardTiles { card, placed }`;
  - `Payment` is flattened into the Option details, so its fields aren't listed twice;
  - a stale scoring docstring, the import order in `view.rs`, and "undefined MegaCredits"
    in the status text;
  - the 12 extra cards are marked done in tickets 11, 12, 13 and 17.
- Left as is:
  - `can_play` sums what the Player can spend instead of calling `payments`, which allocates.
    It is asked for every card in hand at every Action Decision, and a doc comment says why.
  - The pending-Decision fields (`placing`, `paying_for`, `placing_for`, `waiting_bonus`) and
    the growing `match` in `decision()` were left as is, as in ticket 04.
  - `game.rs` and `playing_cards.rs` call each other through `pub(crate)` methods. Both are
    `impl Game`, split by topic.
  - `{megacredits, steel, titanium}` also appears as the GUI's `Split` type.

**Open points:**
- **The Production Requirement** is checked in `meets` but has no test. The first cards with
  one are #002 Asteroid Mining Consortium and #061 Great Escarpment Consortium, both attacks
  (tickets 11/17).
- **Resource losses** are checked against what a Player holds before they pay. A future data
  card that both costs steel or titanium and loses some must check what is left after paying.
- **Ticket 09:**
  - replace the starter-set deal (`STARTER_SET` in `game.rs`, and its rules note);
  - add the discard pile to `CardSet`s and to `every_card_in_exactly_one_place`;
  - reshuffle the discard pile when the deck runs out (and drop that rules note).
- **Ticket 11 onwards:**
  - cards with City or Greenery Tiles need the legal-Area test above;
  - a card with two Tiles of one kind needs as many Areas, not just one.
- **Ticket 16:** an Event's Tags count while it is being played; `tags()` doesn't cover that
  moment.
- **Ticket 23:**
  - the hand starts just below the fold at 1440×900;
  - the status bar wraps to two lines at 1440 px.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no
  "done" label.

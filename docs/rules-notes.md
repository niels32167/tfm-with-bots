# Rules notes

Every rules judgment call the engine makes, so play can be checked against the agreed
interpretation. The order of authority is: the official rulebook, then the official
FryxGames FAQ and corrections, then the open-source game
(terraforming-mars/terraforming-mars) as tiebreaker (ADR 0001).

Each note gives the call, the sources behind it, and the tests that pin it down.

## Standard Projects and conversions

### Asteroid at maximum Temperature

**Call:** The Asteroid Standard Project is still offered when Temperature is at +8 °C.
The Player pays 14 MegaCredits; Temperature and Terraform Rating stay as they are.

**Why:**
- Rulebook, on Global Parameters at their goal: "You may still play cards and actions
  that increase the parameter", ignoring that part of the effect. A Standard Project is
  an Action.
- The community-compiled *Terraforming Mars Comprehensive FAQ* (v1.7) answers this exact
  question the same way, for Asteroid at maximum Temperature and Aquifer with no Oceans
  left: you may pay, and get nothing. It is not an official FryxGames document, so it
  only confirms the rulebook reading.
- The open-source game agrees: its Asteroid Standard Project stays usable and only shows
  a "max temperature" warning.

Ticket 01 first said Asteroid would not be offered; the user chose to follow the
authority order instead (2026-10-22). Aquifer follows the same call (below).

**Tests:** `tests/rules/test_asteroid.py::test_asteroid_at_maximum_temperature_costs_14_megacredits_and_does_nothing_else`

### Aquifer once 9 Oceans are placed

**Call:** The Aquifer Standard Project is still offered once all 9 Oceans are placed.
The Player pays 18 MegaCredits and places no Ocean, so they get no Terraform Rating,
no placement bonus and no MegaCredits for adjacent Oceans.

**Why:**
- The rulebook quote under Asteroid covers every Global Parameter, Oceans included.
- The community *Comprehensive FAQ* (v1.7) answers Aquifer with no Oceans left the same
  way: you may pay, and get nothing.
- The open-source game agrees: its Aquifer Standard Project stays usable and only shows
  a "max oceans" warning.

Ticket 03 said the Standard Projects are offered only when "a legal Area exists". The
user had already chosen the authority order for Asteroid, and confirmed it for Aquifer
when ticket 03 started (2026-10-22).

**Tests:** `tests/rules/test_oceans.py::test_once_9_oceans_are_placed_aquifer_costs_18_megacredits_and_does_nothing_else`

### Heat conversion at maximum Temperature

**Call:** Converting 8 heat into a Temperature step is still offered when Temperature is
at +8 °C. The Player spends 8 heat; Temperature and Terraform Rating stay as they are.

**Why:**
- The rulebook quote under Asteroid covers any Action that raises a Global Parameter,
  and converting heat is one.
- The open-source game agrees: its heat conversion only adds a "max temperature" warning
  and stays usable.

The user chose this when ticket 04 started (2026-10-23), following the Asteroid call.

**Tests:** `tests/rules/test_heat_conversion.py::test_at_maximum_temperature_converting_heat_costs_8_heat_and_does_nothing_else`

## Track bonuses

### The Ocean at 0 °C once 9 Oceans are placed

**Call:** A Player who raises Temperature to 0 °C when all 9 Oceans are already placed
gets no Ocean, and nothing instead. The game log says so.

**Why:** It is the Aquifer call above: a Global Parameter at its maximum stops rising.
The user placed this bonus under that call when ticket 04 was written.

**Tests:** `tests/rules/test_track_bonuses.py::test_once_9_oceans_are_placed_reaching_0_degrees_places_no_ocean`

### When the 0 °C Ocean is placed

**Call:** When a Greenery reaches 8 % Oxygen and that Temperature step reaches 0 °C, the
Player places the Ocean first. Only then do they collect the Greenery's placement bonus
and its 2 MegaCredits per adjacent Ocean, which counts the new Ocean if it is next to the
Greenery. The Action ends after that.

**Why:** The rulebook doesn't order the two effects. The user ruled that the Player
chooses which to carry out first (2026-10-23). Placing the Ocean first is never worse for
the Player, so the engine always does that and asks nothing. The open-source game uses
the other order: it defers the Ocean until the Greenery's bonuses are paid.

**Tests:** `tests/rules/test_track_bonuses.py::test_8_percent_oxygen_can_raise_temperature_to_0_degrees_and_the_ocean_is_placed_before_the_greenerys_bonus`

## End of the Game

### Order of the final Greenery conversion

**Call:** After the final Production phase, Players convert plants into Greeneries in
player order, starting with the first player of the final Generation. Each Player
converts as many times as they like (one Greenery per Decision, then "Done") before the
next Player starts. A Player without 8 plants or a free Area for a Greenery is passed over.

**Why:** The rulebook says only "in player order". The open-source game goes round the
Players in generation order from the first player, asking each one again until they are
done or cannot convert, and only then moves to the next.

**Tests:** `tests/rules/test_final_greenery_conversion.py::test_players_go_in_player_order_from_the_first_player_and_then_the_game_is_over`
and `test_a_player_keeps_converting_until_they_are_done`.

## Tiles

### Card-draw placement bonuses before there is a deck (temporary)

**Call:** Until the deck exists (ticket 08), a Tile placed on an Area with a card bonus
gives nothing. The game log says what it would give, for example "Player 1 would draw
2 cards from the placement bonus, but there is no deck yet."

**Why:** Not a rules question but a gap in the engine, recorded so that play-testing
doesn't mistake it for a bug. Chosen by the user (2026-10-22). Ticket 08 replaces it
with the real draw.

**Tests:** `tests/rules/test_placement_bonuses.py::test_until_there_is_a_deck_a_card_bonus_only_says_what_it_would_give`

## Turns

### Passing after the first Action of a Turn

**Call:** Pass is offered at any point in a Turn, including after the first Action.

**Why:** The rulebook describes passing as taking no Action on your Turn, but does not
forbid passing after one Action, and the result is the same as ending the Turn and
passing at the start of the next one. The open-source game (tiebreaker) offers
"Pass for this generation" after the first action too. Chosen by the user (2026-10-22).

**Tests:** `tests/rules/test_turns.py::test_a_player_may_pass_straight_after_their_first_action`

### End Turn once everyone else has passed

**Call:** End Turn is not offered once every other Player has passed. The last Player
simply keeps taking Turns of one or two Actions until they pass.

**Why:** The rulebook has the last Player keep taking Turns. Ending a Turn would only
start their next one, so End Turn would be an Option that changes nothing. The
open-source game also hides "End Turn" when all other players have passed.

**Tests:** `tests/rules/test_turns.py::test_end_turn_is_not_offered_once_every_other_player_has_passed`

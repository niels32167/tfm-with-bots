# Rules notes

Every rules judgment call the engine makes, so play can be checked against the agreed
interpretation. The order of authority is: the official rulebook, then the official
FryxGames FAQ and corrections, then the open-source game
(terraforming-mars/terraforming-mars) as tiebreaker (ADR 0001).

Each note gives the call, the sources behind it, and the tests that pin it down.

## Standard Projects

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
authority order instead (2026-10-22). The same reasoning will apply to Aquifer once all
nine Oceans are placed.

**Tests:** `tests/rules/test_asteroid.py::test_asteroid_at_maximum_temperature_costs_14_megacredits_and_does_nothing_else`

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

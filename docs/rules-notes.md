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

## Milestones and Awards

### Award ties, and counts of 0

**Call:** Every Player tied for first place in a funded Award gets 5 Victory Points, and
then nobody gets second place. With a single leader, every Player tied for second gets 2.
2-player Games have no second place. A count of 0 is scored like any other count: if
nobody has heat, every Player ties for first in Thermalist, and if one Player leads, every
Player at 0 ties for second.

**Why:**
- The rulebook says ties are friendly: all tied Players get the bonus for their place, a
  tie for first leaves no second place, and second place gives nothing in a 2-player Game.
- The rulebook says nothing about counts of 0. The open-source game (tiebreaker) scores
  them like any other count, with the results above.

Chosen by Claude (2026-10-23), on the user's instruction to make the ticket 05 calls
without asking.

**Tests:** `tests/rules/test_awards.py::test_players_tied_for_first_place_all_get_5_and_nobody_gets_second_place`,
`test_miner_counts_steel_and_titanium_together` (a tie for second),
`test_in_a_2_player_game_the_runner_up_gets_nothing` and
`test_a_count_of_0_can_win_an_award_or_take_second_place`.

### What the Awards and Milestones count

**Call:**
- **Landlord** counts every Tile a Player owns: their Greeneries and Cities, and later
  their special Tiles. Oceans belong to nobody, so they count for nobody.
- **Mayor** counts the Cities a Player owns and **Gardener** their Greeneries.
- **Banker** compares MegaCredit Production as it stands, below zero too: −2 beats −5.
- **Thermalist** counts heat and **Miner** steel and titanium together. Like every Award,
  they are counted at final scoring: after the final Production phase (which turns energy
  into heat) and after the final Greenery conversion (whose Greeneries count for Landlord).
- A claimed Milestone stays claimed even if its Player later falls below it. Nothing can
  lower these counts before cards exist; a Planner's hand can shrink once there are cards,
  and its test comes with ticket 08.

**Why:** These follow the printed conditions ("owning the most tiles in play", "the most
heat resource cubes"). The open-source game also leaves Oceans out of Landlord. Whether
the Cities off Mars (Phobos Space Haven, Ganymede Colony) count for Mayor, Landlord and
City scoring is for ticket 18, when they can be placed.

Chosen by Claude (2026-10-23), on the user's instruction to make the ticket 05 calls
without asking.

**Tests:** `tests/rules/test_awards.py::test_landlord_goes_to_whoever_owns_the_most_tiles_and_oceans_belong_to_nobody`,
`test_banker_goes_to_the_highest_megacredit_production_even_below_zero`,
`test_thermalist_counts_heat_after_the_final_production_phase`,
`tests/rules/test_final_scoring.py::test_greeneries_from_the_final_conversion_score_and_count_for_landlord`,
and the Mayor and Gardener tests in `tests/rules/test_milestones.py`.

### Builder, Planner and Scientist before there are cards (temporary)

**Call:** Until cards exist (ticket 08), every Player has 0 building Tags, 0 cards in hand
and 0 science Tags. Builder and Planner can never be claimed, and a funded Scientist Award
gives every Player 5 Victory Points, since they all tie for first at 0.

**Why:** Not a rules question but a gap in the engine, recorded so that play-testing
doesn't mistake it for a bug. It follows from the call on counts of 0 above. Ticket 08
gives these three their real counts.

**Tests:** `tests/rules/test_awards.py::test_until_there_are_tags_a_funded_scientist_gives_every_player_5_victory_points`

## Final scoring

### A tie for the win

**Call:** The Player with the most Victory Points wins. Of Players tied on Victory Points,
the one with the most MegaCredits ranks higher. Players tied on both share their rank, and
the win if it is first place. The game log says which happened.

**Why:** The rulebook breaks a tie on Victory Points by MegaCredits and goes no further.
Some rules summaries add cards in hand as a further tiebreak, but no official source for
that was found, and there are no hands until ticket 08.

Chosen by Claude (2026-10-23), on the user's instruction to make the ticket 05 calls
without asking.

**Tests:** `tests/rules/test_final_scoring.py::test_on_equal_victory_points_the_player_with_more_megacredits_ranks_higher`
and `test_players_tied_on_victory_points_and_megacredits_share_a_rank`.

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

## Scenarios

### A Terraform Rating of 5 or more

**Call:** A Scenario refuses a Player with a Terraform Rating below 5.

**Why:** Not a rules question but a guard for the fuzzer's "no negative Resources"
invariant. In the Production phase a Player gains MegaCredits equal to their Terraform
Rating plus their MegaCredit Production, which stops at −5, so from a Terraform Rating of
5 up nobody ever ends with fewer than 0 MegaCredits. The rulebook says nothing about
negative MegaCredits, and a Game from normal setup never comes near this: Terraform
Rating starts at 20 and only rises in the base game with Corporate Era. Chosen by the
user (2026-10-23).

**Tests:** `tests/rules/test_starting_a_game.py::test_a_scenario_terraform_rating_is_at_least_5_so_megacredits_never_go_below_zero`

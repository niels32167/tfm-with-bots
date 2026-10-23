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
- **Builder** counts building Tags in play and **Scientist** science Tags in play, both as
  every Tag is counted (see "Tags on played Events" below). **Planner** counts cards in hand.
- A claimed Milestone stays claimed even if its Player later falls below it, as a Planner
  does once they play a card.

**Why:** These follow the printed conditions ("owning the most tiles in play", "the most
heat resource cubes"). The open-source game also leaves Oceans out of Landlord. Whether
the Cities off Mars (Phobos Space Haven, Ganymede Colony) count for Mayor, Landlord and
City scoring is for ticket 18, when they can be placed.

Chosen by Claude (2026-10-23), on the user's instruction to make the ticket 05 calls
without asking.

Builder, Planner and Scientist got their real counts with ticket 08 (2026-10-23).

**Tests:** `tests/rules/test_awards.py::test_landlord_goes_to_whoever_owns_the_most_tiles_and_oceans_belong_to_nobody`,
`test_banker_goes_to_the_highest_megacredit_production_even_below_zero`,
`test_thermalist_counts_heat_after_the_final_production_phase`,
`test_scientist_counts_science_tags_in_play_and_none_on_played_events`,
`tests/rules/test_final_scoring.py::test_greeneries_from_the_final_conversion_score_and_count_for_landlord`,
and the Mayor, Gardener, Builder and Planner tests in `tests/rules/test_milestones.py`, among
them `test_a_claimed_planner_stays_claimed_after_the_hand_shrinks`.

## Final scoring

### A tie for the win

**Call:** The Player with the most Victory Points wins. Of Players tied on Victory Points,
the one with the most MegaCredits ranks higher. Players tied on both share their rank, and
the win if it is first place. The game log says which happened.

**Why:** The rulebook breaks a tie on Victory Points by MegaCredits and goes no further.
Some rules summaries add cards in hand as a further tiebreak, but no official source for
that was found, and the open-source game ranks by Victory Points, then MegaCredits only.

Chosen by Claude (2026-10-23), on the user's instruction to make the ticket 05 calls
without asking. Revisited once there were hands (ticket 08): the user chose to keep
MegaCredits as the only tiebreak (2026-10-23).

**Tests:** `tests/rules/test_final_scoring.py::test_on_equal_victory_points_the_player_with_more_megacredits_ranks_higher`
and `test_players_tied_on_victory_points_and_megacredits_share_a_rank`.

## Cards

### Tags on played Events

**Call:** A Player's Tags are counted in one place, over their played Automated and Active
cards (and, from ticket 21, their Corporation). No Tag on a played Event counts, the Event
Tag included: not for Requirements, Builder, Scientist or Victory Points per Tag. The card
catalog keeps the Event Tag as printed, for the GUI. An Event's Tags count only while it is
being played, for the "when you play…" effects of ticket 16.

**Why:**
- The rulebook puts an Event face down once it is played, and its Tags apply only while it
  is being played.
- Media Archives counts the Events played, not their Tags.
- The open-source game (tiebreaker) leaves the Event Tag off its Events and counts no Tag
  on a played Event, so it gives the same results.

Chosen by the user (2026-10-23).

**Tests:** `tests/rules/test_tags.py::test_no_tag_on_a_played_event_counts_not_even_the_event_tag` and
`tests/rules/test_awards.py::test_scientist_counts_science_tags_in_play_and_none_on_played_events`.

### Paying with steel and titanium

**Call:** A card with a building Tag may be paid partly or wholly with steel, worth 2
MegaCredits each, and a card with a space Tag with titanium, worth 3. When there is more
than one way to pay, a payment Decision offers one Option per split, the most MegaCredits
first. Steel and titanium may pay more than the cost, with no change, but only when the last
cube is needed: a split with a cube the others make unneeded (3 steel for a 4-MegaCredit
card) is left out. With only one way to pay, the card is paid for with no Decision.

**Why:**
- The rulebook lets steel and titanium pay for those cards and gives no refund for
  overpaying.
- A split with a cube that isn't needed only loses that cube, so it is never worth taking.
  Offering it would be an Option that only does worse, the same reasoning as not offering
  End Turn when it changes nothing.

Chosen by the user (2026-10-23).

**Tests:** `tests/rules/test_payment.py`, in particular
`test_steel_overpays_only_when_the_last_cube_is_needed` and
`test_with_only_one_way_to_pay_there_is_no_payment_decision`.

### Production at its limit

**Call:** A card is not offered if playing it would take the Player's own Production below
its limit (MegaCredit Production −5, every other Production 0), or their own Resources below
0. So Nuclear Power and Black Polar Dust need MegaCredit Production −3 or more, and Strip Mine
needs 2 energy Production.

**Why:** The rulebook lets a Player play a card only if they can carry out its effects on
their own Resources and Production; Production never goes below its limit. The open-source
game checks the same before offering a card. Chosen by Claude (2026-10-23), following the
rulebook.

**Tests:** `tests/cards/test_nuclear_power.py::test_nuclear_power_cannot_take_megacredit_production_below_minus_5`,
`tests/cards/test_black_polar_dust.py::test_black_polar_dust_cannot_take_megacredit_production_below_minus_5`,
`tests/cards/test_strip_mine.py::test_strip_mine_needs_2_energy_production_to_lower` and
`tests/cards/test_rad_chem_factory.py::test_rad_chem_factory_needs_energy_production_to_lower`.

### The order of a card's effects

**Call:** The effects written as data are carried out in a fixed order: Resources,
Production, Temperature and Oxygen steps, Terraform Rating, cards drawn, then the Tiles one
at a time. A Tile that a track bonus gives along the way (the Ocean at 0 °C) is placed
before the card's own Tiles. When Strip Mine's first Oxygen step reaches 8 % and that
Temperature step reaches 0 °C, its second Oxygen step comes before the Ocean is placed.

**Why:** The rulebook doesn't order a card's effects. The Player chooses the order of
simultaneous effects, but when one order is never worse the engine applies it without a
Decision (see "When the 0 °C Ocean is placed" above). For the cards described as data, every
order gives the same outcome; a card whose order matters gets its own Rust code (ADR 0009).
Chosen by Claude (2026-10-23), on the user's instruction to make the remaining ticket 08
calls without asking.

**Tests:** `tests/cards/test_strip_mine.py::test_strip_mine_reaching_8_percent_oxygen_and_0_degrees_gives_the_ocean_to_place_last`
and `tests/cards/test_black_polar_dust.py::test_black_polar_dust_places_an_ocean_and_trades_megacredit_production_for_heat_production`.

### A card's Oceans once 9 are placed

**Call:** A card that places Oceans can still be played once all 9 are placed; it places as
many as are left (none at 9) and does everything else. Lake Marineris with 8 Oceans placed
places one; Black Polar Dust with 9 only changes Production.

**Why:** It is the Aquifer call above: a Global Parameter at its maximum stops rising, and
the rulebook lets cards that raise it be played anyway. Chosen by Claude (2026-10-23),
following the Aquifer call.

**Tests:** `tests/cards/test_lake_marineris.py::test_with_8_oceans_placed_lake_marineris_places_the_last_one`
and `tests/cards/test_black_polar_dust.py::test_once_9_oceans_are_placed_black_polar_dust_only_changes_production`.

### The starter-set deal (temporary)

**Call:** Until ticket 09 brings Corporations and buying cards, a new Game shuffles the 11
starter-set cards (#022, #045, #053, #056, #060, #087, #113, #138, #141, #144 and #168) and
deals them round-robin from the first player: 5–6 each with 2 Players, 2–3 with 5. Every
other Project Card is shuffled into the deck. Cards that are not implemented yet can sit in a
hand (from a card bonus or a Scenario) but are never offered.

**Why:** Not a rules question but a stand-in for the Corporate Era setup, so the starter set
can be played in the GUI. Chosen by the user (2026-10-23).

**Tests:** `tests/rules/test_deck.py::test_until_ticket_09_a_new_game_deals_out_the_starter_set_round_robin_from_the_first_player`
and `tests/rules/test_playing_cards.py::test_a_card_that_is_not_implemented_yet_is_never_offered`.

### When the deck runs out (temporary)

**Call:** A Player who must draw from an empty deck draws nothing more, and the game log
says so: "The deck is empty, so Player 1 draws no more cards."

**Why:** Not a rules question but a gap in the engine. The rulebook reshuffles the discard
pile into a new deck, but nothing is discarded until ticket 09 (Research and Sell Patents),
which brings the reshuffle. Until then only a Scenario that holds nearly every card can
empty the deck: a normal Game has 197 cards in it after the deal, and only 6 card bonuses on
the board. Chosen by Claude (2026-10-23), on the user's instruction to make the remaining
ticket 08 calls without asking.

**Tests:** `tests/rules/test_placement_bonuses.py::test_a_card_bonus_with_the_deck_empty_draws_nothing`

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

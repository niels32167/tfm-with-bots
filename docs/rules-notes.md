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

While an Event is being played, its Tags do count for paying: titanium pays for Imported GHG,
an Event with a space Tag, as for any card with one (see "Paying with steel and titanium"). The
rulebook lets titanium pay for any card with a space Tag, and the open-source game does the same
for Events.

**Tests:** `tests/rules/test_tags.py::test_no_tag_on_a_played_event_counts_not_even_the_event_tag`,
`tests/rules/test_awards.py::test_scientist_counts_science_tags_in_play_and_none_on_played_events`,
`tests/cards/test_technology_demonstration.py::test_technology_demonstrations_tags_stop_counting_once_it_is_played`
(an Event played during the Game) and
`tests/cards/test_imported_ghg.py::test_imported_ghg_may_be_paid_with_titanium_for_its_space_tag`.

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

The same check covers a Resource the card makes its Player lose: Moss "requires that you lose 1
plant", so it is not offered to a Player with no plant (open-source game: `player.plants >= 1`),
and Nitrophilic Moss, which loses 2, not to a Player with fewer than 2 (`player.plants >= 2`).

**Tests:** `tests/cards/test_nuclear_power.py::test_nuclear_power_cannot_take_megacredit_production_below_minus_5`,
`tests/cards/test_black_polar_dust.py::test_black_polar_dust_cannot_take_megacredit_production_below_minus_5`,
`tests/cards/test_strip_mine.py::test_strip_mine_needs_2_energy_production_to_lower`,
`tests/cards/test_rad_chem_factory.py::test_rad_chem_factory_needs_energy_production_to_lower`,
`tests/cards/test_moss.py::test_moss_needs_a_plant_to_lose`,
`tests/cards/test_nitrophilic_moss.py::test_nitrophilic_moss_needs_2_plants_to_lose` and
`tests/cards/test_investment_loan.py::test_investment_loan_cannot_take_megacredit_production_below_minus_5`.

### The order of a card's effects

**Call:** The effects written as data are carried out in a fixed order: Resources (fixed, then
per Tag or Tile), Production (fixed, then per Tag or Tile, then for having at least so many),
Temperature and Oxygen steps, Terraform Rating (fixed, then per Tag), cards drawn, cards looked
at to keep or buy some of (see "Looking at cards to keep some of them" and "Buying the card
looked at" below), the Production or Resource change the Player chooses (see "A Production
change to choose" and "A Resource change to choose for an action" below), then the Tiles one at
a time. An action is paid for first (see "Card actions" below). A Tile that a track bonus
gives along the way (the Ocean at 0 °C) is placed before the card's own Tiles. When Strip
Mine's first Oxygen step reaches 8 % and that Temperature step reaches 0 °C, its second Oxygen
step comes before the Ocean is placed. Triggers on the card played come once it is paid for,
before its effects, and Mars University's discard after them (see "Triggers" and "Mars University's
discard" below); Immigrant City lowers its Production after its City (see "Immigrant City's own
City" below).

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

The Events that place Oceans follow the same call: Ice Asteroid with 8 Oceans placed places
one, Subterranean Reservoir with 9 places none, and Towing a Comet with 9 still gains its plants
and raises Oxygen.

**Tests:** `tests/cards/test_lake_marineris.py::test_with_8_oceans_placed_lake_marineris_places_the_last_one`,
`tests/cards/test_black_polar_dust.py::test_once_9_oceans_are_placed_black_polar_dust_only_changes_production`,
`tests/cards/test_ice_asteroid.py::test_with_8_oceans_placed_ice_asteroid_places_the_last_one`,
`tests/cards/test_subterranean_reservoir.py::test_once_9_oceans_are_placed_subterranean_reservoir_is_still_offered_and_places_none`
and `tests/cards/test_towing_a_comet.py::test_once_9_oceans_are_placed_towing_a_comet_still_gains_plants_and_raises_oxygen`.

### A card's City or Greenery needs an Area

**Call:** A card that places a City or a Greenery is offered only while there is an Area for
that Tile. Domed Crater is not offered when the only free land on Mars is next to a City, and
Urbanized Area not without free land next to 2 Cities. Oceans are the exception (see "A card's
Oceans once 9 are placed"), but Artificial Lake's Ocean, which goes on land, needs a free Area
reserved for nothing while fewer than 9 Oceans are placed. No card in the v1 set
places two Cities or two Greeneries, so one Area for each kind is enough. The same check
covers Greeneries: Plantation (#193), the first card with a Greenery on the usual Areas, is not
offered without free land.

**Why:** The rulebook lets a Player play a card only if they can carry out its effects, and a
Tile with no legal Area can't be placed. The open-source game also checks for an Area before
it offers such a card. Chosen by Claude in ticket 08 (2026-10-23). The test came with Domed
Crater, the first card with a City Tile (2026-10-27).

**Tests:** `tests/rules/test_playing_cards.py::test_a_card_with_a_city_tile_is_not_offered_without_an_area_for_the_city`,
`test_no_card_places_two_cities_or_two_greeneries_so_one_area_for_each_is_enough`,
`tests/cards/test_urbanized_area.py::test_urbanized_area_needs_free_land_next_to_2_cities`,
`tests/cards/test_artificial_lake.py::test_artificial_lake_is_not_offered_without_free_land` and
`tests/cards/test_plantation.py::test_plantation_is_not_offered_without_an_area_for_its_greenery`.

### Production and Terraform Rating per Tag

**Call:** A card that raises Production "for each" Tag the Player has counts their Tags once
the card is played, so its own Tags count. So does Terraforming Ganymede, which raises
Terraform Rating 1 step for each jovian Tag, its own included. Tags on played Events don't
count. With nothing to count, the Production stays as it is and the game log says nothing
about it. Miranda Resort raises MegaCredit Production 1 step for each Earth Tag. It has no
Earth Tag of its own.

**Why:**
- The cards that also count their own Tags say so: Power Grid's and Terraforming Ganymede's
  "including this" and Satellites' "including this one". Insects, which counts plant Tags, has
  none of its own.
- Tags on Events are covered under "Tags on played Events" above.
- The open-source game adds the card's own Tags to the count while the card is being played
  (`Counter`: "include the card itself if it isn't already on the tableau"), with the same
  results.

Chosen by Claude (2026-10-27), on the user's instruction to make the remaining ticket 11 calls
without asking. Terraform Rating per Tag as effect data (`terraform_rating_per`): chosen by the
user (2026-10-29).

**Tests:** `tests/cards/test_miranda_resort.py`,
`tests/cards/test_cartel.py::test_cartel_with_only_its_own_earth_tag_raises_megacredit_production_by_1`
and `tests/cards/test_terraforming_ganymede.py`.

### Mangrove's and Protected Valley's Greenery

**Call:** Mangrove and Protected Valley each place a Greenery on any free Area reserved for
Oceans. That Area need not be next to the Player's own Tiles. From then on it is a Greenery like any other:
- it raises Oxygen, and with it Terraform Rating, unless Oxygen is at its maximum;
- the Player collects the Area's printed placement bonus and 2 MegaCredits for each Ocean next
  to it;
- it scores as a Greenery and counts for Gardener and Landlord;
- the Player's later Greeneries may go next to it.

Fewer than 9 Oceans placed always leaves an Area for the next one. Of the 12 Areas reserved
for Oceans, other Tiles take at most 3 (Mangrove, Protected Valley and Mohole Area), and
Artificial Lake's Ocean goes on land (see "Artificial Lake's Ocean" below). So the 0 °C Ocean
and Aquifer need no extra check.

**Why:**
- Mangrove says "Disregard normal placement restrictions for this", Protected Valley
  "disregarding normal placement restrictions".
- The rulebook gives the placement bonus for any Tile placed on an Area.
- The open-source game places both cards' Greenery on an Area reserved for Oceans
  (`greenery: {on: 'ocean'}`) through its normal Greenery placement, bonuses included.

The sources agree. Chosen by Claude (2026-10-27), on the user's instruction to make the
remaining ticket 11 calls without asking; Protected Valley by Claude (2026-10-29), on the same
instruction for ticket 13.

**Tests:** `tests/cards/test_mangrove.py`, among them
`test_mangroves_greenery_is_the_players_own_for_milestones_awards_and_their_next_greenery`,
`tests/cards/test_protected_valley.py`,
`tests/fuzzing/test_invariants.py::test_mangroves_greenery_on_an_area_reserved_for_oceans_breaks_no_invariant`,
`test_protected_valleys_greenery_on_an_area_reserved_for_oceans_beside_mangroves_breaks_no_invariant`
and `test_a_greenery_on_an_area_reserved_for_oceans_without_a_card_that_puts_it_there_breaks_an_invariant`.

### Artificial Lake's Ocean

**Call:** Artificial Lake places its Ocean on any free Area on Mars reserved for nothing,
whatever is next to it: not on an Area reserved for Oceans, and not on Noctis City's Area,
which is reserved for the Noctis City card. From then on it is an Ocean like any other:
- it raises the Ocean track, and with it Terraform Rating;
- the Player collects the Area's printed placement bonus and 2 MegaCredits for each Ocean
  next to it;
- a Tile placed next to it later collects 2 MegaCredits for it.

The card is offered only while there is a free Area reserved for nothing, unless all 9 Oceans
are placed: then it is played and places none (see "A card's Oceans once 9 are placed").

**Why:**
- The card: "Place 1 ocean tile ON AN AREA NOT RESERVED FOR OCEAN".
- The rulebook keeps Noctis City's Area for the Noctis City card, and gives the placement bonus
  and the adjacent-Ocean bonus for any Tile placed.
- The open-source game places it with `ocean: {on: 'land'}` and checks for a free Area on land
  only while Oceans are not at their maximum (`bespokeCanPlay`: "Card is playable, it just has
  no effect").

The sources agree. Chosen by Claude (2026-10-29), on the user's instruction to make the
remaining ticket 12 calls without asking.

**Tests:** `tests/cards/test_artificial_lake.py`, among them
`test_artificial_lakes_ocean_next_to_an_ocean_collects_2_megacredits_for_it` and
`test_once_9_oceans_are_placed_artificial_lake_needs_no_free_land`, and
`tests/fuzzing/test_invariants.py::test_more_oceans_on_land_than_cards_that_put_one_there_break_an_invariant`.

### Urbanized Area's City

**Call:** Urbanized Area places its City on any free Area on Mars reserved for nothing that is
next to at least 2 Cities, whoever owns them; the usual rule that no City goes next to another
does not apply to it. The card is offered only while there is such an Area (see "A card's City
or Greenery needs an Area"). Later Cities still keep apart from it, as from any City.

**Why:**
- The card: "Place a city tile ADJACENT TO AT LEAST 2 OTHER CITY TILES".
- The open-source game offers the Areas on land with at least 2 Cities next to them, and checks
  for one before it offers the card.

The sources agree. Chosen by Claude (2026-10-29), on the user's instruction to make the
remaining ticket 12 calls without asking.

**Tests:** `tests/cards/test_urbanized_area.py`, among them
`test_later_cities_keep_apart_from_urbanized_areas_city`, and
`tests/fuzzing/test_invariants.py::test_urbanized_area_lets_only_its_own_city_lie_next_to_other_cities`.

### A Production change to choose

**Call:** A card whose Production change is the Player's choice (Artificial Photosynthesis: "1
plant Production step or 2 energy Production steps") asks with a Production Decision, one
Option for each change the Player can carry out, after the card's other effects and before its
Tiles. When only one change is possible, it is made without a Decision. Whether the card can be
played at all is checked against the Player's Production before its other effects; no card has
both a choice and fixed Production.

**Why:**
- The card leaves the choice to its Player, and both changes are worth having, so neither Option
  only does worse.
- A Decision with one Option changes nothing (see "The last card is kept without a Decision").
- The open-source game offers the two as `or` behaviours, and selects the only one possible on
  its own (`autoSelect`).

Chosen by the user (effect data and a shared Decision, 2026-10-29); the Decision's details by
Claude, on the user's instruction to make the remaining ticket 12 calls without asking.

**Tests:** `tests/cards/test_artificial_photosynthesis.py`.

### Robotic Workforce

**Call:** Robotic Workforce copies the production box of one of its Player's own played
Automated or Active cards with a building Tag: that card's fixed Production, then its Production
per Tag or Tile, counted again as it is copied. The copy is carried out in full, decreases
included, so:
- a box the Player cannot carry out is not offered (Tropical Resort without 2 heat Production);
- the card is not offered without at least one box it can copy;
- with only one, it is copied without a Decision;
- otherwise a Production Decision offers one Option per card, in card-number order, even when
  two boxes are the same.

Events, cards without a production box and other Players' cards are never offered.

**Why:**
- The card: "Duplicate only the production box of one of your building cards".
- The *Comprehensive FAQ* (v1.7, quoted in the open-source game) says it copies only the
  production box, decreases must still be performed, it "cannot be played if you have no
  building cards in play with a production box that you can fully copy", and only your own
  cards count. Copying Medical Lab recounts the building Tags.
- The open-source game copies the production of the Player's own building cards it can carry
  out, Events excluded.
- One Option per card is what the card names. An Option that gives the same as another is not
  worse, so it isn't left out.

The sources agree. Chosen by the user (implemented now, as Rust code, 2026-10-29); the details
by Claude, on the user's instruction to make the remaining ticket 12 calls without asking.

From the FAQ, as the ticket 17 card lines quote it: a box that decreases any Player's Production
picks its victim again. Copying Heat Trappers or Biomass Combustors raises the Player's own energy
Production and then asks for a target as the card does (see "Taking from any Player" below); the
box is offered only while someone can lose the Production. Still to come: Mining Area and Mining
Rights copy the Production their Tile gave (ticket 18); a Corporation's printed Production, but
not one in an effect or action, can be copied (Mining Guild, ticket 21). Each ticket's card line says so, and
`tests/rules/test_playing_cards.py::test_every_implemented_building_card_has_its_printed_production_box_as_production_data`
fails for a building card whose production box isn't Production data.

The same goes for a card's action (ticket 15): Robotic Workforce copies the production box of
Space Elevator, Electro Catapult and AI Central, printed apart from their action, but not the
one that is part of Equatorial Magnetizer's or Underground Detonations' action. Those are the
action's Production data, which the test above allows.

**Tests:** `tests/cards/test_robotic_workforce.py`, among them
`test_robotic_workforce_copies_only_the_production_box_not_the_cards_other_effects` and
`test_robotic_workforce_offers_every_card_in_card_number_order_even_two_with_the_same_box`;
`tests/cards/test_medical_lab.py::test_robotic_workforce_copying_medical_lab_counts_the_building_tags_again`,
`tests/cards/test_equatorial_magnetizer.py::test_robotic_workforce_cannot_copy_equatorial_magnetizer_whose_production_box_is_its_action`, and
`tests/fuzzing/test_invariants.py::test_robotic_workforce_offering_a_card_it_may_not_copy_breaks_an_invariant`.

### Research's two science Tags

**Call:** Research is printed with two science Tags, and both count, for Requirements, Awards
and Victory Points like any other Tags. "Counts as playing 2 science cards" also makes it two
science Tags played for the "when you play a science Tag" effects: Mars University (ticket 16)
and Olympus Conference (see "Olympus Conference and Mars University").

**Why:** The card list and the open-source game both give it two science Tags. Chosen by
Claude (2026-10-29), on the user's instruction to make the remaining ticket 12 calls without
asking.

**Tests:** `tests/cards/test_research.py::test_research_counts_as_2_science_tags`,
`test_research_counts_twice_for_the_scientist_award` and
`tests/cards/test_gene_repair.py::test_gene_repair_needs_3_science_tags`.

### A card's own Tags and its Requirements

**Call:** A card's Requirements are checked before it is played, so its own Tags never help
meet them. Advanced Ecosystems, printed with a plant, a microbe and an animal Tag, needs one
of each on the Player's other played cards.

**Why:**
- The rulebook checks a card's Requirements to see whether it may be played; until then the
  card is not in play, and only Tags in play count (see "Tags on played Events").
- The open-source game checks Requirements against the Player's tableau, which doesn't hold the
  card yet.

The sources agree. Chosen by Claude (2026-10-29), on the user's instruction to make the
remaining ticket 13 calls without asking.

**Tests:** `tests/cards/test_advanced_ecosystems.py::test_advanced_ecosystems_own_tags_do_not_meet_its_requirements`.

### Insulation

**Call:** Insulation trades 1 up to all of its Player's heat Production for as many steps of
MegaCredit Production. A Production Decision (see "A Production change to choose") offers one
Option per number of steps, the fewest first. With 1 heat Production the trade is made without
a Decision, and without heat Production the card is not offered.

**Why:**
- The card: "Decrease your heat production any number of steps and increase your MC production
  the same number of steps".
- The open-source game asks for an amount from 1 up to the heat Production, and doesn't offer
  the card without heat Production (`bespokeCanPlay`: `player.production.heat >= 1`).
- Trading 0 steps would only spend 2 MegaCredits and the card, an Option that only does worse
  than not playing it (the same reasoning as not offering End Turn when it changes nothing).

Chosen by the user (2026-10-29): Rust code sharing the Production Decision, and 1 up to the heat
Production. The Option order by Claude, on the user's instruction to make the remaining ticket
13 calls without asking.

**Tests:** `tests/cards/test_insulation.py`.

### Looking at cards to keep some of them

**Call:** Business Contacts ("look at the top 4 cards from the deck, take 2 of them into hand and
discard the other 2") and Invention Contest (the top 3, take 1) take their cards from the top of
the deck once the card is paid for. The Player keeps them one at a time: a "keep_cards" Decision
offers one Option per card they may still keep, in card-number order. Once they have kept as many
as the card says, those go into their hand together and the rest go face down to the discard
pile. Only that Player sees the cards (in their own Player View, and in the full view); the game
log says how many they looked at, kept and discarded, but not which.

When the deck runs out while they take the cards, the discard pile is shuffled into a new deck as
for any draw (see "When the deck runs out"). With no more cards to look at than they keep (both
piles nearly empty), they keep them all without a Decision.

**Why:**
- The cards say so; the rulebook puts discarded cards face down.
- One card at a time is how the Draft picks; a Decision per pair would need a pair picker and
  offers nothing more.
- A Decision with no real choice changes nothing (see "The last card is kept without a
  Decision").
- The open-source game writes both as `drawCard: {count, keep}` effects.

Chosen by the user (2026-10-29): effect data `"look_at": {"cards": 4, "keep": 2}` and one card at
a time. The rest by Claude, on the user's instruction to make the remaining ticket 14 calls
without asking.

**Tests:** `tests/cards/test_business_contacts.py`, `tests/cards/test_invention_contest.py`,
`tests/engine/test_views.py::test_while_a_player_keeps_cards_they_look_at_no_other_player_view_shows_them`,
`tests/server/test_keeping_cards.py` and
`tests/fuzzing/test_invariants.py::test_cards_looked_at_with_business_contacts_break_no_invariant`;
the deck running out mid-look and too few cards in
`test_when_the_deck_runs_out_business_contacts_takes_the_rest_from_the_reshuffled_discard_pile`
and `test_with_only_1_card_left_to_draw_business_contacts_keeps_it_without_a_decision`.

### Nitrogen-Rich Asteroid's plant Production

**Call:** Nitrogen-Rich Asteroid raises plant Production 1 step, or 4 steps if the Player has at
least 3 plant Tags in play. With more than 3 plant Tags it still gives 4. The game log shows the 4
as a raise of 1 and then of 3. (When the Tags are counted doesn't matter for this card: it has no
plant Tag of its own, and no Event has one.)

**Why:**
- The card: "Increase your plant production 1 step, or 4 steps if you have 3 plant tags."
- The open-source game gives 1 below 3 plant Tags and 4 from 3 on
  (`player.tags.count(Tag.PLANT) < 3`).

The sources agree. Chosen by the user (2026-10-29): effect data, `"production": {"plants": 1}`
plus `"production_at_least": {"resource": "plants", "steps": 3, "at_least": 3, "of": {"tag":
"plant"}}`. The rest by Claude, on the user's instruction to make the remaining ticket 14 calls
without asking.

**Tests:** `tests/cards/test_nitrogen_rich_asteroid.py`.

### Card actions

**Call:** The action of a played Active card (its red arrow) is an Action its Player may take
once per Generation, from the Generation the card is played in. Only the Player who played the
card may use it. The Action Decision offers each usable action after the cards to play, in
card-number order. An action counts as one of the Turn's two Actions and ends once its Tile, if
any, is placed. Every action is unused again after the Production phase, which ends the
Generation; the Player View shows each Player's "used_actions", and the GUI marks those cards
"Used".

An action is offered only if its Player can carry it out in full: pay its MegaCredits (with steel
or titanium where it allows them), lose the Resources it spends, lower the Production it lowers
(Equatorial Magnetizer needs energy Production), and make at least one of its Resource changes
(Electro Catapult needs a plant or a steel, Power Infrastructure some energy). The order of an
action's effects is its payment, then the order of a card's effects (see "The order of a card's
effects").

**Why:**
- The rulebook makes the action on a blue card an Action, usable once each Generation, marked
  with a Player marker until the Generation ends.
- The open-source game keeps a set of used actions per Player, cleared at the end of each
  Generation, and offers an action only when `canAct` holds, which checks what it spends.

Chosen by the user (2026-10-31): actions are effect data, an `"action"` block in the same shapes
as a card's effects (`engine/cards/cards.json`), with Rust code only for Power Infrastructure;
the Game's waiting fields became one enum first; the GUI offers actions on the played cards. The
rest by Claude, on the user's instruction to make the remaining ticket 15 calls without asking.

**Tests:** `tests/rules/test_card_actions.py`, among them
`test_each_cards_action_can_be_used_only_once_per_generation` and
`test_a_used_action_is_available_again_in_the_next_generation`; and
`tests/fuzzing/test_invariants.py::test_an_action_used_twice_or_not_the_players_own_breaks_an_invariant`.

### Actions that raise a Global Parameter at its maximum

**Call:** An action that raises Oxygen or places an Ocean stays open once that Global Parameter
is at its maximum, as Asteroid and Aquifer do (above). Ironworks, Steelworks and Ore Processor
at 14 % Oxygen spend their energy and gain their steel or titanium; Water Splitting Plant spends
its energy for nothing; Water Import from Europa and Aquifer Pumping once 9 Oceans are placed
are paid for and place none.

**Why:** The rulebook: "You may still play cards and actions that increase the parameter". The
open-source game doesn't block these actions at the maximum. Chosen by Claude (2026-10-31),
following the Asteroid call, on the user's instruction to make the remaining ticket 15 calls
without asking.

**Tests:** `tests/cards/test_ironworks.py::test_at_maximum_oxygen_ironworks_action_is_still_offered_and_only_gains_the_steel`,
`tests/cards/test_water_splitting_plant.py::test_water_splitting_plants_action_is_offered_at_maximum_oxygen_like_asteroid_at_maximum_temperature`
and `tests/cards/test_water_import_from_europa.py::test_once_9_oceans_are_placed_water_import_from_europas_action_is_still_offered_and_places_none`.

### Paying for an action with steel or titanium

**Call:** Water Import from Europa's action costs 12 MegaCredits, which titanium may pay at 3
each, and Aquifer Pumping's 8, which steel may pay at 2 each. They are paid as cards are (see
"Paying with steel and titanium"): a payment Decision with one Option per split, the most
MegaCredits first, only when there is more than one way, and no split with a cube the others
make unneeded. No other action lets steel or titanium pay, so Space Mirrors and Underground
Detonations need their MegaCredits.

**Why:** The cards: "TITANIUM MAY BE USED as if playing a Space card" and "STEEL MAY BE USED as
if you were playing a Building card". The open-source game writes both as
`spend: {megacredits, canUseTitanium}` / `canUseSteel`. Chosen by Claude (2026-10-31), on the
user's instruction to make the remaining ticket 15 calls without asking.

**Tests:** `tests/cards/test_water_import_from_europa.py::test_titanium_may_pay_for_water_import_from_europas_action_at_3_megacredits_each`,
`tests/cards/test_aquifer_pumping.py::test_steel_may_pay_for_aquifer_pumpings_action_at_2_megacredits_each`
and `tests/server/test_card_actions.py`.

### A Resource change to choose for an action

**Call:** Electro Catapult's action spends 1 plant or 1 steel for 7 MegaCredits. With both, a
"resources" Decision offers the two, plant first; with only one, it is spent without a
Decision. Power Infrastructure's action spends 1 up to all of its Player's energy for as many
MegaCredits, one Option per amount, the fewest first; with 1 energy it is spent without a
Decision.

**Why:**
- The cards: "Spend 1 plant or 1 steel to gain 7 MC" and "Spend any amount of energy and gain
  that amount of MC".
- The open-source game offers Electro Catapult's two as `or` behaviours with `autoSelect`, and
  asks Power Infrastructure for an amount from 1 to the Player's energy (`canAct`: energy > 0).
- Spending 0 energy would only use up the action, an Option that only does worse (as for
  Insulation).

Chosen by Claude (2026-10-31), on the user's instruction to make the remaining ticket 15 calls
without asking.

**Tests:** `tests/cards/test_electro_catapult.py` and `tests/cards/test_power_infrastructure.py`.

### Buying the card looked at

**Call:** Inventors' Guild's and Business Network's action ("look at the top card and either buy
it or discard it") takes the top card of the deck, as for "Looking at cards to keep some of
them". The "keep_cards" Decision offers to buy it for 3 MegaCredits, the price of a card bought
in a Research phase, or Done, which discards it face down. The price is paid when it is bought.
With fewer than 3 MegaCredits, the card is looked at and discarded without a Decision; with
the deck and the discard pile both empty, the action looks at none. Only that Player sees the
card; the game log says whether they bought it, but not which card it was.

**Why:**
- The rulebook: buying a card always costs 3 MegaCredits.
- The open-source game writes the action as `drawCard: {count: 1, pay: true}`, which lets the
  Player buy the card if they can pay for it.
- A Decision whose only Option is Done changes nothing (see "The last card is kept without a
  Decision").

Chosen by Claude (2026-10-31), on the user's instruction to make the remaining ticket 15 calls
without asking.

**Tests:** `tests/cards/test_inventors_guild.py`, `tests/cards/test_business_network.py` and
`tests/engine/test_views.py::test_while_a_player_looks_at_the_card_inventors_guild_offers_them_no_other_player_view_shows_it`.

### Martian Rails' Cities on Mars

**Call:** Martian Rails' action gains 1 MegaCredit for each City on Mars, whoever owns it. The
Cities off Mars (Phobos Space Haven and Ganymede Colony, ticket 18) don't count. With no City on
Mars it is still offered, and spends its energy for nothing.

**Why:** The card: "gain 1 MC for each City tile ON MARS", printed with the red border for every
Player's Tiles. The open-source game counts `cities: {where: 'onmars'}` of all Players and only
checks the energy. Chosen by Claude (2026-10-31), on the user's instruction to make the remaining
ticket 15 calls without asking.

**Tests:** `tests/cards/test_martian_rails.py`.

### Discounts

**Call:** A card's discount ("when you play a card, you pay 1 MC less for it") takes MegaCredits
off the cost of every card its Player plays from then on: Research Outpost 1, Earth Catapult and
Anti-Gravity Technology 2 off every card; Space Station, Quantum Extractor, Mass Converter and
Shuttles 2 off each card with a space Tag; Earth Office 3 off each card with an Earth Tag.
- Discounts add up, and with Indentured Workers' (below), but never take a cost below 0.
- An Event's Tags count while it is played, so Space Station makes Ice Asteroid 2 cheaper.
- A card's own discount doesn't apply to itself: it is paid for before it is in play.
- Only cards played are cheaper: not Standard Projects, card actions or cards bought.
- Steel and titanium pay towards the discounted cost.

The Option to play a card, its label and the Player View's "card_costs" give the discounted cost;
the GUI shows it on the hand's cards, with the printed cost struck through.

**Why:**
- The cards say "when you play a card", and the rulebook lets nothing make a cost negative.
- The open-source game sums the `cardDiscount` of the cards on the Player's tableau, which doesn't
  hold the card being paid for, and never lowers a cost below 0.
- The open-source game counts Space Station's discount per space Tag and Mass Converter's per card.
  No card in the v1 set has two space Tags or two Earth Tags, so both give the same costs here.

The sources agree. Chosen by the user (2026-10-31): discounts are effect data, `"discount":
{"megacredits": 2, "tag": "space"}`, and the GUI shows the discounted cost on the cards. The rest
by Claude, on the user's instruction to make the remaining ticket 16 calls without asking.

**Tests:** `tests/rules/test_cost_changes.py`, among them `test_discounts_add_up` and
`test_no_card_has_two_tags_a_discount_counts_so_a_discount_per_card_and_per_tag_are_the_same`;
the card files of the eight cards, among them
`tests/cards/test_space_station.py::test_space_station_makes_an_event_with_a_space_tag_cheaper_too`
and `tests/cards/test_earth_office.py::test_earth_office_takes_a_cost_down_to_0_and_no_further`;
and `tests/fuzzing/test_invariants.py::test_a_cost_the_discounts_do_not_leave_breaks_an_invariant`.

### What steel and titanium are worth with Advanced Alloys

**Call:** With Advanced Alloys in play, each steel its Player has pays 3 MegaCredits and each
titanium 4, wherever steel or titanium may pay: for cards with a building or space Tag, and for the
actions of Aquifer Pumping and Water Import from Europa. The payment Decision follows "Paying with
steel and titanium" with these values: Mine (4) with 2 steel offers 4 MegaCredits, 1 MegaCredit and
1 steel, or 2 steel.

**Why:** The card: "Each titanium you have is worth 1 MC extra. Each steel you have is worth 1 MC
extra." The open-source game raises the Player's steel and titanium values, which every payment
reads, the two actions' included. Chosen by Claude (2026-10-31), on the user's instruction to make
the remaining ticket 16 calls without asking.

**Tests:** `tests/cards/test_advanced_alloys.py`.

### Requirement steps: Adaptation Technology and Special Design

**Call:** Adaptation Technology makes each of its Player's Requirements on a Global Parameter 2
steps easier to meet from then on; Special Design does the same for the next card they play this
Generation. A step is 2 °C of Temperature, 1 % of Oxygen or 1 Ocean, so with either card Breathing
Filters (7 % Oxygen or more) is offered at 5 % and Archaebacteria (−18 °C or colder) at −14 °C.
- "+2 or -2 steps, your choice" is always taken in the Player's favour, with no Decision: the other
  way only makes the card harder to play.
- Both together make 4 steps.
- Requirements on Tags, Production or Tiles don't change.

**Why:**
- The cards: "Your global requirements are +2 or -2 steps, your choice in each case" and "The next
  card you play this generation is +2 or -2 steps in global requirements, your choice."
- The open-source game adds both cards' `globalParameterRequirementBonus` together and widens
  minimums and maximums alike.
- An Option that only does worse is never offered (see "When the 0 °C Ocean is placed").

The sources agree. Chosen by Claude (2026-10-31), on the user's instruction to make the remaining
ticket 16 calls without asking.

**Tests:** `tests/cards/test_adaptation_technology.py` (one case for each Global Parameter's
minimum and maximum) and `tests/cards/test_special_design.py`, among them
`test_special_design_and_adaptation_technology_add_up_to_4_steps`.

### An Event's effect on the next card played

**Call:** Indentured Workers ("the next card you play this generation costs 8 MC less") and Special
Design (2 Requirement steps, above) wait on the next card their Player plays this Generation,
whatever it is:
- that card uses the effect up, even when it gains nothing from it (Mine after Special Design);
- the effect is lost if no card is played before the Production phase ends the Generation;
- Special Design played right after Indentured Workers costs 0 and uses it up, and then waits on
  the card after it itself;
- Standard Projects and card actions neither gain from it nor use it up.

Everyone sees which Event waits on a Player's next card (the Player View's "next_card"); the GUI
shows it on the player board.

**Why:**
- The cards name "the next card you play this generation".
- The open-source game gives the effect only while the Event is the Player's `lastCardPlayed`,
  which the next card played replaces.

The sources agree. Chosen by Claude (2026-10-31), on the user's instruction to make the remaining
ticket 16 calls without asking (effect data, `"next_card": {"discount": 8}`, chosen by the user).

**Tests:** `tests/cards/test_indentured_workers.py`, `tests/cards/test_special_design.py` and
`tests/fuzzing/test_invariants.py::test_an_effect_on_the_next_card_that_is_no_such_event_or_outlasts_the_action_phase_breaks_an_invariant`.

### Triggers

**Call:** A card's Trigger ("when anyone places an ocean tile, gain 2 plants") gives its own Player
the gain, whoever sets it off, once for each thing that sets it off:
- a Tile: once per Tile placed, by anyone or only by the Player as the card says, the 0 °C Ocean
  included (Arctic Algae, Rover Construction, Immigrant City);
- a card the Player plays: once per card of that type and Tag (Optimal Aerobraking's space Event,
  Media Group's Event), once it is paid for and before its own effects;
- a Tag the Player plays: once per such Tag on the card played, so Research sets off Mars
  University twice, and an Event's Tags count (Special Design's science Tag). One Trigger may name
  several Tags (Decomposers);
- a Standard Project the Player pays for, Sell Patents excepted (Standard Technology).

A card in play counts itself: Immigrant City's own City and Mars University's own science Tag set
them off, as their cards say ("including this"). No other card's Trigger matches the card itself:
Media Group is no Event and Optimal Aerobraking no space Event. When several Triggers fire at once,
each Player's, they are carried out in player number order, each Player's cards in card-number
order. The order never changes the outcome, as each only gains its Player something, so no Player
is asked to order them (see "When the 0 °C Ocean is placed"), but for the two science Tag cards (see
"Olympus Conference and Mars University"). The game log says "Player 2's Arctic
Algae takes effect." before what it gains.

**Why:**
- The cards; the rulebook carries out a card's effect each time its condition is met.
- The open-source game calls `onTilePlaced` for every Player's cards on any Tile placed,
  `onCardPlayed` for the Player's own cards with the card just played on their tableau, and counts
  `cardTagCount` of the Tag for Mars University.

The sources agree. Chosen by the user (2026-10-31): Triggers are effect data, `"when": [{"on":
{"tile_placed": {"tile": "ocean", "by": "anyone"}}, "resources": {"plants": 2}}]`, with Rust code
only for Mars University's Decision and Immigrant City's order. The rest by Claude, on the user's
instruction to make the remaining ticket 16 calls without asking.

**Tests:** `tests/rules/test_triggers.py`, among them
`test_a_trigger_fires_for_its_cards_player_not_for_the_player_who_sets_it_off`,
`test_a_trigger_fires_once_for_each_tile_that_sets_it_off`,
`test_a_card_played_sets_off_its_own_trigger_when_it_matches_immigrant_citys_own_city` and
`test_only_active_cards_have_a_trigger_and_one_that_its_own_play_sets_off_says_so`; and the card
files of the seven cards.

### Immigrant City's own City

**Call:** Immigrant City places its City first, which its own Trigger counts (+1 MegaCredit
Production step), and lowers its Player's Production (−1 energy, −2 MegaCredits) after it. So it
can be played at −4 MegaCredit Production, ending at −5, but not at −5. While its City is being
placed, its Player's Production is still as it was. Robotic Workforce copies only its production
box, which needs −3 MegaCredit Production or more (see "Robotic Workforce").

**Why:**
- The Player orders simultaneous effects, and when one order is never worse the engine applies it
  without a Decision (see "When the 0 °C Ocean is placed"). City first lets the card be played in
  more positions and changes nothing else.
- The open-source game places the City before lowering the Production and offers the card down to
  −4 MegaCredit Production (`bespokeCanPlay`: `production.megacredits >= -4`).

The sources agree. Chosen by Claude (2026-10-31), on the user's instruction to make the remaining
ticket 16 calls without asking. The card has Rust code for this (`card_code::IMMIGRANT_CITY`).

**Tests:** `tests/cards/test_immigrant_city.py`, among them
`test_immigrant_city_can_be_played_at_minus_4_megacredit_production_thanks_to_its_own_city` and
`test_robotic_workforce_copies_only_immigrant_citys_production_box`.

### Mars University's discard

**Call:** Each science Tag the Player plays lets them discard a card from their hand to draw one,
once the card's other effects are done, its Tiles included, in any order with Olympus Conference (see
"Olympus Conference and Mars University"). A "discard_to_draw" Decision offers one Option per card in
hand ("Discard Mine to draw a card"), in card-number order, and Done to keep the
hand. Research asks twice, one after the other. With an empty hand there is no Decision. The card
goes face down to the discard pile before the draw, so with the deck empty it may be drawn back
(see "When the deck runs out"); the game log says "Player 1 discards a card to draw one." without
naming either card.

**Why:**
- The card: "you may discard a card from hand to draw a card", so keeping the hand is an Option.
- The open-source game defers the discard until the card's other effects are done and offers
  "Do nothing"; with no card in hand it asks nothing.
- Discarding last never gives the Player less to go on: they see the whole card's outcome, cards
  drawn from a placement bonus included.

Chosen by the user (2026-10-31): after the card's effects, one Decision per science Tag. The
details by Claude, on the user's instruction to make the remaining ticket 16 calls without asking.

**Tests:** `tests/cards/test_mars_university.py`, among them
`test_mars_university_is_set_off_once_for_each_science_tag_so_twice_by_research` and
`test_mars_university_comes_after_the_cards_tiles`; `tests/server/test_discard_to_draw.py`.

### Standard Technology

**Call:** Standard Technology gives its Player 3 MegaCredits once they have paid for a Standard
Project: Power Plant, Asteroid, Aquifer, Greenery or City, not Sell Patents. It doesn't help pay:
Power Plant still needs 11 MegaCredits. Other Players' Standard Projects give nothing.

**Why:** The card: "After you pay for a standard project, except selling patents, you gain 3 MC."
The open-source game gives the 3 MegaCredits in `onStandardProject`, after paying, for the
Player's own projects other than Sell Patents. Chosen by Claude (2026-10-31), on the user's
instruction to make the remaining ticket 16 calls without asking.

**Tests:** `tests/cards/test_standard_technology.py`.

### Research Outpost's City

**Call:** Research Outpost places its City on any free Area on Mars reserved for nothing that has no
Tile of any kind next to it, an Ocean included. The card is offered only while there is such an
Area (see "A card's City or Greenery needs an Area").

**Why:** The card: "Place a city tile NEXT TO NO OTHER TILE." The open-source game places it with
`city: {on: 'isolated'}`, free land with no Tile next to it. Chosen by Claude (2026-10-31), on the
user's instruction to make the remaining ticket 16 calls without asking.

**Tests:** `tests/cards/test_research_outpost.py` and
`tests/fuzzing/test_invariants.py::test_research_outposts_area_decision_offering_an_area_next_to_a_tile_breaks_an_invariant`.

### Taking from any Player

**Call:** A card with a red-bordered icon ("decrease any heat production 2 steps", "remove up to 3
plants from any player") lets its Player pick the Player it takes from, with a "target" Decision
once the card's other effects and its Tiles are done, and before Mars University's discard.
- **Lowering Production** must be carried out in full, on one Player who can lose every step
  (MegaCredit Production down to −5). The Decision offers each opponent who can. Only when no
  opponent can is the Player's own Production lowered, without a Decision. With nobody able to lose
  it, the card is not offered (Heat Trappers with nobody at 2 heat Production).
- **The Player's own Production** is checked after the card raises it: Hackers can be played at −5
  MegaCredit Production when no opponent is at −3 or more (+2 then −2), and Energy Tapping and Power
  Supply Consortium when nobody has energy Production (+1 then −1). Asteroid Mining Consortium and
  Great Escarpment Consortium need that Production anyway.
- **Removing Resources** may be left undone. The Decision offers each opponent who has some of the
  Resource, taking as much as they have up to the amount printed (Asteroid takes 2 plants from a
  Player with 2), then "Remove nothing". Sabotage offers its three Resources for each opponent,
  Hired Raiders its two, "Steal" rather than "Remove", and the Player gains what is stolen. With no
  opponent to take from, there is no Decision and nothing is taken. Ants' action is a cost, so it has
  no "Remove nothing" (see "Ants"). Mining Expedition's "Remove 2
  plants" is read as every red-bordered removal is: up to 2, or none.
- **Never offered**, as Options that only do worse for the Player: their own Resources, their own
  Production while an opponent can lose it, and partial amounts below what the card can take.
- **One target only** is taken without a Decision, as with any Decision with one Option.
- **Flooding** may remove 4 MegaCredits (up to 4) only from an opponent who owns a Tile next to its
  Ocean, or nothing. Once all 9 Oceans are placed, it places none and removes nothing.
- **Order:** taking comes last because a card's Tiles can only give an opponent more: Comet's Ocean
  sets off an opponent's Arctic Algae (2 plants), which Comet can then remove.

The game log says "Player 1 lowers Player 3's heat Production by 2.", "Player 1 lowers their own
heat Production by 2.", "Player 1 removes 3 plants from Player 2.", "Player 1 steals 2 steel from
Player 2." or "Player 1 removes nothing with Asteroid."

**Why:**
- The rulebook, as two rules sites quote it (rules.dized.com, "Red-bordered icons"; rulespal.com):
  a red border "targets any player (you or an opponent)"; removing red-bordered Resources "may
  also be performed partly, or not at all"; reducing red-bordered Production "must be performed, so
  if your opponent doesn't have that production, then you must lower your own production or not
  play the card at all".
- The open-source game asks for a Player who can lose all the steps (`canHaveProductionReduced`),
  offers the Player themselves too, and doesn't offer the card without one. It offers the
  opponents with some of a Resource, taking up to the amount, plus "Do not remove", and Flooding's
  adjacent opponents plus "Don't remove".
- Lowering an opponent's Production leaves the Player better off than lowering their own, so
  their own is left out while an opponent can lose it (see "When the 0 °C Ocean is placed": an
  Option that only does worse is not offered). Taking less than the card allows lies between
  taking it all and taking nothing.
- Raising their own Production before lowering it is never worse for the Player, so it is the
  order used (as for Immigrant City's own City). The open-source game checks the Production before
  the card raises it, so it refuses Hackers at −5, and Energy Tapping with nobody having energy
  Production. The rulebook doesn't order a card's effects, and the user's rule that the Player
  orders simultaneous effects decides it.
- The *Comprehensive FAQ* could not be checked: the PDF and BoardGameGeek refuse the download.

Chosen by the user (2026-11-01): effect data, an `"any_player"` block (`{"production": {"heat":
-2}}`, `{"remove": [{"plants": 3}]}`, `{"steal": [...]}`) with Rust code only for Flooding's
adjacent owners; no dominated Option; status-bar buttons; the Decision after the Tiles. The rest by
Claude, on the user's instruction to make the remaining ticket 17 calls without asking.

**Tests:** `tests/rules/test_targets.py`, among them
`test_lowering_any_production_offers_exactly_the_opponents_who_can_lose_every_step` and
`test_the_target_decision_comes_after_the_cards_tiles_so_a_trigger_they_set_off_counts`; the card
files of the 17 cards that take, among them `tests/cards/test_hackers.py`, `tests/cards/test_flooding.py`,
`tests/cards/test_sabotage.py`,
`tests/cards/test_energy_tapping.py::test_with_nobody_with_energy_production_energy_tapping_raises_and_lowers_the_players_own`
and
`tests/cards/test_heat_trappers.py::test_robotic_workforce_copying_heat_trappers_picks_whose_heat_production_to_lower_again`;
and `tests/fuzzing/test_invariants.py`, among them
`test_a_target_decision_offering_the_players_own_production_while_an_opponent_can_lose_it_breaks_an_invariant`.

### What the counting cards count

**Call:**
- **Toll Station** counts the space Tags its Player's opponents have in play, not its Player's own,
  and none on played Events (see "Tags on played Events").
- **Media Archives** counts every Event played by any Player so far, its Player's own included.
- **Greenhouses** and **Energy Saving** count every City in play, whoever owns it; from ticket 18,
  the Cities off Mars too.
- **Zeppelins** counts the Cities on Mars only, as Martian Rails does.

**Why:** The cards: "for each space tag your OPPONENTS have", "for each event EVER PLAYED by all
players", "for each city tile in play" and "for each City tile ON MARS". The open-source game counts
`{tag: space, others: true}`, `{eventsPlayed: true, all: true}`, `{cities: {}}` and `{cities: {where:
'onmars'}}`. The sources agree. Chosen by Claude (2026-11-01), on the user's instruction to make
the remaining ticket 17 calls without asking.

**Tests:** `tests/cards/test_toll_station.py`, `tests/cards/test_media_archives.py`,
`tests/cards/test_greenhouses.py`, `tests/cards/test_energy_saving.py` and
`tests/cards/test_zeppelins.py`.

### Special Tiles

**Call:**
- A **special Tile** is printed with its card's symbol and belongs to the card's Player. With no
  placement restriction printed ("Place this tile": Commercial District, Nuclear Zone, Restricted
  Area), it goes on any free Area on Mars reserved for nothing, next to a City too. Others go where
  their card says: Natural Preserve next to no other Tile, Industrial Center next to a City (whoever
  owns it; Capital's counts), Lava Flows on one of the four volcanoes, Mohole Area on a free Area
  reserved for Oceans (it is no Ocean: Oceans don't rise, and it takes the Area from the Oceans),
  Mining Rights on land with a steel or titanium placement bonus, and Mining Area on such land next
  to another of its Player's Tiles.
- **Capital's City** is a special Tile and a City: City rules place it (never next to another
  City), and it counts as a City everywhere, for Mayor, Martian Rails, Rover Construction, Immigrant
  City, Commercial District and a City's Greeneries in the final scoring. It scores 1 more Victory
  Point for each Ocean next to it.
- A special Tile is one of its owner's Tiles: a Greenery goes next to it if it can, Mining Area may
  go next to it, it counts for Landlord, Natural Preserve and Research Outpost's City can't go next
  to it, and Flooding may take 4 MegaCredits from its owner. Placing one collects the Area's
  placement bonus and 2 MegaCredits per Ocean next to it, as any Tile does.
- **Mining Area and Mining Rights** raise the Production of the steel or titanium their Area's
  placement bonus gives, without a Decision: no Area of the Tharsis board has both. Robotic
  Workforce copies that step of Production.
- **Commercial District** scores 1 Victory Point for each City next to its Tile, whoever owns it.

**Why:**
- The rulebook calls these "special tiles" with no placement rule of their own beyond the card's,
  and a Greenery goes "next to another tile that you own". The open-source game places them `on:
  'land'`, `'isolated'`, `'volcanic'` or `'ocean'`, Industrial Center next to `Board.isCitySpace`
  (which includes Capital), Capital `on: 'city'`, and Mining Area next to a Player's non-Ocean Tile;
  its Mining cards offer steel or titanium only on an Area with both (Ares only).
- Robotic Workforce copying the Mining cards' Production: the ticket quotes the FAQ, and the
  open-source game's `productionBox` for them is the bonus Resource. The *Comprehensive FAQ* could
  not be checked: the PDF and BoardGameGeek refuse the download.
- Landlord counts every owned Tile but Oceans in the open-source game (`Landlord.ts`), special Tiles
  and the Cities off Mars included, as the engine already did.

Chosen by the user (2026-11-01): each special Tile drawn with its card's symbol on the board.
The rest by Claude (2026-11-01), on the user's instruction to make the remaining ticket 18 calls
without asking: special Tiles as effect data (`"special"`, with `"on"` for the card's Areas; the
card being played prints its symbol on the Tile), and Rust code only for the Mining cards'
Production.

**Tests:** the card files `tests/cards/test_nuclear_zone.py`, `test_restricted_area.py`,
`test_commercial_district.py`, `test_capital.py`, `test_natural_preserve.py`, `test_mohole_area.py`,
`test_lava_flows.py`, `test_industrial_center.py`, `test_mining_rights.py` and `test_mining_area.py`,
among them `tests/cards/test_nuclear_zone.py::test_nuclear_zones_tile_counts_as_its_owners_tile_for_a_greenery`,
`tests/cards/test_natural_preserve.py::test_flooding_may_remove_4_megacredits_from_the_owner_of_a_special_tile_next_to_its_ocean`
and `tests/cards/test_mining_rights.py::test_robotic_workforce_copies_the_production_mining_rights_tile_gave`.

### The Areas reserved for a card's City

**Call:**
- **Noctis City's Area** (E3) takes nothing but Noctis City's City, which goes there "disregarding
  normal placement restrictions", next to another City too. A City placed later still keeps away
  from it. Placing it collects the Area's 2 plants and the MegaCredits for Oceans next to it.
- **Phobos Space Haven's and Ganymede Colony's Areas** are off Mars and take nothing but their
  cards' Cities. They have no placement bonus and nothing next to them. Their Cities are Cities in
  play (Greenhouses, Energy Saving, Mayor, Landlord, and Rover Construction and Immigrant City when
  placed) but not on Mars (Martian Rails, Zeppelins).
- No other Tile is ever offered a reserved Area, and each reserved Area's card offers only it.

**Why:** The cards ("Place a City tile ON THE RESERVED AREA") and the board. The open-source game
places Noctis City on `noctisCitySpaceId` without the City rule, and Phobos Space Haven and Ganymede
Colony on their `SpaceName`s, which `getCitiesOnMars` leaves out. Chosen by Claude (2026-11-01), on
the user's instruction to make the remaining ticket 18 calls without asking.

**Tests:** `tests/rules/test_reserved_areas.py` (each reserved Area used only by its card, in
scenarios and in 40 random Games), `tests/cards/test_noctis_city.py`,
`tests/cards/test_phobos_space_haven.py` and `tests/cards/test_ganymede_colony.py`,
`tests/rules/test_milestones.py::test_mayor_counts_capitals_city_and_the_cities_off_mars`,
`tests/rules/test_awards.py::test_landlord_counts_special_tiles_and_the_cities_off_mars`, and the
fuzz invariant `each_reserved_area_used_only_by_its_card`.

### Land Claim

**Call:** Land Claim asks its Player, with an Area Decision ("Claim A1"), for a free Area on Mars
reserved for nothing that nobody has claimed, and marks it with their marker. From then on only they
may place a Tile there, an Ocean on land included (Artificial Lake); they still follow the Tile's
own placement rules, and collect the Area's placement bonus as usual. The marker is no Tile: it
counts for nothing next to it, nor for Landlord. A Greenery that could go next to its owner's Tiles
only on another Player's claimed Area goes on any other free land instead. With no Area to claim,
Land Claim is not offered. The game log says "Player 1 claims A1 with Land Claim."

**Why:** The card: "Place your marker on a non-reserved area. Only you may place a tile here." The
open-source game claims from `getNonReservedLandSpaces` and leaves claimed Areas out of every other
Player's land, and its Landlord skips the claimed Area (the comment in `Landlord.ts`). Chosen by the
user (2026-11-01): the claim is a marker, not a Tile, shown as a ring in the Player's colour. The
rest by Claude, on the user's instruction to make the remaining ticket 18 calls without asking:
effect data `"claim_area": true`, and at most one claim on the board, as there is one Land Claim.

**Tests:** `tests/cards/test_land_claim.py`, among them
`test_a_claimed_area_is_kept_from_every_other_tile_an_ocean_on_land_included`, and the fuzz
invariant tests in `tests/fuzzing/test_invariants.py`, among them
`test_a_tile_on_land_another_player_claimed_breaks_an_invariant`.

### Card Resources

**Call:** A card holds Card Resources only if printed with one to hold, of one kind, and only once
played. Those 9 cards hold 0 when played, unless they say otherwise (Nitrite Reducing Bacteria's 3);
the Player View's `"card_resources"` lists each such played card, even with 0 on it, and the GUI
draws the count next to the Card Resource's icon. They count for Victory Points only on the card
they are on: 1 per 4 microbes on Tardigrades, with 3 microbes on it giving none. Search for Life
scores 3 with at least 1 science on it, and more scores no more. Olympus Conference's Victory Point
is fixed, whatever is on it. The game log says "Player 1 adds 2 microbes to Tardigrades." and
"Player 1 removes 2 microbes from Regolith Eaters."

**Why:** The rulebook: "Other resources (including animals and microbes) are collected on their
respective cards, which also define what they do", and "If a card adds a non-standard resource, it
is generally placed on that same card" (rulespal.com's copy). The open-source game gives each such
card a `resourceType` and a `resourceCount`, and agrees on all 9. Chosen by Claude (2026-11-04), on
the user's instruction to make the ticket 19 calls without asking: effect data (`"holds"`,
`"card_resources"`), counted in one small array on the Game for the 18 cards that hold any (ADR
0004).

**Tests:** `tests/rules/test_card_resources.py`, among them
`test_card_resources_count_for_victory_points_as_printed`; `tests/cards/test_tardigrades.py`,
`tests/cards/test_physics_complex.py`, `tests/cards/test_search_for_life.py`.

### An action's alternatives

**Call:** An action printed with "or" is offered if at least one alternative can be carried out, and
the Player chooses with an "effects" Decision only when more than one can: "Add 1 microbe to Regolith
Eaters" or "Remove 2 microbes from Regolith Eaters to raise Oxygen 1 step". Removing needs that many
on the card itself, so with too few the action only adds, without a Decision. With the Global
Parameter at its maximum, removing is still offered and raises nothing, as with Asteroid. GHG
Producing Bacteria's step to 0 °C gives the Ocean as any step does, and the action ends once it is
placed.

**Why:**
- The cards; the open-source game's `or` behaviours with `spend: {resourcesHere}` and `autoSelect`.
- The rulebook: "You may still play cards and actions that increase the parameter" (see "Actions that
  raise a Global Parameter at its maximum").
- A Decision with one Option is no Decision, as everywhere.

Chosen by Claude (2026-11-04), on the user's instruction to make the ticket 19 calls without asking:
effect data, an action's `"choice"`, which ticket 20's cards can extend to a card's play.

**Tests:** `tests/cards/test_regolith_eaters.py`, `tests/cards/test_ghg_producing_bacteria.py`,
`tests/cards/test_nitrite_reducing_bacteria.py`, `tests/cards/test_extreme_cold_fungus.py`.

### Adding Card Resources to another card

**Call:** "Add 2 microbes to ANOTHER card" means one of the Player's own played cards that holds
microbes, of their picking, once the card's Tiles are placed. With one such card they go on it without
a Decision. Otherwise an "add_to_card" Decision offers each one, as a button and as an outlined played
card.
- **Without such a card, a card can still be played**, and the microbes are lost: Aerobraked Ammonia
  Asteroid still raises its Production ("Player 1 has no card to add 2 microbes to.").
- **So can an action**: Symbiotic Fungus is offered without another card that holds microbes, and the
  microbe is lost. Extreme-Cold Fungus only gains its plant then, without a Decision, as its other
  alternative can't be carried out.
- **CEO's Favorite Project** adds 1 of whichever kind a card holds, to a card of the Player's with at
  least 1 on it, and can't be played without one.

**Why:**
- The rulebook (rulespal.com's copy) lets a card be played without being able to do everything in
  these cases: "adding microbe resources without having any microbe project to place them on". It
  makes that exception for playing a card, not for an action.
- The open-source game's `AddResourcesToCard` takes the Player's own cards, picks by itself with one,
  and does nothing with none. It has `mustHaveCard` and `min: 1` for CEO's Favorite Project.
- **Symbiotic Fungus's action with nothing to add to**: the rulebook makes its exception for playing a
  card and doesn't speak of actions here, so the open-source game decides: it offers the action, which
  does nothing. This is no dominated Option either, as using it keeps the Player in the Generation
  without passing.
- The *Comprehensive FAQ* could not be checked: the PDF and BoardGameGeek refuse the download.

Chosen by Claude (2026-11-04), on the user's instruction to make the ticket 19 calls without asking:
effect data, `"add_to_another"`, with `"must_have_card"` and `"at_least"`; buttons and outlined cards
both, as a required choice among the played cards may be out of view.

**Tests:** `tests/cards/test_aerobraked_ammonia_asteroid.py`, `tests/cards/test_symbiotic_fungus.py`,
`tests/cards/test_extreme_cold_fungus.py`, `tests/cards/test_ceos_favorite_project.py`;
`tests/server/test_card_resources.py`.

### Ants

**Call:** Ants' action moves 1 microbe from any card to Ants, with the "target" Decision. It offers
each card of the opponents' with a microbe ("Remove 1 microbe from Player 2's Tardigrades"). Only when
they have none does it offer the Player's own cards ("from your own Tardigrades"), since taking from an
opponent is never worse than from themselves. Those include Ants itself, as "any card" does, which
moves a microbe back onto it. With no microbe on any card, the action isn't offered; with one card,
it is taken without a Decision. **"Remove nothing" is not offered.** The game log says "Player 1 moves 1 microbe
from Player 2's Tardigrades to Ants."

**Why:**
- **Against the ticket's note**, which asked for "Remove nothing" as in "Taking from any Player". The
  rulebook: "When you use an action on a blue card, you must first pay any cost stated to the left of
  the arrow", and Ants' microbe is on the left of its arrow. The open-source game agrees: its
  `RemoveResourcesFromCard` is `mandatory` when "it's a cost", with no "Do not remove". Its red border
  only says whose card it may be. The rulebook comes first. Ticket 20's Predators works the same way.
- The open-source game offers the Player's own cards alongside the opponents', and Ants itself. Taking
  from an opponent leaves the Player with one more microbe and the opponent with one fewer, so the
  Player's own only do worse while an opponent has one (see "When the 0 °C Ocean is placed"). Once none
  has, they may be worth moving, and moving one back onto Ants keeps the Player in the Generation.

Chosen by Claude (2026-11-04), on the user's instruction to make the ticket 19 calls without asking:
effect data, `"any_player": {"move_card_resource": "microbe"}` in the action, sharing the target
Decision.

**Tests:** `tests/cards/test_ants.py`, among them
`test_the_player_picks_among_the_opponents_cards_with_microbes_and_their_own_are_left_out` and
`test_with_no_opponent_to_take_from_the_player_may_move_microbes_from_their_own_cards`;
`tests/fuzzing/test_invariants.py::test_ants_taking_from_its_players_own_card_while_an_opponent_has_some_breaks_an_invariant`.

### Decomposers

**Call:** Each animal, plant or microbe Tag the Player plays adds 1 microbe to Decomposers, its own
microbe Tag included, and an Event's Tags too. Each such Tag on a card counts, so Advanced Ecosystems'
three Tags add 3 at once.

**Why:** The card ("including this"); the open-source game counts `cardTagCount` of the three Tags.
Chosen by Claude (2026-11-04), on the user's instruction to make the ticket 19 calls without asking:
effect data, `{"on": {"tag_played": ["animal", "plant", "microbe"]}, "card_resources": 1}`.

**Tests:** `tests/cards/test_decomposers.py`.

### Search for Life

**Call:** Search for Life's action spends 1 MegaCredit, then reveals the top card of the deck, which the
game log names, and discards it. If that card has a microbe Tag, a science goes on Search for Life. The
action isn't offered without a card to reveal (none in the deck or the discard pile, which is shuffled
into a new deck if the deck has run out), and stays open once a science is on the card.

**Why:** The card; the open-source game's `canAct` asks for 1 MegaCredit and a card to draw, and it logs
the card revealed and discards it. Chosen by Claude (2026-11-04), on the user's instruction to make the
ticket 19 calls without asking: Rust code for the reveal (`card_code::SEARCH_FOR_LIFE`).

**Tests:** `tests/cards/test_search_for_life.py`.

### Olympus Conference and Mars University

**Call:** Each science Tag the Player plays, its own included, makes Olympus Conference add a science to
itself or remove one to draw a card, once the card played is done, as Mars University's discard is. With
no science on it, or no card left to draw, it adds one without a Decision. Research asks twice.

With Mars University in play, each science Tag sets off both. While both have something due, one
"olympus_conference" Decision offers both cards' Options together: "Add 1 science to Olympus
Conference", "Remove 1 science from Olympus Conference to draw a card", "Discard Mine to draw a card"
for each card in the hand, and "Keep the hand". The Option picked is carried out and the rest stay due,
so the Player orders them by picking. With no card in the hand, Olympus Conference comes first, as its
draw may give them one to discard.

**Why:**
- The Player orders simultaneous effects, and a Decision is skipped only when one order is never worse
  (the user's rule, see "When the 0 °C Ocean is placed"). **No order dominates here.** Discarding first
  lets the Player see the card drawn and then still keep their science. Removing first lets them see that
  card and then choose what to discard. So the Player chooses. The one exception is adding to an empty
  card, which offers no choice and can only help a later Tag, so it comes first.
- Offering the Options together orders them without a separate "which first" Decision.
- The open-source game fixes the order instead: Olympus Conference first, by its priority.
- The *Comprehensive FAQ* could not be checked: the PDF and BoardGameGeek refuse the download.

Chosen by Claude (2026-11-04), on the user's instruction to make the ticket 19 calls without asking,
which covered asking about an order that doesn't dominate. Rust code for the Decision
(`card_code::OLYMPUS_CONFERENCE`); its Trigger is effect data.

**Tests:** `tests/cards/test_olympus_conference.py`, among them
`test_research_counts_as_2_science_tags_so_it_sets_it_off_twice`,
`test_with_mars_university_the_player_orders_the_two_as_the_options_of_one_decision`,
`test_carrying_out_olympus_conference_first_leaves_mars_universitys_discard_with_the_card_drawn` and
`test_carrying_out_mars_university_first_leaves_olympus_conferences_choice`.

## Card flow

### What setup cards cost until Corporations exist (temporary)

**Call:** Until Corporations arrive (ticket 21), every Player starts with 42 MegaCredits, is
dealt 10 Project Cards, and buys any of them for 3 MegaCredits each.

**Why:** 42 MegaCredits was first taken from the Beginner Corporation, but the Beginner keeps
all 10 cards for free (its card in the open-source game: "Instead of choosing from 10 cards
during setup, you get 10 cards for free"; the rules: "A Beginner Corporation gets to keep all
their cards for free"). Ticket 21 leaves the Beginner out, as it belongs to the beginner
variant. So 42 MegaCredits stays as a plain stand-in (Helion and Saturn Systems start with it
too), and setup buying works now as the Corporations will use it. Chosen by the user
(2026-10-24).

**Tests:** `tests/rules/test_buying_cards.py::test_until_corporations_exist_every_player_starts_with_42_megacredits_to_buy_cards_with`
and `test_players_buy_in_player_order_from_the_first_player_and_pay_once_everyone_is_done`.

### Buying stays hidden until every Player is done

**Call:** At setup and in each Research phase, Players buy one at a time in player order from
the first player, with a chain of single picks ("Buy …", then Done). Nothing is paid and no
card moves until the last Player is done: then every Player pays 3 MegaCredits per card
bought, takes those cards into their hand, and the rest go face down to the discard pile. The
game log then says how many cards each Player bought, never which. Until then, another
Player's view shows neither the cards dealt nor those bought, and MegaCredits and hand sizes
as they were.

**Why:** Buying is simultaneous at the table; the engine asks one Player at a time (ADR 0002),
so a later Player must not see what an earlier Player bought, even as falling MegaCredits. The
open-source game lets each player confirm on their own, which shows MegaCredits early. Chosen
by the user (2026-10-24).

**Tests:** `tests/engine/test_views.py::test_while_players_buy_at_setup_no_player_view_shows_what_another_player_was_dealt_or_bought`,
`test_while_players_buy_in_a_research_phase_no_player_view_shows_what_another_player_drew_or_bought`
and `test_once_everyone_is_done_buying_the_log_says_how_many_cards_each_player_bought_but_not_which`.

### The Research phase, and who is asked to buy

**Call:** From Generation 2, after the Player Order phase, each Player draws 4 cards in player
order from the first player, then buys as above. With the Draft on (the default), the Draft
replaces the drawing (see "Draft" below), and Players buy from the cards they kept.
A Player is asked only while they can buy another card: one is left and they can pay for it on
top of those already bought. A Player who cannot afford any card, or has bought every card
dealt, is passed over without a Decision; their cards not bought are discarded.

**Why:** The rulebook's Research phase: each Player draws 4 cards and buys any of them for 3
MegaCredits each, discarding the rest. A Decision whose only Option is Done changes nothing,
the same reasoning as not offering End Turn when it changes nothing. Chosen by Claude
(2026-10-24), on the user's instruction to make the remaining ticket 09 calls without asking.

**Tests:** `tests/rules/test_buying_cards.py::test_from_generation_2_the_research_phase_deals_each_player_4_cards_in_player_order`,
`test_a_player_buys_only_as_many_cards_as_they_can_pay_for_and_with_none_is_not_asked` and
`test_a_player_who_buys_every_card_dealt_is_done_without_picking_done`.

### Sell Patents

**Call:** Sell Patents, printed first among the Standard Projects, is offered whenever the Player
has a card in hand. It is a chain of single picks: each card sold goes face down to the
discard pile and gains 1 MegaCredit at once. Done is offered only once a card is sold, and
selling the last card in hand ends the Action without it. The game log says how many patents
were sold, never which.

**Why:** The rulebook: discard any number of cards from your hand to gain 1 MegaCredit each.
Selling none would only waste an Action, an Option that changes nothing for the better. Chosen
by Claude (2026-10-24), on the user's instruction to make the remaining ticket 09 calls without
asking.

**Tests:** `tests/rules/test_sell_patents.py`.

### The discard pile lies face down

**Call:** A Player View shows only how many cards are in the discard pile; the full view lists
them.

**Why:** The rules: "cards are always discarded face down". Chosen by the user (2026-10-24).

**Tests:** `tests/rules/test_deck.py::test_a_scenario_puts_cards_face_down_in_the_discard_pile_which_only_the_full_view_lists`
and `tests/rules/test_sell_patents.py::test_selling_patents_is_a_chain_of_single_picks_ending_with_done`.

### When the deck runs out

**Call:** When a Player must draw from an empty deck, the discard pile is shuffled with the
Game's own random numbers into a new deck, and the game log says so. Cards being bought from
in that moment are not in the discard pile yet. If the discard pile is empty too, the Player
draws no more cards.

**Why:** The rulebook shuffles the discard pile into a new deck when the deck runs out. Both
empty takes every card in hands, being bought or played; the rulebook is silent, and drawing
nothing is the only possibility. Chosen by Claude (2026-10-24), on the user's instruction to make
the remaining ticket 09 calls without asking.

**Tests:** `tests/rules/test_deck.py::test_when_the_deck_runs_out_the_discard_pile_is_shuffled_into_a_new_deck`,
`test_the_reshuffled_deck_comes_from_the_games_own_random_numbers`,
`tests/rules/test_buying_cards.py::test_the_research_phase_draws_from_the_reshuffled_discard_pile_once_the_deck_runs_out`
and `tests/rules/test_placement_bonuses.py::test_a_card_bonus_with_the_deck_and_the_discard_pile_empty_draws_nothing`.

### Dealing the implemented cards first (a setting, temporary)

**Call:** A Game setting, `implemented_cards_first`, shuffles the implemented cards and puts them
on top of the shuffled deck, so with 2 Players almost all of them are dealt at setup. Off (the
engine's default), the deck is shuffled as the rules say. The GUI's setup screen has it on by
default until every card is implemented; the fuzzer has it on for seeds 4 to 7, 12 to 15 and so
on. Cards not implemented can still be dealt, bought, held and sold, but are never offered
to play.

**Why:** Not a rules question but a play-testing aid: with 23 of 208 cards implemented, about 1
dealt card in 9 would be playable. Chosen by the user (2026-10-24).

**Tests:** `tests/rules/test_deck.py::test_while_most_cards_are_not_implemented_a_new_game_can_deal_the_implemented_ones_first`,
`test_a_new_game_deals_from_the_whole_shuffled_deck_by_default` and
`tests/rules/test_playing_cards.py::test_a_card_that_is_not_implemented_yet_is_never_offered`.

## Draft

### The Draft is on unless switched off, from Generation 2 only

**Call:** Every Research phase from Generation 2 has the Draft, unless the Game's `draft` setting
is off: `tm_engine.Game(draft=True)`, Scenarios (`"draft": true`), the server's `new_game` and
the GUI's setup screen all default to on. A Replay whose settings or Scenario have no `draft`
(saved before ticket 10) reads as off, as it was played. There is no Draft at setup: each Player still buys
from the 10 cards dealt.

**Why:** ADR 0003 has the Draft on by default in the GUI and in AI training. The rulebook:
"Drafting is not used during the first generation since the first Research phase is skipped".
The open-source game's draft at setup is an optional variant of its own, not a rule. The
default was chosen by the user (2026-10-24); no Draft at setup by Claude, on the rulebook.

**Tests:** `tests/rules/test_draft.py::test_the_draft_is_on_unless_switched_off_and_a_replay_from_before_the_draft_existed_reads_as_off`,
`test_a_scenario_has_the_draft_unless_switched_off_but_one_in_a_replay_from_before_the_draft_existed_does_not`,
`test_there_is_no_draft_at_setup_where_each_player_buys_from_the_10_cards_dealt`,
`test_with_the_draft_off_the_research_phase_deals_4_cards_straight_to_buy_from` and
`tests/server/test_new_game.py::test_a_new_game_has_the_draft_unless_it_is_switched_off`.

### Picks, passing and the passing direction

**Call:** Each Player, in player order from the first player, is dealt 4 cards to draft. Every
Player keeps one of the cards they hold, one Player at a time in player order from the first
player; once all have kept one, everyone passes the rest at the same moment, and each picks
again from the cards passed to them. Cards go clockwise, to the next Player as the Turns go
(Player 1 to Player 2), in even Generations, and counter-clockwise, to the Player before, in
odd ones. With 2 Players both directions reach
the other Player. Once every card is kept, the Draft is over and each Player buys from the
cards they kept, as in "Buying stays hidden until every Player is done".

**Why:** The rulebook's Draft variant: each Player keeps 1 card and passes the rest, until all
4 are kept; "Cards are passed clockwise during even-numbered generations and counter-clockwise
during odd-numbered generations", and play proceeds clockwise. The open-source game agrees: it
passes to the player after in even Generations and before in odd ones. Neither has a rule of
its own for 2 Players. Picks are simultaneous at the table, so the engine asks one Player at a
time (ADR 0002) and moves no card until everyone has picked. Chosen by Claude (2026-10-24), as
the sources agree.

**Tests:** `tests/rules/test_draft.py::test_from_generation_2_each_player_is_dealt_4_cards_to_draft_and_the_first_player_keeps_one_first`,
`test_players_keep_a_card_in_player_order_and_the_rest_pass_on_only_once_everyone_has_kept_one`,
`test_cards_pass_clockwise_in_even_generations_and_counter_clockwise_in_odd_ones` and
`test_with_2_players_cards_always_pass_to_the_other_player`.

### The last card is kept without a Decision

**Call:** A Player holding a single card to draft keeps it without a Decision: normally the
last card of each hand, passed on after the third pick.

**Why:** The rulebook has each Player simply receive the last card; the open-source game hands
it over automatically. A Decision with one Option changes nothing. Chosen by Claude
(2026-10-24), on the user's instruction to make the remaining calls without asking.

**Tests:** `tests/rules/test_draft.py::test_the_last_card_of_each_hand_is_kept_without_a_decision_and_then_players_buy_from_the_cards_they_kept`.

### When the deck and the discard pile run out during the deal

**Call:** A Player dealt fewer than 4 cards, because the deck and the discard pile are both
empty, still drafts: each time, every Player holding cards keeps one (with a Decision only
when they hold two or more), and the rest are passed on, until every card is kept. So the
cards dealt all end up kept, though not always 4 each.

**Why:** The rulebook is silent; this keeps the Draft's own steps and ends it with every card
kept. Both piles are empty only when nearly every card is in hands or played. Chosen by Claude
(2026-10-24), on the user's instruction to make the remaining calls without asking.

**Tests:** `tests/rules/test_draft.py::test_a_player_left_with_fewer_cards_when_the_deck_and_discard_pile_run_out_still_keeps_every_card_passed`.

### What stays hidden, and what each Player sees of the cards they passed

**Call:** A Player View shows its own Player's cards to draft from and those kept, never another
Player's, and the game log names no card drafted. Each Player View also lists every set of
cards its Player passed on in the Draft, with the Generation and to whom, for the rest of the
Game. Nothing is paid during the Draft, so MegaCredits and hand sizes stay as they were.

**Why:** CONTEXT.md: the Player View is everything one Player is allowed to know, including
the cards they passed in the Draft; a Player at the table saw those cards, so the AI needn't
remember them on its own. Kept for the whole Game: chosen by the user (2026-10-24).

**Tests:** `tests/engine/test_views.py::test_while_players_draft_no_player_view_shows_what_another_player_holds_kept_or_passed`
and `tests/rules/test_draft.py::test_a_player_view_lists_the_cards_its_player_passed_and_to_whom_for_the_rest_of_the_game`.

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

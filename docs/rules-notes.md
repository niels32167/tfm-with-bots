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

The same check covers a Resource the card makes its Player lose: Moss "requires that you lose 1
plant", so it is not offered to a Player with no plant (open-source game: `player.plants >= 1`).

**Tests:** `tests/cards/test_nuclear_power.py::test_nuclear_power_cannot_take_megacredit_production_below_minus_5`,
`tests/cards/test_black_polar_dust.py::test_black_polar_dust_cannot_take_megacredit_production_below_minus_5`,
`tests/cards/test_strip_mine.py::test_strip_mine_needs_2_energy_production_to_lower`,
`tests/cards/test_rad_chem_factory.py::test_rad_chem_factory_needs_energy_production_to_lower` and
`tests/cards/test_moss.py::test_moss_needs_a_plant_to_lose`.

### The order of a card's effects

**Call:** The effects written as data are carried out in a fixed order: Resources,
Production (fixed, then per Tag or Tile), Temperature and Oxygen steps, Terraform Rating,
cards drawn, the Production change the Player chooses (see "A Production change to choose"
below), then the Tiles one at a time. A Tile that a track bonus gives along the way (the Ocean at 0 °C) is placed
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

### A card's City or Greenery needs an Area

**Call:** A card that places a City or a Greenery is offered only while there is an Area for
that Tile. Domed Crater is not offered when the only free land on Mars is next to a City, and
Urbanized Area not without free land next to 2 Cities. Oceans are the exception (see "A card's
Oceans once 9 are placed"), but Artificial Lake's Ocean, which goes on land, needs a free Area
reserved for nothing while fewer than 9 Oceans are placed. No card in the v1 set
places two Cities or two Greeneries, so one Area for each kind is enough. The same check
covers Greeneries; its first card with a Greenery on the usual Areas is Plantation (#193,
ticket 13).

**Why:** The rulebook lets a Player play a card only if they can carry out its effects, and a
Tile with no legal Area can't be placed. The open-source game also checks for an Area before
it offers such a card. Chosen by Claude in ticket 08 (2026-10-23). The test came with Domed
Crater, the first card with a City Tile (2026-10-27).

**Tests:** `tests/rules/test_playing_cards.py::test_a_card_with_a_city_tile_is_not_offered_without_an_area_for_the_city`,
`test_no_card_places_two_cities_or_two_greeneries_so_one_area_for_each_is_enough`,
`tests/cards/test_urbanized_area.py::test_urbanized_area_needs_free_land_next_to_2_cities` and
`tests/cards/test_artificial_lake.py::test_artificial_lake_is_not_offered_without_free_land`.

### Production per Tag

**Call:** A card that raises Production "for each" Tag the Player has counts their Tags once
the card is played, so its own Tags count. Tags on played Events don't count. With nothing to
count, the Production stays as it is and the game log says nothing about it. Miranda Resort
raises MegaCredit Production 1 step for each Earth Tag. It has no Earth Tag of its own.

**Why:**
- The cards that also count their own Tags say so: Power Grid's "including this" and
  Satellites' "including this one".
- Tags on Events are covered under "Tags on played Events" above.
- The open-source game adds the card's own Tags to the count while the card is being played
  (`Counter`: "include the card itself if it isn't already on the tableau"), with the same
  results.

Chosen by Claude (2026-10-27), on the user's instruction to make the remaining ticket 11 calls
without asking.

**Tests:** `tests/cards/test_miranda_resort.py`.

### Mangrove's Greenery

**Call:** Mangrove places a Greenery on any free Area reserved for Oceans. That Area need not
be next to the Player's own Tiles. From then on it is a Greenery like any other:
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
- The card says "Disregard normal placement restrictions for this".
- The rulebook gives the placement bonus for any Tile placed on an Area.
- The open-source game places Mangrove's Greenery on an Area reserved for Oceans
  (`greenery: {on: 'ocean'}`) through its normal Greenery placement, bonuses included.

The sources agree. Chosen by Claude (2026-10-27), on the user's instruction to make the
remaining ticket 11 calls without asking.

**Tests:** `tests/cards/test_mangrove.py`, among them
`test_mangroves_greenery_is_the_players_own_for_milestones_awards_and_their_next_greenery`,
`tests/fuzzing/test_invariants.py::test_mangroves_greenery_on_an_area_reserved_for_oceans_breaks_no_invariant`
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

Still to come, from the FAQ: a box that decreases any Player's Production picks its victim again
(Heat Trappers and Biomass Combustors, ticket 17); Mining Area and Mining Rights copy the
Production their Tile gave (ticket 18); a Corporation's printed Production, but not one in an
effect or action, can be copied (Mining Guild, ticket 21). Each ticket's card line says so, and
`tests/rules/test_playing_cards.py::test_every_implemented_building_card_has_its_printed_production_box_as_production_data`
fails for a building card whose production box isn't Production data.

**Tests:** `tests/cards/test_robotic_workforce.py`, among them
`test_robotic_workforce_copies_only_the_production_box_not_the_cards_other_effects` and
`test_robotic_workforce_offers_every_card_in_card_number_order_even_two_with_the_same_box`, and
`tests/fuzzing/test_invariants.py::test_robotic_workforce_offering_a_card_it_may_not_copy_breaks_an_invariant`.

### Research's two science Tags

**Call:** Research is printed with two science Tags, and both count, for Requirements, Awards
and Victory Points like any other Tags. "Counts as playing 2 science cards" also makes it two
science Tags played for the "when you play a science Tag" effects: Mars University (ticket 16)
and Olympus Conference (ticket 19).

**Why:** The card list and the open-source game both give it two science Tags. Chosen by
Claude (2026-10-29), on the user's instruction to make the remaining ticket 12 calls without
asking.

**Tests:** `tests/cards/test_research.py::test_research_counts_as_2_science_tags`,
`test_research_counts_twice_for_the_scientist_award` and
`tests/cards/test_gene_repair.py::test_gene_repair_needs_3_science_tags`.

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

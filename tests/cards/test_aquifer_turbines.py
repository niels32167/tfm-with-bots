"""#P02 Aquifer Turbines (Prelude Card): place an Ocean Tile. Increase your energy Production 2 steps. Pay 3
MegaCredits. The price is paid last, so the MegaCredits its Ocean gains for the Oceans next to it count."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    ocean,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
)


def test_aquifer_turbines_places_an_ocean_raises_energy_production_2_steps_and_costs_3_megacredits():
    game = scenario(player(prelude_cards=["aquifer_turbines"]), player(), prelude=True)

    assert areas_offered(game) == sorted(OCEAN_AREAS)
    pick(game, area="A2")

    assert area(game, "A2")["tile"]["type"] == "ocean"
    assert production(game, 0)["energy"] == 2
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["megacredits"] == 39
    assert "Player 1 pays 3 MegaCredits for Aquifer Turbines." in game.log
    assert game.decision["kind"] == "action"


def test_a_player_short_of_3_megacredits_is_offered_only_the_areas_whose_oceans_next_to_them_cover_it():
    game = scenario(player(prelude_cards=["aquifer_turbines"], megacredits=1), player(), prelude=True,
                    tiles=[ocean("E5")])

    assert areas_offered(game) == ["E4", "E6"]
    pick(game, area="E6")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["energy"] == 2


def test_with_no_megacredits_only_an_area_next_to_2_oceans_will_do():
    game = scenario(player(prelude_cards=["aquifer_turbines"], megacredits=0), player(), prelude=True,
                    tiles=[ocean("E4"), ocean("E6")])

    assert areas_offered(game) == ["E5"]


def test_helions_heat_counts_towards_it():
    game = scenario(
        player(prelude_cards=["aquifer_turbines"], corporation="helion", megacredits=0, heat=1),
        player(),
        prelude=True,
        tiles=[ocean("E5")],
    )

    assert areas_offered(game) == ["E4", "E6"]
    pick(game, area="E4")

    assert resources(game, 0)["megacredits"] == 0
    assert resources(game, 0)["heat"] == 0
    assert "Player 1 pays 2 MegaCredits and 1 heat for Aquifer Turbines." in game.log


def test_with_no_area_that_covers_it_it_cant_be_played_and_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["aquifer_turbines"], megacredits=0), player(), prelude=True,
                    tiles=[ocean("E5")])

    assert resources(game, 0)["megacredits"] == 15
    assert production(game, 0)["energy"] == 0
    assert player_board(game, 0)["played_prelude_cards"] == []


def test_with_9_oceans_placed_it_is_played_without_one_if_the_player_has_3_megacredits():
    nine_oceans = [ocean(name) for name in OCEAN_AREAS[:9]]
    enough = scenario(player(prelude_cards=["aquifer_turbines"], megacredits=3), player(), prelude=True,
                      tiles=nine_oceans)
    short = scenario(player(prelude_cards=["aquifer_turbines"], megacredits=2), player(), prelude=True,
                     tiles=nine_oceans)

    assert player_board(enough, 0)["played_prelude_cards"] == ["aquifer_turbines"]
    assert resources(enough, 0)["megacredits"] == 0
    assert production(enough, 0)["energy"] == 2
    assert player_board(short, 0)["played_prelude_cards"] == []
    assert resources(short, 0)["megacredits"] == 17


def test_the_view_names_the_prelude_card_being_played_while_its_effects_are_carried_out():
    game = scenario(player(prelude_cards=["aquifer_turbines"]), player(), prelude=True)

    assert game.full_view()["playing_prelude_card"] == "aquifer_turbines"
    pick(game, area="A2")
    assert game.full_view()["playing_prelude_card"] is None

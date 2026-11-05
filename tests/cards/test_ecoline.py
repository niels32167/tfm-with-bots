"""EcoLine (plant Tag): Effect: you may always pay 7 plants, instead of 8, to place Greenery. You
start with 2 plant Production, 3 plants and 36 MegaCredits."""

from tests.helpers import (
    end_the_generation,
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
    terraformed_mars,
)


def test_ecoline_starts_with_2_plant_production_3_plants_36_megacredits_and_a_plant_tag():
    game, first = start_as("ecoline")

    assert resources(game, first) == {
        "megacredits": 36,
        "steel": 0,
        "titanium": 0,
        "plants": 3,
        "energy": 0,
        "heat": 0,
    }
    assert production(game, first) == {
        "megacredits": 0,
        "steel": 0,
        "titanium": 0,
        "plants": 2,
        "energy": 0,
        "heat": 0,
    }
    assert player_board(game, first)["tags"]["plant"] == 1


def test_converting_7_plants_places_a_greenery():
    game = scenario(player(corporation="ecoline", plants=7), player())

    assert offered(game, "Convert 7 plants into a Greenery", plants=7)
    pick(game, "Convert 7 plants")
    pick(game, type="area", area="C3")

    assert resources(game, 0)["plants"] == 0
    assert "Player 1 converts 7 plants into a Greenery." in game.log


def test_6_plants_are_not_enough():
    game = scenario(player(corporation="ecoline", plants=6), player())

    assert not offered(game, "Convert")


def test_it_pays_7_plants_in_the_final_greenery_conversion_too():
    game = scenario(
        player(corporation="ecoline", plants=7), player(), **terraformed_mars()
    )

    end_the_generation(game)

    assert game.decision["kind"] == "final_greenery"
    pick(game, "Convert 7 plants")
    pick(game, type="area", area="C3")
    assert resources(game, 0)["plants"] == 0


def test_another_player_still_pays_8_plants():
    game = scenario(player(plants=7), player(corporation="ecoline"))

    assert not offered(game, "Convert")

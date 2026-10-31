"""#177 Water Splitting Plant (12 MegaCredits, building Tag): requires 2 Ocean Tiles. Action: spend
3 energy to raise Oxygen 1 step."""

from tests.helpers import (
    final_scores,
    ocean,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_water_splitting_plant_needs_2_oceans():
    holding = player(hand=["water_splitting_plant"])
    assert not offered(scenario(holding, player(), tiles=[ocean("A2")]), "Play Water Splitting Plant")
    assert offered(scenario(holding, player(), tiles=[ocean("A2"), ocean("A4")]), "Play Water Splitting Plant")


def test_water_splitting_plant_does_nothing_when_played():
    game = scenario(player(megacredits=12, hand=["water_splitting_plant"]), player(), tiles=[ocean("A2"), ocean("A4")])

    pick(game, "Play Water Splitting Plant (12 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.player_view(0)["oxygen"] == 0


def test_water_splitting_plants_action_spends_3_energy_to_raise_oxygen_1_step():
    game = scenario(player(energy=3, played_cards=["water_splitting_plant"]), player())

    pick(game, "Use the action of Water Splitting Plant")

    assert resources(game, 0)["energy"] == 0
    assert game.player_view(0)["oxygen"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21


def test_water_splitting_plants_action_needs_3_energy():
    game = scenario(player(energy=2, played_cards=["water_splitting_plant"]), player())

    assert not offered(game, type="use_action")


def test_water_splitting_plants_action_is_offered_at_maximum_oxygen_like_asteroid_at_maximum_temperature():
    game = scenario(player(energy=3, played_cards=["water_splitting_plant"]), player(), oxygen=14)

    pick(game, "Use the action of Water Splitting Plant")

    assert resources(game, 0)["energy"] == 0
    assert player_board(game, 0)["terraform_rating"] == 20


def test_water_splitting_plant_has_no_victory_points():
    game = scenario(player(played_cards=["water_splitting_plant"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

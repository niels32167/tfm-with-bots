"""#171 Magnetic Field Dome (5 MegaCredits, building Tag): decrease your energy Production 2 steps
and increase your plant Production 1 step. Raise your Terraform Rating 1 step."""

from tests.helpers import (
    final_scores,
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def test_magnetic_field_dome_needs_2_energy_production_to_lower():
    one = player(hand=["magnetic_field_dome"], production={"energy": 1})
    two = player(hand=["magnetic_field_dome"], production={"energy": 2})

    assert not offered(scenario(one, player()), "Play Magnetic Field Dome")
    assert offered(scenario(two, player()), "Play Magnetic Field Dome")


def test_magnetic_field_dome_trades_energy_for_plant_production_and_raises_terraform_rating_by_1():
    game = scenario(player(megacredits=5, hand=["magnetic_field_dome"], production={"energy": 2}), player())

    pick(game, "Play Magnetic Field Dome (5 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["plants"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["megacredits"] == 0


def test_magnetic_field_dome_is_worth_no_victory_points():
    game = scenario(player(played_cards=["magnetic_field_dome"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

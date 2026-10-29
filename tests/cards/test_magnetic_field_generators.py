"""#165 Magnetic Field Generators (20 MegaCredits, building Tag): decrease your energy Production 4
steps and increase your plant Production 2 steps. Raise your Terraform Rating 3 steps."""

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


def test_magnetic_field_generators_needs_4_energy_production_to_lower():
    three = player(hand=["magnetic_field_generators"], production={"energy": 3})
    four = player(hand=["magnetic_field_generators"], production={"energy": 4})

    assert not offered(scenario(three, player()), "Play Magnetic Field Generators")
    assert offered(scenario(four, player()), "Play Magnetic Field Generators")


def test_magnetic_field_generators_trades_energy_for_plant_production_and_raises_terraform_rating_by_3():
    holding = player(megacredits=20, hand=["magnetic_field_generators"], production={"energy": 4})
    game = scenario(holding, player())

    pick(game, "Play Magnetic Field Generators (20 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["plants"] == 2
    assert player_board(game, 0)["terraform_rating"] == 23
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their Terraform Rating by 3." in game.log


def test_magnetic_field_generators_is_worth_no_victory_points():
    game = scenario(player(played_cards=["magnetic_field_generators"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

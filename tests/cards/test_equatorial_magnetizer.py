"""#015 Equatorial Magnetizer (11 MegaCredits, building Tag): Action: decrease your energy
Production 1 step to increase your Terraform Rating 1 step."""

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


def test_equatorial_magnetizer_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=11, hand=["equatorial_magnetizer"]), player())

    pick(game, "Play Equatorial Magnetizer (11 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["energy"] == 0


def test_equatorial_magnetizers_action_trades_1_energy_production_step_for_1_terraform_rating():
    game = scenario(player(production={"energy": 2}, played_cards=["equatorial_magnetizer"]), player())

    pick(game, "Use the action of Equatorial Magnetizer")

    assert production(game, 0)["energy"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21


def test_equatorial_magnetizers_action_needs_energy_production_to_lower():
    game = scenario(player(played_cards=["equatorial_magnetizer"]), player())

    assert not offered(game, type="use_action")


def test_robotic_workforce_cannot_copy_equatorial_magnetizer_whose_production_box_is_its_action():
    holding = player(production={"energy": 1}, hand=["robotic_workforce"], played_cards=["equatorial_magnetizer"])

    assert not offered(scenario(holding, player()), "Play Robotic Workforce")


def test_equatorial_magnetizer_has_no_victory_points():
    game = scenario(player(played_cards=["equatorial_magnetizer"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

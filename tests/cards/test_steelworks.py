"""#103 Steelworks (15 MegaCredits, building Tag): Action: spend 4 energy to gain 2 steel and
increase Oxygen 1 step."""

from tests.helpers import (
    final_scores,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_steelworks_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=15, hand=["steelworks"]), player())

    pick(game, "Play Steelworks (15 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.player_view(0)["oxygen"] == 0


def test_steelworks_action_spends_4_energy_to_gain_2_steel_and_raise_oxygen():
    game = scenario(player(energy=4, played_cards=["steelworks"]), player())

    pick(game, "Use the action of Steelworks")

    assert resources(game, 0)["energy"] == 0
    assert resources(game, 0)["steel"] == 2
    assert game.player_view(0)["oxygen"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21


def test_steelworks_action_reaching_8_percent_oxygen_raises_temperature_too():
    game = scenario(player(energy=4, played_cards=["steelworks"]), player(), oxygen=7)

    pick(game, "Use the action of Steelworks")

    assert game.player_view(0)["oxygen"] == 8
    assert game.player_view(0)["temperature"] == -28
    assert player_board(game, 0)["terraform_rating"] == 22


def test_steelworks_action_needs_4_energy():
    assert not offered(scenario(player(energy=3, played_cards=["steelworks"]), player()), type="use_action")


def test_steelworks_has_no_victory_points():
    game = scenario(player(played_cards=["steelworks"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

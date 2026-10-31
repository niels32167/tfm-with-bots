"""#101 Ironworks (11 MegaCredits, building Tag): Action: spend 4 energy to gain 1 steel and raise
Oxygen 1 step."""

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


def test_ironworks_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=11, hand=["ironworks"]), player())

    pick(game, "Play Ironworks (11 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.player_view(0)["oxygen"] == 0


def test_ironworks_action_spends_4_energy_to_gain_1_steel_and_raise_oxygen():
    game = scenario(player(energy=5, played_cards=["ironworks"]), player(), oxygen=3)

    pick(game, "Use the action of Ironworks")

    assert resources(game, 0)["energy"] == 1
    assert resources(game, 0)["steel"] == 1
    assert game.player_view(0)["oxygen"] == 4
    assert player_board(game, 0)["terraform_rating"] == 21


def test_ironworks_action_needs_4_energy():
    assert not offered(scenario(player(energy=3, played_cards=["ironworks"]), player()), type="use_action")


def test_at_maximum_oxygen_ironworks_action_is_still_offered_and_only_gains_the_steel():
    game = scenario(player(energy=4, played_cards=["ironworks"]), player(), oxygen=14)

    pick(game, "Use the action of Ironworks")

    assert resources(game, 0)["steel"] == 1
    assert game.player_view(0)["oxygen"] == 14
    assert player_board(game, 0)["terraform_rating"] == 20
    assert "Oxygen is already at its maximum, so it does not rise." in game.log


def test_ironworks_has_no_victory_points():
    game = scenario(player(played_cards=["ironworks"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

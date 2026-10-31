"""#104 Ore Processor (13 MegaCredits, building Tag): Action: spend 4 energy to gain 1 titanium
and increase Oxygen 1 step."""

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


def test_ore_processor_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=13, hand=["ore_processor"]), player())

    pick(game, "Play Ore Processor (13 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.player_view(0)["oxygen"] == 0


def test_ore_processors_action_spends_4_energy_to_gain_1_titanium_and_raise_oxygen():
    game = scenario(player(energy=4, played_cards=["ore_processor"]), player())

    pick(game, "Use the action of Ore Processor")

    assert resources(game, 0)["energy"] == 0
    assert resources(game, 0)["titanium"] == 1
    assert game.player_view(0)["oxygen"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21


def test_ore_processors_action_needs_4_energy():
    assert not offered(scenario(player(energy=3, played_cards=["ore_processor"]), player()), type="use_action")


def test_ore_processor_has_no_victory_points():
    game = scenario(player(played_cards=["ore_processor"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

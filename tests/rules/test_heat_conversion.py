"""Converting 8 heat into a Temperature step, as an Action."""

from tests.helpers import offered, options, pick, player, player_board, resources, scenario


def test_a_player_may_convert_8_heat_into_a_temperature_step_for_one_terraform_rating():
    game = scenario(player(megacredits=0, heat=9, terraform_rating=20), player(), temperature=-10)

    pick(game, type="convert_heat")

    assert resources(game, 0)["heat"] == 1
    assert game.player_view(0)["temperature"] == -8
    assert player_board(game, 0)["terraform_rating"] == 21
    assert game.player_view(0)["actions_this_turn"] == 1
    assert game.log[-2:] == [
        "Player 1 converts 8 heat into a Temperature step.",
        "Player 1 raises Temperature to -8 °C and gains 1 Terraform Rating.",
    ]


def test_converting_heat_is_offered_with_8_heat_and_not_with_7():
    game = scenario(player(heat=8), player())
    conversions = [option for option in options(game) if option["details"]["type"] == "convert_heat"]
    assert [(option["label"], option["details"]) for option in conversions] == [
        ("Convert 8 heat into a Temperature step", {"type": "convert_heat", "heat": 8})
    ]

    assert not offered(scenario(player(heat=7), player()), type="convert_heat")


def test_at_maximum_temperature_converting_heat_costs_8_heat_and_does_nothing_else():
    game = scenario(player(megacredits=0, heat=8, terraform_rating=30), player(), temperature=8)

    pick(game, type="convert_heat")

    assert resources(game, 0)["heat"] == 0
    assert game.player_view(0)["temperature"] == 8
    assert player_board(game, 0)["terraform_rating"] == 30
    assert game.log[-1] == "Temperature is already at its maximum, so it does not rise."

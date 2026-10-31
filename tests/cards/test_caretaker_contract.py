"""#154 Caretaker Contract (Corporate Era, 3 MegaCredits, no Tags): requires 0 °C or warmer.
Action: spend 8 heat to increase your Terraform Rating 1 step."""

from tests.helpers import final_scores, offered, pick, player, player_board, resources, scenario, terraformed_mars


def test_caretaker_contract_needs_0_degrees_or_warmer():
    assert not offered(scenario(player(hand=["caretaker_contract"]), player(), temperature=-2), "Play Caretaker")
    assert offered(scenario(player(hand=["caretaker_contract"]), player(), temperature=0), "Play Caretaker")


def test_caretaker_contract_does_nothing_when_played():
    game = scenario(player(megacredits=3, hand=["caretaker_contract"]), player(), temperature=0)

    pick(game, "Play Caretaker Contract (3 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert player_board(game, 0)["terraform_rating"] == 20


def test_caretaker_contracts_action_spends_8_heat_to_raise_terraform_rating_1_step():
    game = scenario(player(heat=9, played_cards=["caretaker_contract"]), player())

    pick(game, "Use the action of Caretaker Contract")

    assert resources(game, 0)["heat"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21
    assert "Player 1 raises their Terraform Rating by 1." in game.log


def test_caretaker_contracts_action_needs_8_heat():
    game = scenario(player(heat=7, played_cards=["caretaker_contract"]), player())

    assert not offered(game, type="use_action")


def test_caretaker_contract_has_no_victory_points():
    game = scenario(player(played_cards=["caretaker_contract"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

"""#P34 UNMI Contractor (Prelude Card, Earth Tag): increase your Terraform Rating 3 steps. Draw a card."""

from tests.helpers import hand, player, player_board, scenario


def test_unmi_contractor_raises_terraform_rating_by_3_and_draws_a_card():
    game = scenario(player(prelude_cards=["unmi_contractor"]), player(), prelude=True, deck=["trees"])

    assert player_board(game, 0)["terraform_rating"] == 23
    assert hand(game, 0) == ["trees"]
    assert player_board(game, 0)["tags"]["earth"] == 1

"""#196 Lagrange Observatory (9 MegaCredits, space and science Tags, 1 Victory Point): draw 1 card."""

from tests.helpers import final_scores, hand, pick, player, scenario, terraformed_mars


def test_lagrange_observatory_draws_1_card():
    game = scenario(player(hand=["lagrange_observatory"]), player(), deck=["birds", "trees"])

    pick(game, "Play Lagrange Observatory")

    assert hand(game, 0) == ["birds"]
    assert "Player 1 draws 1 card." in game.log


def test_lagrange_observatory_is_worth_1_victory_point():
    game = scenario(player(played_cards=["lagrange_observatory"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

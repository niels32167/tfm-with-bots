"""#090 Research (Corporate Era, 11 MegaCredits, two science Tags, 1 Victory Point): counts as
playing 2 science cards. Draw 2 cards."""

from tests.helpers import award, final_scores, hand, pick, player, player_board, scenario, terraformed_mars


def test_research_draws_2_cards():
    game = scenario(player(megacredits=11, hand=["research"]), player(), deck=["birds", "trees", "mine"])

    pick(game, "Play Research (11 MegaCredits)")

    assert set(hand(game, 0)) == {"birds", "trees"}
    assert "Player 1 draws 2 cards." in game.log


def test_research_counts_as_2_science_tags():
    game = scenario(player(hand=["research"]), player(), deck=["birds", "trees"])

    pick(game, "Play Research")

    assert player_board(game, 0)["tags"]["science"] == 2


def test_research_counts_twice_for_the_scientist_award():
    game = scenario(player(played_cards=["research"]), player())

    assert award(game, "scientist")["counts"] == [2, 0]


def test_research_is_worth_1_victory_point():
    game = scenario(player(played_cards=["research"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

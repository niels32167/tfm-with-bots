"""#204 Technology Demonstration (5 MegaCredits, Event, space and science Tags): draw 2 cards."""

from tests.helpers import final_scores, hand, offered, pick, player, player_board, scenario, terraformed_mars


def test_technology_demonstration_draws_2_cards():
    game = scenario(player(megacredits=5, hand=["technology_demonstration"]), player(), deck=["birds", "trees", "mine"])

    pick(game, "Play Technology Demonstration (5 MegaCredits)")

    assert set(hand(game, 0)) == {"birds", "trees"}
    assert "Player 1 draws 2 cards." in game.log


def test_technology_demonstrations_tags_stop_counting_once_it_is_played():
    # Gene Repair requires 3 science Tags. Research has 2, and Technology Demonstration's own science
    # Tag counts only while it is being played.
    game = scenario(player(hand=["technology_demonstration", "gene_repair"], played_cards=["research"]), player())

    pick(game, "Play Technology Demonstration")

    assert player_board(game, 0)["tags"]["science"] == 2
    assert player_board(game, 0)["tags"]["space"] == 0
    assert not offered(game, "Play Gene Repair")


def test_technology_demonstration_has_no_victory_points():
    game = scenario(player(played_cards=["technology_demonstration"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

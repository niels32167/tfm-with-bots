"""#112 Bribed Committee (7 MegaCredits, Event and Earth Tags, -2 Victory Points): raise your
Terraform Rating 2 steps."""

from tests.helpers import final_scores, pick, player, player_board, scenario, terraformed_mars


def test_bribed_committee_raises_terraform_rating_by_2():
    game = scenario(player(megacredits=7, hand=["bribed_committee"]), player())

    pick(game, "Play Bribed Committee (7 MegaCredits)")

    assert player_board(game, 0)["terraform_rating"] == 22
    assert player_board(game, 0)["tags"]["earth"] == 0


def test_bribed_committee_costs_2_victory_points_though_it_lies_face_down():
    game = scenario(player(played_cards=["bribed_committee"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-2, 0]

"""#161 Convoy From Europa (15 MegaCredits, Event and space Tags): place 1 Ocean Tile and draw 1
card."""

from tests.helpers import area, final_scores, hand, pick, player, player_board, scenario, terraformed_mars


def test_convoy_from_europa_places_an_ocean_and_draws_a_card():
    game = scenario(player(megacredits=15, hand=["convoy_from_europa"]), player(), deck=["birds", "trees"])

    pick(game, "Play Convoy From Europa (15 MegaCredits)")
    assert hand(game, 0) == ["birds"]
    pick(game, area="B6")

    assert area(game, "B6")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 21
    assert "Player 1 draws 1 card." in game.log
    assert game.decision["kind"] == "action"


def test_convoy_from_europa_has_no_victory_points():
    game = scenario(player(played_cards=["convoy_from_europa"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

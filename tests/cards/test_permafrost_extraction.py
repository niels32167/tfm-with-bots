"""#191 Permafrost Extraction (8 MegaCredits, Event Tag): requires -8 °C or warmer. Place 1 Ocean
Tile."""

from tests.helpers import area, final_scores, offered, pick, player, player_board, scenario, terraformed_mars


def test_permafrost_extraction_needs_minus_8_degrees_or_warmer():
    cold = scenario(player(hand=["permafrost_extraction"]), player(), temperature=-10)
    warm_enough = scenario(player(hand=["permafrost_extraction"]), player(), temperature=-8)

    assert not offered(cold, "Play Permafrost Extraction")
    assert offered(warm_enough, "Play Permafrost Extraction")


def test_permafrost_extraction_places_an_ocean():
    game = scenario(player(megacredits=8, hand=["permafrost_extraction"]), player(), temperature=-8)

    pick(game, "Play Permafrost Extraction (8 MegaCredits)")
    pick(game, area="A2")

    assert area(game, "A2")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 21


def test_permafrost_extraction_has_no_victory_points():
    game = scenario(player(played_cards=["permafrost_extraction"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

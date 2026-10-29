"""#181 Ice Cap Melting (5 MegaCredits, Event Tag): requires +2 °C or warmer. Place 1 Ocean Tile."""

from tests.helpers import area, final_scores, offered, pick, player, player_board, scenario, terraformed_mars


def test_ice_cap_melting_needs_2_degrees_or_warmer():
    assert not offered(scenario(player(hand=["ice_cap_melting"]), player(), temperature=0), "Play Ice Cap Melting")
    assert offered(scenario(player(hand=["ice_cap_melting"]), player(), temperature=2), "Play Ice Cap Melting")


def test_ice_cap_melting_places_an_ocean():
    game = scenario(player(megacredits=5, hand=["ice_cap_melting"]), player(), temperature=2)

    pick(game, "Play Ice Cap Melting (5 MegaCredits)")
    pick(game, area="J5")

    assert area(game, "J5")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 21


def test_ice_cap_melting_has_no_victory_points():
    game = scenario(player(played_cards=["ice_cap_melting"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

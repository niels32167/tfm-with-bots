"""#119 Dust Seals (2 MegaCredits, no Tags, 1 Victory Point): requires 3 or fewer Ocean Tiles.
No other effect."""

from tests.helpers import final_scores, ocean, offered, player, scenario, terraformed_mars

THREE_OCEANS = [ocean("A2"), ocean("A4"), ocean("A5")]


def test_dust_seals_needs_3_oceans_or_fewer():
    assert offered(scenario(player(hand=["dust_seals"]), player(), tiles=THREE_OCEANS), "Play Dust Seals")
    assert not offered(
        scenario(player(hand=["dust_seals"]), player(), tiles=[*THREE_OCEANS, ocean("B6")]), "Play Dust Seals"
    )


def test_dust_seals_is_worth_1_victory_point():
    game = scenario(player(played_cards=["dust_seals"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

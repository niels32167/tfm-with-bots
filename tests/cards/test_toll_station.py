"""#099 Toll Station (12 MegaCredits, space Tag): increase your MegaCredit Production 1 step for each
space Tag your opponents have."""

from tests.helpers import final_scores, pick, player, production, scenario, terraformed_mars


def test_toll_station_counts_the_space_tags_of_every_opponent_but_not_the_players_own():
    game = scenario(
        player(hand=["toll_station"], played_cards=["methane_from_titan"]),
        player(played_cards=["asteroid_mining", "water_import_from_europa"]),
        player(played_cards=["optimal_aerobraking"]),
    )

    pick(game, "Play Toll Station (12 MegaCredits)")

    assert production(game, 0)["megacredits"] == 3


def test_toll_station_does_not_count_an_opponents_played_events():
    game = scenario(player(hand=["toll_station"]), player(played_cards=["asteroid"]))

    pick(game, "Play Toll Station")

    assert production(game, 0)["megacredits"] == 0


def test_toll_station_has_no_victory_points():
    game = scenario(player(played_cards=["toll_station"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

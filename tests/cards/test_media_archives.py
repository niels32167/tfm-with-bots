"""#107 Media Archives (8 MegaCredits, Earth Tag): gain 1 MegaCredit for each Event ever played by
all Players."""

from tests.helpers import final_scores, pick, player, resources, scenario, terraformed_mars


def test_media_archives_gains_1_megacredit_for_each_event_any_player_has_played():
    game = scenario(
        player(megacredits=8, hand=["media_archives"], played_cards=["asteroid", "space_station"]),
        player(played_cards=["comet", "deimos_down"]),
    )

    pick(game, "Play Media Archives (8 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 3


def test_media_archives_counts_an_event_played_earlier_in_the_game():
    game = scenario(player(megacredits=22, hand=["asteroid", "media_archives"]), player())

    pick(game, "Play Asteroid")
    pick(game, "Play Media Archives")

    assert resources(game, 0)["megacredits"] == 1


def test_media_archives_has_no_victory_points():
    game = scenario(player(played_cards=["media_archives"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

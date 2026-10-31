"""#109 Media Group (Corporate Era, 6 MegaCredits, Earth Tag): Effect: after you play an Event card,
you gain 3 MegaCredits."""

from tests.helpers import final_scores, pick, player, resources, scenario, terraformed_mars


def test_media_group_has_no_requirements_and_gives_nothing_for_itself():
    game = scenario(player(megacredits=6, hand=["media_group"]), player())

    pick(game, "Play Media Group (6 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


def test_with_media_group_each_event_played_gains_3_megacredits():
    game = scenario(
        player(megacredits=7, hand=["bribed_committee", "indentured_workers"], played_cards=["media_group"]), player()
    )

    pick(game, "Play Bribed Committee")
    assert resources(game, 0)["megacredits"] == 3
    pick(game, "Play Indentured Workers")

    assert resources(game, 0)["megacredits"] == 6
    assert game.log.count("Player 1's Media Group takes effect.") == 2


def test_media_group_gives_nothing_for_a_card_that_is_no_event_or_for_another_players_event():
    game = scenario(player(megacredits=11, hand=["mine", "bribed_committee"]), player(played_cards=["media_group"]))
    holding = player(megacredits=4, hand=["mine"], played_cards=["media_group"])

    pick(game, "Play Bribed Committee")
    assert resources(game, 1)["megacredits"] == 42
    alone = scenario(holding, player())
    pick(alone, "Play Mine")
    assert resources(alone, 0)["megacredits"] == 0


def test_media_group_is_worth_no_victory_points():
    game = scenario(player(played_cards=["media_group"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

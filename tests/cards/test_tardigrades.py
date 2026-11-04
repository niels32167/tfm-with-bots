"""#049 Tardigrades (4 MegaCredits, microbe Tag): Action: add 1 microbe to this card. 1 Victory Point
per 4 microbes on this card."""

from tests.helpers import (
    card_resources,
    end_the_generation,
    final_scores,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_tardigrades_has_no_requirements_and_starts_with_no_microbes():
    game = scenario(player(megacredits=4, hand=["tardigrades"]), player())

    pick(game, "Play Tardigrades (4 MegaCredits)")

    assert card_resources(game, 0) == {"tardigrades": 0}


def test_tardigrades_action_adds_1_microbe_to_the_card_once_per_generation():
    game = scenario(
        player(played_cards=["tardigrades"], card_resources={"tardigrades": 2}),
        player(),
    )

    pick(game, "Use the action of Tardigrades")

    assert card_resources(game, 0) == {"tardigrades": 3}
    assert "Player 1 adds 1 microbe to Tardigrades." in game.log
    assert not offered(game, "Use the action of Tardigrades")

    end_the_generation(game)
    pick(game, "Pass")  # Player 2 holds the first-player marker now.
    pick(game, "Use the action of Tardigrades")
    assert card_resources(game, 0) == {"tardigrades": 4}


def test_tardigrades_scores_1_victory_point_per_4_microbes():
    for microbes, points in ((0, 0), (3, 0), (4, 1), (7, 1), (8, 2)):
        holding = player(
            played_cards=["tardigrades"], card_resources={"tardigrades": microbes}
        )
        game = scenario(holding, player(), **terraformed_mars())

        assert final_scores(game)[0]["cards"] == points

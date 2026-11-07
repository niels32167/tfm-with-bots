"""Point Luna (Prelude's Corporation, space and Earth Tags): Effect: when you play an Earth Tag, including this, draw a
card. You start with 1 titanium Production and 38 MegaCredits."""

from tests.helpers import hand, pick, player, player_board, production, resources, scenario, start_as


def test_point_luna_starts_with_38_megacredits_1_titanium_production_and_draws_a_card_for_its_own_earth_tag():
    game, first = start_as("point_luna", prelude=True)

    assert resources(game, first)["megacredits"] == 38
    assert production(game, first)["titanium"] == 1
    assert player_board(game, first)["tags"]["space"] == 1
    assert player_board(game, first)["tags"]["earth"] == 1
    assert len(hand(game, first)) == 1
    assert f"Player {first + 1} draws 1 card." in game.log


def test_playing_an_earth_tag_draws_a_card():
    game = scenario(player(corporation="point_luna", megacredits=6, hand=["sponsors"]), player(), prelude=True,
                    deck=["mine", "trees"])

    pick(game, "Play Sponsors")

    assert hand(game, 0) == ["mine"]


def test_a_card_without_an_earth_tag_draws_none():
    game = scenario(player(corporation="point_luna", megacredits=4, hand=["mine"]), player(), prelude=True,
                    deck=["trees"])

    pick(game, "Play Mine")

    assert hand(game, 0) == []


def test_a_wild_tag_is_no_earth_tag_when_played():
    game = scenario(player(corporation="point_luna", megacredits=4, hand=["research_coordination"]), player(),
                    prelude=True, deck=["trees"])

    pick(game, "Play Research Coordination")

    assert hand(game, 0) == []

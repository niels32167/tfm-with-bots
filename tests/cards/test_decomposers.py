"""#131 Decomposers (5 MegaCredits, microbe Tag, requires 3 % Oxygen): Effect: when you play an
animal, plant or microbe Tag, including this, add a microbe to this card. 1 Victory Point per 3
microbes on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_decomposers_requires_3_percent_oxygen():
    hand = player(megacredits=5, hand=["decomposers"])

    assert not offered(scenario(hand, player(), oxygen=2), "Play Decomposers")
    assert offered(scenario(hand, player(), oxygen=3), "Play Decomposers")


def test_its_own_microbe_tag_adds_a_microbe_to_it():
    game = scenario(player(megacredits=5, hand=["decomposers"]), player(), oxygen=3)

    pick(game, "Play Decomposers (5 MegaCredits)")

    assert card_resources(game, 0) == {"decomposers": 1}
    assert "Player 1's Decomposers takes effect." in game.log
    assert "Player 1 adds 1 microbe to Decomposers." in game.log


def test_a_plant_tag_and_a_microbe_tag_each_add_a_microbe():
    for card, label in (("trees", "Play Trees"), ("tardigrades", "Play Tardigrades")):
        playing = player(megacredits=30, hand=[card], played_cards=["decomposers"])
        game = scenario(playing, player(), temperature=8)

        pick(game, label)

        assert card_resources(game, 0)["decomposers"] == 1, card


def test_an_animal_tag_adds_a_microbe_and_each_matching_tag_on_a_card_counts():
    # Advanced Ecosystems is printed with an animal, a microbe and a plant Tag.
    playing = player(
        megacredits=11,
        hand=["advanced_ecosystems"],
        played_cards=["decomposers", "trees", "fish"],
    )
    game = scenario(playing, player())

    pick(game, "Play Advanced Ecosystems")

    assert card_resources(game, 0)["decomposers"] == 3
    assert game.log.count("Player 1's Decomposers takes effect.") == 1
    assert "Player 1 adds 3 microbes to Decomposers." in game.log


def test_an_animal_card_adds_a_microbe():
    playing = player(megacredits=9, hand=["fish"], played_cards=["decomposers"])
    game = scenario(playing, player(production={"plants": 1}), temperature=2)

    pick(game, "Play Fish")

    assert card_resources(game, 0) == {"decomposers": 1, "fish": 0}


def test_other_tags_add_nothing():
    game = scenario(
        player(megacredits=30, hand=["mine"], played_cards=["decomposers"]), player()
    )

    pick(game, "Play Mine")

    assert card_resources(game, 0) == {"decomposers": 0}


def test_another_players_tags_add_nothing():
    game = scenario(
        player(megacredits=4, hand=["tardigrades"]),
        player(played_cards=["decomposers"]),
    )

    pick(game, "Play Tardigrades")

    assert card_resources(game, 1) == {"decomposers": 0}


def test_decomposers_scores_1_victory_point_per_3_microbes():
    for microbes, points in ((2, 0), (3, 1), (7, 2)):
        holding = player(
            played_cards=["decomposers"], card_resources={"decomposers": microbes}
        )

        assert (
            final_scores(scenario(holding, player(), **terraformed_mars()))[0]["cards"]
            == points
        )

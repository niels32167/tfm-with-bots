"""#054 Small Animals (6 MegaCredits, animal Tag, requires 6 % Oxygen): Action: add 1 animal to this
card. Decrease any plant Production 1 step. 1 Victory Point per 2 animals on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)


def test_small_animals_requires_6_percent_oxygen():
    hand = player(megacredits=6, hand=["small_animals"])
    other = player(production={"plants": 1})

    assert not offered(scenario(hand, other, oxygen=5), "Play Small Animals")
    assert offered(scenario(hand, other, oxygen=6), "Play Small Animals")


def test_it_lowers_any_plant_production_1_step():
    hand = player(megacredits=6, hand=["small_animals"])
    game = scenario(hand, player(production={"plants": 1}), oxygen=6)

    pick(game, "Play Small Animals (6 MegaCredits)")

    assert production(game, 1)["plants"] == 0
    assert card_resources(game, 0) == {"small_animals": 0}


def test_it_is_not_offered_with_nobody_to_lose_plant_production():
    hand = player(megacredits=6, hand=["small_animals"])

    assert not offered(scenario(hand, player(), oxygen=6), "Play Small Animals")


def test_the_action_adds_1_animal():
    game = scenario(player(played_cards=["small_animals"]), player())

    pick(game, "Use the action of Small Animals")

    assert card_resources(game, 0) == {"small_animals": 1}


def test_small_animals_scores_1_victory_point_per_2_animals():
    for animals, points in ((1, 0), (2, 1), (5, 2)):
        holding = player(
            played_cards=["small_animals"], card_resources={"small_animals": animals}
        )

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == points

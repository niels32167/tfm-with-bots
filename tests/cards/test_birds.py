"""#072 Birds (10 MegaCredits, animal Tag, requires 13 % Oxygen): Action: add an animal to this card.
Decrease any plant Production 2 steps. 1 Victory Point per animal on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)


def test_birds_requires_13_percent_oxygen():
    hand = player(megacredits=10, hand=["birds"])
    other = player(production={"plants": 2})

    assert not offered(scenario(hand, other, oxygen=12), "Play Birds")
    assert offered(scenario(hand, other, oxygen=13), "Play Birds")


def test_it_lowers_any_plant_production_2_steps():
    hand = player(megacredits=10, hand=["birds"])
    game = scenario(hand, player(production={"plants": 3}), oxygen=13)

    pick(game, "Play Birds (10 MegaCredits)")

    assert production(game, 1)["plants"] == 1
    assert card_resources(game, 0) == {"birds": 0}


def test_only_a_player_who_can_lose_both_steps_is_a_target():
    hand = player(megacredits=10, hand=["birds"])
    game = scenario(
        hand,
        player(production={"plants": 1}),
        player(production={"plants": 2}),
        player(production={"plants": 4}),
        oxygen=13,
    )

    pick(game, "Play Birds")

    assert labels(game) == [
        "Lower Player 3's plant Production by 2",
        "Lower Player 4's plant Production by 2",
    ]


def test_it_is_not_offered_with_nobody_to_lose_both_steps():
    hand = player(megacredits=10, hand=["birds"], production={"plants": 1})
    other = player(production={"plants": 1})

    assert not offered(scenario(hand, other, oxygen=13), "Play Birds")


def test_the_action_adds_1_animal():
    game = scenario(player(played_cards=["birds"]), player())

    pick(game, "Use the action of Birds")

    assert card_resources(game, 0) == {"birds": 1}


def test_birds_scores_1_victory_point_per_animal():
    for animals in (0, 1, 4):
        holding = player(played_cards=["birds"], card_resources={"birds": animals})

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == animals

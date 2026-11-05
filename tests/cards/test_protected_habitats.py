"""#173 Protected Habitats (5 MegaCredits): opponents may not remove your plants, animals or microbes."""

import pytest

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def protected(**fields):
    fields["played_cards"] = ["protected_habitats", *fields.get("played_cards", [])]
    return player(**fields)


def test_it_has_no_requirement_and_does_nothing_when_played():
    game = scenario(player(megacredits=5, hand=["protected_habitats"]), player())

    pick(game, "Play Protected Habitats (5 MegaCredits)")

    assert card_resources(game, 0) == {}
    assert game.decision["kind"] == "action"


@pytest.mark.parametrize(
    ("card", "cost", "label"),
    [
        ("asteroid", 14, "Play Asteroid"),
        ("comet", 21, "Play Comet"),
        ("big_asteroid", 27, "Play Big Asteroid"),
        ("deimos_down", 31, "Play Deimos Down"),
        ("giant_ice_asteroid", 36, "Play Giant Ice Asteroid"),
        ("mining_expedition", 12, "Play Mining Expedition"),
    ],
)
def test_the_cards_that_remove_plants_leave_its_player_out(card, cost, label):
    game = scenario(
        player(megacredits=cost, hand=[card]),
        protected(plants=9),
        player(plants=1),
    )

    pick(game, label)
    while game.decision["kind"] == "area":
        pick(game, area=game.decision["options"][0]["details"]["area"])

    assert game.decision["kind"] == "target"
    assert labels(game) == ["Remove 1 plant from Player 3", "Remove nothing"]


def test_with_nobody_else_to_take_from_nothing_is_removed_without_a_decision():
    game = scenario(player(megacredits=14, hand=["asteroid"]), protected(plants=9))

    pick(game, "Play Asteroid")

    assert resources(game, 1)["plants"] == 9
    assert game.decision["kind"] == "action"


def test_its_players_other_resources_may_still_be_removed():
    game = scenario(
        player(megacredits=1, hand=["sabotage"]),
        protected(megacredits=7, steel=4, titanium=3),
    )

    pick(game, "Play Sabotage")

    assert labels(game) == [
        "Remove 3 titanium from Player 2",
        "Remove 4 steel from Player 2",
        "Remove 7 MegaCredits from Player 2",
        "Remove nothing",
    ]


def test_it_does_not_protect_production():
    game = scenario(
        player(megacredits=9, hand=["fish"]),
        protected(production={"plants": 1}),
        temperature=2,
    )

    pick(game, "Play Fish")

    assert production(game, 1)["plants"] == 0


def test_ants_cannot_take_its_players_microbes():
    game = scenario(
        player(played_cards=["ants"]),
        protected(played_cards=["tardigrades"], card_resources={"tardigrades": 3}),
    )

    assert not offered(game, "Use the action of Ants")


def test_predators_cannot_take_its_players_animals_so_it_takes_from_the_next_opponent():
    game = scenario(
        player(played_cards=["predators"]),
        protected(played_cards=["fish"], card_resources={"fish": 3}),
        player(played_cards=["birds"], card_resources={"birds": 1}),
    )

    pick(game, "Use the action of Predators")

    assert card_resources(game, 1) == {"fish": 3}
    assert card_resources(game, 2) == {"birds": 0}
    assert card_resources(game, 0) == {"predators": 1}


def test_with_every_opponent_protected_predators_takes_from_its_players_own_cards():
    game = scenario(
        player(played_cards=["predators", "birds"], card_resources={"birds": 2}),
        protected(played_cards=["fish"], card_resources={"fish": 3}),
    )

    pick(game, "Use the action of Predators")

    assert card_resources(game, 0) == {"birds": 1, "predators": 1}
    assert card_resources(game, 1) == {"fish": 3}


def test_its_player_may_still_take_from_their_own_cards():
    game = scenario(
        protected(
            played_cards=["predators", "fish"],
            card_resources={"fish": 2},
        ),
        player(),
    )

    pick(game, "Use the action of Predators")

    assert card_resources(game, 0) == {"fish": 1, "predators": 1}


def test_virus_cannot_remove_its_players_animals_or_plants():
    game = scenario(
        player(megacredits=1, hand=["virus"]),
        protected(plants=5, played_cards=["fish"], card_resources={"fish": 2}),
    )

    pick(game, "Play Virus")

    assert resources(game, 1)["plants"] == 5
    assert card_resources(game, 1) == {"fish": 2}
    assert game.decision["kind"] == "action"


def test_it_scores_no_victory_points():
    played = player(played_cards=["protected_habitats"])

    assert (
        final_scores(scenario(played, player(), **terraformed_mars()))[0]["cards"] == 0
    )

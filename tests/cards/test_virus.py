"""#050 Virus (1 MegaCredit, microbe and Event Tags): remove up to 2 animals or 5 plants from any
player."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def playing(**fields):
    return player(megacredits=1, hand=["virus"], **fields)


def test_it_offers_each_opponents_animal_cards_and_plants_then_remove_nothing():
    game = scenario(
        playing(played_cards=["birds"], card_resources={"birds": 4}, plants=9),
        player(
            plants=7,
            played_cards=["fish", "small_animals", "tardigrades"],
            card_resources={"fish": 3, "small_animals": 1, "tardigrades": 2},
        ),
        player(plants=2),
    )

    pick(game, "Play Virus (1 MegaCredit)")

    assert game.decision["kind"] == "target"
    assert labels(game) == [
        "Remove 2 animals from Player 2's Fish",
        "Remove 1 animal from Player 2's Small Animals",
        "Remove 5 plants from Player 2",
        "Remove 2 plants from Player 3",
        "Remove nothing",
    ]


def test_removing_animals_takes_them_from_the_card_picked():
    game = scenario(
        playing(),
        player(played_cards=["fish"], card_resources={"fish": 3}),
    )
    pick(game, "Play Virus")

    pick(
        game,
        type="remove_card_resources",
        card="virus",
        player=1,
        **{"from": "fish"},
        kind="animal",
        amount=2,
    )

    assert card_resources(game, 1) == {"fish": 1}
    assert "Player 1 removes 2 animals from Player 2's Fish." in game.log
    assert game.decision["kind"] == "action"


def test_removing_plants_takes_as_many_as_the_player_has_up_to_5():
    game = scenario(playing(), player(plants=3))
    pick(game, "Play Virus")

    pick(game, "Remove 3 plants from Player 2")

    assert resources(game, 1)["plants"] == 0
    assert "Player 1 removes 3 plants from Player 2." in game.log


def test_it_may_remove_nothing():
    game = scenario(
        playing(),
        player(plants=3, played_cards=["fish"], card_resources={"fish": 3}),
    )
    pick(game, "Play Virus")

    pick(game, "Remove nothing")

    assert resources(game, 1)["plants"] == 3
    assert card_resources(game, 1) == {"fish": 3}
    assert "Player 1 removes nothing with Virus." in game.log


def test_the_players_own_animals_and_plants_are_never_offered():
    game = scenario(
        playing(plants=5, played_cards=["fish"], card_resources={"fish": 3}),
        player(plants=1),
    )

    pick(game, "Play Virus")

    assert labels(game) == ["Remove 1 plant from Player 2", "Remove nothing"]


def test_with_nothing_of_an_opponents_to_remove_it_can_still_be_played_and_removes_nothing():
    game = scenario(
        playing(plants=5, played_cards=["fish"], card_resources={"fish": 3}),
        player(played_cards=["birds"]),
    )

    assert offered(game, "Play Virus")
    pick(game, "Play Virus")

    assert game.decision["kind"] == "action"
    assert resources(game, 0)["plants"] == 5
    assert card_resources(game, 0) == {"fish": 3}


def test_a_card_with_microbes_is_not_offered():
    game = scenario(
        playing(),
        player(
            played_cards=["tardigrades", "fish"],
            card_resources={"tardigrades": 3, "fish": 1},
        ),
    )

    pick(game, "Play Virus")

    assert labels(game) == ["Remove 1 animal from Player 2's Fish", "Remove nothing"]


def test_it_scores_no_victory_points():
    played = player(played_cards=["virus"])

    assert (
        final_scores(scenario(played, player(), **terraformed_mars()))[0]["cards"] == 0
    )

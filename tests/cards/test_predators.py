"""#024 Predators (14 MegaCredits, animal Tag, requires 11 % Oxygen): Action: remove 1 animal from any
card and add it to this card. 1 Victory Point per animal on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_predators_requires_11_percent_oxygen():
    hand = player(megacredits=14, hand=["predators"])

    assert not offered(scenario(hand, player(), oxygen=10), "Play Predators")
    assert offered(scenario(hand, player(), oxygen=11), "Play Predators")


def test_it_holds_no_animal_when_played():
    game = scenario(player(megacredits=14, hand=["predators"]), player(), oxygen=11)

    pick(game, "Play Predators (14 MegaCredits)")

    assert card_resources(game, 0) == {"predators": 0}


def test_with_one_card_to_take_from_the_action_moves_the_animal_without_a_decision():
    game = scenario(
        player(played_cards=["predators"]),
        player(played_cards=["fish"], card_resources={"fish": 2}),
    )

    pick(game, "Use the action of Predators")

    assert card_resources(game, 0) == {"predators": 1}
    assert card_resources(game, 1) == {"fish": 1}
    assert "Player 1 moves 1 animal from Player 2's Fish to Predators." in game.log
    assert game.decision["kind"] == "action"


def test_the_player_picks_among_the_opponents_cards_with_animals_and_their_own_are_left_out():
    game = scenario(
        player(played_cards=["predators", "birds"], card_resources={"birds": 5}),
        player(played_cards=["fish", "small_animals"], card_resources={"fish": 1}),
        player(played_cards=["livestock"], card_resources={"livestock": 3}),
    )

    pick(game, "Use the action of Predators")

    assert game.decision["kind"] == "target"
    assert labels(game) == [
        "Remove 1 animal from Player 2's Fish",
        "Remove 1 animal from Player 3's Livestock",
    ]
    pick(
        game,
        type="move_card_resource",
        card="predators",
        player=2,
        **{"from": "livestock"},
        kind="animal",
    )
    assert card_resources(game, 0) == {"birds": 5, "predators": 1}
    assert card_resources(game, 2) == {"livestock": 2}


def test_remove_nothing_is_not_offered_as_the_animal_is_the_actions_cost():
    game = scenario(
        player(played_cards=["predators"]),
        player(played_cards=["fish", "birds"], card_resources={"fish": 1, "birds": 1}),
    )

    pick(game, "Use the action of Predators")

    assert not offered(game, "Remove nothing")


def test_with_no_opponent_to_take_from_the_player_may_move_animals_from_their_own_cards():
    game = scenario(
        player(
            played_cards=["predators", "fish"],
            card_resources={"predators": 4, "fish": 2},
        ),
        player(played_cards=["ants"], card_resources={"ants": 1}),
    )

    pick(game, "Use the action of Predators")

    assert labels(game) == [
        "Remove 1 animal from your own Predators",
        "Remove 1 animal from your own Fish",
    ]
    pick(game, "your own Fish")
    assert card_resources(game, 0) == {"fish": 1, "predators": 5}


def test_with_animals_only_on_predators_itself_the_action_moves_one_back_onto_it():
    game = scenario(
        player(played_cards=["predators"], card_resources={"predators": 3}), player()
    )

    pick(game, "Use the action of Predators")

    assert card_resources(game, 0) == {"predators": 3}
    assert "Player 1 moves 1 animal from their own Predators to Predators." in game.log


def test_the_action_is_not_offered_without_an_animal_on_any_card():
    game = scenario(
        player(
            played_cards=["predators", "tardigrades"], card_resources={"tardigrades": 2}
        ),
        player(played_cards=["fish"]),
    )

    assert not offered(game, "Use the action of Predators")


def test_ceos_favorite_project_may_add_to_predators():
    playing = player(
        megacredits=1,
        hand=["ceos_favorite_project"],
        played_cards=["predators", "security_fleet"],
        card_resources={"predators": 1, "security_fleet": 1},
    )
    game = scenario(playing, player())

    pick(game, "Play CEO's Favorite Project")

    assert labels(game) == [
        "Add 1 animal to Predators",
        "Add 1 fighter to Security Fleet",
    ]
    pick(game, "Add 1 fighter to Security Fleet")
    assert card_resources(game, 0) == {"predators": 1, "security_fleet": 2}


def test_predators_scores_1_victory_point_per_animal():
    for animals in (0, 1, 6):
        holding = player(
            played_cards=["predators"], card_resources={"predators": animals}
        )

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == animals

"""#033 Regolith Eaters (13 MegaCredits, microbe and science Tags): Action: add 1 microbe to this
card, or remove 2 microbes from this card to raise Oxygen 1 step."""

from tests.helpers import card_resources, labels, pick, player, scenario


def test_regolith_eaters_has_no_requirements_and_holds_microbes():
    game = scenario(player(megacredits=13, hand=["regolith_eaters"]), player())

    pick(game, "Play Regolith Eaters (13 MegaCredits)")

    assert card_resources(game, 0) == {"regolith_eaters": 0}


def test_with_fewer_than_2_microbes_the_action_just_adds_one_without_a_decision():
    game = scenario(
        player(played_cards=["regolith_eaters"], card_resources={"regolith_eaters": 1}),
        player(),
    )

    pick(game, "Use the action of Regolith Eaters")

    assert card_resources(game, 0) == {"regolith_eaters": 2}
    assert game.decision["kind"] == "action"
    assert game.player_view(0)["oxygen"] == 0


def test_with_2_microbes_the_player_chooses_between_adding_one_and_removing_two():
    game = scenario(
        player(played_cards=["regolith_eaters"], card_resources={"regolith_eaters": 2}),
        player(),
    )

    pick(game, "Use the action of Regolith Eaters")

    assert game.decision["kind"] == "effects"
    assert labels(game) == [
        "Add 1 microbe to Regolith Eaters",
        "Remove 2 microbes from Regolith Eaters to raise Oxygen 1 step",
    ]


def test_removing_2_microbes_raises_oxygen_and_the_terraform_rating():
    game = scenario(
        player(played_cards=["regolith_eaters"], card_resources={"regolith_eaters": 3}),
        player(),
    )

    pick(game, "Use the action of Regolith Eaters")
    pick(game, "Remove 2 microbes")

    view = game.player_view(0)
    assert card_resources(game, 0) == {"regolith_eaters": 1}
    assert view["oxygen"] == 1
    assert view["players"][0]["terraform_rating"] == 21
    assert "Player 1 removes 2 microbes from Regolith Eaters." in game.log
    assert game.decision["kind"] == "action"


def test_at_maximum_oxygen_the_player_may_still_remove_2_microbes():
    game = scenario(
        player(played_cards=["regolith_eaters"], card_resources={"regolith_eaters": 2}),
        player(),
        oxygen=14,
    )

    pick(game, "Use the action of Regolith Eaters")
    pick(game, "Remove 2 microbes")

    view = game.player_view(0)
    assert (view["oxygen"], view["players"][0]["terraform_rating"]) == (14, 20)
    assert card_resources(game, 0) == {"regolith_eaters": 0}

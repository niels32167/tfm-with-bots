"""#133 Symbiotic Fungus (4 MegaCredits, microbe Tag, requires -14 °C or warmer): Action: add a
microbe to ANOTHER card."""

from tests.helpers import card_resources, labels, offered, pick, player, scenario


def test_symbiotic_fungus_requires_minus_14_degrees():
    hand = player(megacredits=4, hand=["symbiotic_fungus"])

    assert not offered(
        scenario(hand, player(), temperature=-16), "Play Symbiotic Fungus"
    )
    assert offered(scenario(hand, player(), temperature=-14), "Play Symbiotic Fungus")


def test_symbiotic_fungus_holds_no_microbes_itself():
    game = scenario(
        player(megacredits=4, hand=["symbiotic_fungus"]), player(), temperature=-14
    )

    pick(game, "Play Symbiotic Fungus")

    assert card_resources(game, 0) == {}


def test_its_action_adds_a_microbe_to_the_only_other_card_that_holds_them():
    game = scenario(player(played_cards=["symbiotic_fungus", "tardigrades"]), player())

    pick(game, "Use the action of Symbiotic Fungus")

    assert card_resources(game, 0) == {"tardigrades": 1}
    assert game.decision["kind"] == "action"


def test_its_action_lets_the_player_pick_among_their_own_cards_only():
    game = scenario(
        player(played_cards=["symbiotic_fungus", "tardigrades", "regolith_eaters"]),
        player(played_cards=["ants"]),
    )

    pick(game, "Use the action of Symbiotic Fungus")

    assert labels(game) == [
        "Add 1 microbe to Regolith Eaters",
        "Add 1 microbe to Tardigrades",
    ]
    pick(game, "Add 1 microbe to Regolith Eaters")
    assert card_resources(game, 0) == {"regolith_eaters": 1, "tardigrades": 0}


def test_without_another_card_of_theirs_that_holds_microbes_its_action_is_offered_and_the_microbe_is_lost():
    game = scenario(
        player(played_cards=["symbiotic_fungus", "physics_complex"]),
        player(played_cards=["tardigrades"]),
    )

    pick(game, "Use the action of Symbiotic Fungus")

    assert card_resources(game, 0) == {"physics_complex": 0}
    assert card_resources(game, 1) == {"tardigrades": 0}
    assert "Player 1 has no card to add 1 microbe to." in game.log
    assert game.decision["kind"] == "action"

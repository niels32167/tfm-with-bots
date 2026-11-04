"""#134 Extreme-Cold Fungus (13 MegaCredits, microbe Tag, -10 °C or colder): Action: gain 1 plant, or
add 2 microbes to ANOTHER card."""

from tests.helpers import (
    card_resources,
    labels,
    offered,
    pick,
    player,
    resources,
    scenario,
)


def test_extreme_cold_fungus_must_be_played_at_minus_10_degrees_or_colder():
    hand = player(megacredits=13, hand=["extreme_cold_fungus"])

    assert offered(
        scenario(hand, player(), temperature=-10), "Play Extreme-Cold Fungus"
    )
    assert not offered(
        scenario(hand, player(), temperature=-8), "Play Extreme-Cold Fungus"
    )


def test_without_another_card_that_holds_microbes_the_action_gains_a_plant_without_a_decision():
    game = scenario(
        player(played_cards=["extreme_cold_fungus"]),
        player(played_cards=["tardigrades"]),
    )

    pick(game, "Use the action of Extreme-Cold Fungus")

    assert resources(game, 0)["plants"] == 1
    assert game.decision["kind"] == "action"


def test_with_one_the_player_chooses_between_the_plant_and_2_microbes():
    game = scenario(
        player(played_cards=["extreme_cold_fungus", "tardigrades"]), player()
    )

    pick(game, "Use the action of Extreme-Cold Fungus")

    assert game.decision["kind"] == "effects"
    assert labels(game) == ["Gain 1 plant", "Add 2 microbes to another card"]
    pick(game, "Add 2 microbes")
    assert card_resources(game, 0) == {"tardigrades": 2}
    assert resources(game, 0)["plants"] == 0
    assert game.decision["kind"] == "action"


def test_gaining_the_plant_adds_nothing():
    game = scenario(
        player(played_cards=["extreme_cold_fungus", "tardigrades"]), player()
    )

    pick(game, "Use the action of Extreme-Cold Fungus")
    pick(game, "Gain 1 plant")

    assert resources(game, 0)["plants"] == 1
    assert card_resources(game, 0) == {"tardigrades": 0}


def test_with_two_cards_the_player_picks_which_gets_the_microbes():
    game = scenario(
        player(played_cards=["extreme_cold_fungus", "tardigrades", "regolith_eaters"]),
        player(),
    )

    pick(game, "Use the action of Extreme-Cold Fungus")
    pick(game, "Add 2 microbes")
    assert game.decision["kind"] == "add_to_card"
    pick(game, "Add 2 microbes to Tardigrades")

    assert card_resources(game, 0) == {"regolith_eaters": 0, "tardigrades": 2}

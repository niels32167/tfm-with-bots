"""#P39 Psychrophiles (Prelude's Project Card, 2 MegaCredits, microbe Tag): Action: add 1 microbe to this card.
Effect: when paying for a plant card, microbes here may be used as 2 MegaCredits each. Temperature must be -20 °C or
lower."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    options,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def with_microbes(microbes: int, **fields):
    return player(played_cards=["psychrophiles"], card_resources={"psychrophiles": microbes}, **fields)


def test_psychrophiles_needs_the_temperature_at_minus_20_or_lower_and_starts_with_no_microbes():
    at_minus_20 = scenario(player(megacredits=2, hand=["psychrophiles"]), player(), prelude=True, temperature=-20)
    at_minus_18 = scenario(player(megacredits=2, hand=["psychrophiles"]), player(), prelude=True, temperature=-18)

    assert not offered(at_minus_18, "Play Psychrophiles")
    pick(at_minus_20, "Play Psychrophiles (2 MegaCredits)")
    assert card_resources(at_minus_20, 0) == {"psychrophiles": 0}


def test_its_action_adds_1_microbe_to_the_card():
    game = scenario(with_microbes(1), player(), prelude=True)

    pick(game, "Use the action of Psychrophiles")

    assert card_resources(game, 0) == {"psychrophiles": 2}


def test_its_microbes_may_pay_2_megacredits_each_for_a_plant_card():
    # Adapted Lichen costs 9 MegaCredits and has a plant Tag.
    game = scenario(with_microbes(3, megacredits=9, hand=["adapted_lichen"]), player(), prelude=True)

    pick(game, "Play Adapted Lichen")

    assert labels(game) == [
        "Pay 9 MegaCredits",
        "Pay 7 MegaCredits and 1 microbe",
        "Pay 5 MegaCredits and 2 microbes",
        "Pay 3 MegaCredits and 3 microbes",
    ]
    assert options(game)[3]["details"] == {
        "type": "payment",
        "card": "adapted_lichen",
        "megacredits": 3,
        "steel": 0,
        "titanium": 0,
        "heat": 0,
        "microbes": 3,
    }
    pick(game, "Pay 5 MegaCredits and 2 microbes")
    assert resources(game, 0)["megacredits"] == 4
    assert card_resources(game, 0) == {"psychrophiles": 1}
    assert "Player 1 plays Adapted Lichen, paying 5 MegaCredits and 2 microbes." in game.log


def test_a_plant_card_its_player_can_pay_for_only_with_the_microbes_is_offered():
    game = scenario(with_microbes(4, megacredits=1, hand=["adapted_lichen"]), player(), prelude=True)

    pick(game, "Play Adapted Lichen")

    # A fifth microbe would pay more than the 9 MegaCredits, so 4 microbes and 1 MegaCredit is the only way.
    assert resources(game, 0)["megacredits"] == 0
    assert card_resources(game, 0) == {"psychrophiles": 0}


def test_its_microbes_pay_for_no_card_without_a_plant_tag():
    game = scenario(with_microbes(3, megacredits=1, hand=["mine"]), player(), prelude=True)

    assert not offered(game, "Play Mine")


def test_psychrophiles_is_worth_no_victory_points():
    game = scenario(with_microbes(5), player(), prelude=True, **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

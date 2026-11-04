"""#034 GHG Producing Bacteria (8 MegaCredits, microbe and science Tags, requires 4 % Oxygen):
Action: add 1 microbe to this card, or remove 2 microbes to raise Temperature 1 step."""

from tests.helpers import (
    card_resources,
    labels,
    offered,
    pick,
    player,
    resources,
    scenario,
)


def test_ghg_producing_bacteria_requires_4_percent_oxygen():
    hand = player(megacredits=8, hand=["ghg_producing_bacteria"])

    assert not offered(
        scenario(hand, player(), oxygen=3), "Play GHG Producing Bacteria"
    )
    assert offered(scenario(hand, player(), oxygen=4), "Play GHG Producing Bacteria")


def test_with_fewer_than_2_microbes_the_action_just_adds_one():
    game = scenario(player(played_cards=["ghg_producing_bacteria"]), player())

    pick(game, "Use the action of GHG Producing Bacteria")

    assert card_resources(game, 0) == {"ghg_producing_bacteria": 1}


def test_with_2_microbes_the_player_chooses():
    holding = player(
        played_cards=["ghg_producing_bacteria"],
        card_resources={"ghg_producing_bacteria": 2},
    )
    game = scenario(holding, player())

    pick(game, "Use the action of GHG Producing Bacteria")

    assert labels(game) == [
        "Add 1 microbe to GHG Producing Bacteria",
        "Remove 2 microbes from GHG Producing Bacteria to raise Temperature 1 step",
    ]
    pick(game, "Remove 2 microbes")
    assert game.player_view(0)["temperature"] == -28
    assert card_resources(game, 0) == {"ghg_producing_bacteria": 0}


def test_raising_temperature_to_0_degrees_places_the_ocean_before_the_action_ends():
    holding = player(
        played_cards=["ghg_producing_bacteria"],
        card_resources={"ghg_producing_bacteria": 2},
    )
    game = scenario(holding, player(), temperature=-2)

    pick(game, "Use the action of GHG Producing Bacteria")
    pick(game, "Remove 2 microbes")
    assert game.decision["kind"] == "area"
    pick(game, "Place the Ocean on A4")

    assert game.player_view(0)["oceans"] == 1
    assert game.decision["kind"] == "action"
    assert offered(game, "End Turn")
    assert resources(game, 0)["megacredits"] == 42

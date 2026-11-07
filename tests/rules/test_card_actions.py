"""Card actions: the action of a played Active card or a Corporation is an Action its Player may take
once per Generation."""

import pytest
import tm_engine

from tests.helpers import (
    MAX_PICKS,
    end_the_generation,
    labels,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
)


def test_a_played_cards_action_is_offered_as_an_action():
    game = scenario(player(steel=1, played_cards=["space_elevator"]), player())

    assert offered(game, "Use the action of Space Elevator", type="use_action", card="space_elevator")


def test_using_an_action_carries_it_out_and_counts_as_one_action_of_the_turn():
    game = scenario(player(megacredits=0, steel=1, played_cards=["space_elevator"]), player())

    pick(game, "Use the action of Space Elevator")

    assert resources(game, 0)["steel"] == 0
    assert resources(game, 0)["megacredits"] == 5
    assert "Player 1 uses the action of Space Elevator." in game.log
    assert game.decision["player"] == 0
    assert offered(game, "End Turn")


def test_each_cards_action_can_be_used_only_once_per_generation():
    game = scenario(player(steel=2, played_cards=["space_elevator"]), player())

    pick(game, "Use the action of Space Elevator")

    assert not offered(game, type="use_action")
    assert player_board(game, 0)["used_actions"] == ["space_elevator"]
    pick(game, "End Turn")
    assert game.decision["player"] == 1
    pick(game, "Pass")
    assert game.decision["player"] == 0
    assert not offered(game, type="use_action")


def test_a_used_action_is_available_again_in_the_next_generation():
    game = scenario(player(steel=2, played_cards=["space_elevator"]), player(), draft=False)
    pick(game, "Use the action of Space Elevator")

    end_the_generation(game)

    assert player_board(game, 0)["used_actions"] == []
    assert game.decision["player"] == 1
    pick(game, "Pass")
    assert offered(game, "Use the action of Space Elevator")


# Every card with an action, and enough to use it in two Generations: Resources, energy Production
# to lower and to give the next Generation's 6 energy, and a deck to look at and draw from.
CARDS_WITH_AN_ACTION = [
    card["id"] for card in tm_engine.card_catalog() if "action" in card.get("effects", {}) and card["type"] != "corporation"
]
PLENTY = {"megacredits": 30, "steel": 5, "titanium": 5, "plants": 5, "energy": 10, "heat": 10}


def use_the_action_of(game: tm_engine.Game, card: str) -> None:
    """Player 1 uses the action of `card`, picking the first Option of each Decision it asks for,
    until they are back at an Action Decision."""
    pick(game, type="use_action", card=card)
    for _ in range(MAX_PICKS):
        if game.decision["kind"] == "action":
            return
        game.pick(0)
    raise AssertionError(f"the action of {card} had not ended after {MAX_PICKS} picks")


@pytest.mark.parametrize("card", CARDS_WITH_AN_ACTION)
def test_every_cards_action_is_used_once_per_generation_and_is_available_again_in_the_next(card):
    # Symbiotic Fungus needs another card to add to, Ants and Predators a card to take from.
    played = [card, "tardigrades"] if card == "symbiotic_fungus" else [card]
    using = player(**PLENTY, production={"energy": 6}, played_cards=played)
    holding = player(
        played_cards=["decomposers", "herbivores"], card_resources={"decomposers": 9, "herbivores": 9}
    )
    game = scenario(using, holding, deck=["mine", "trees", "comet", "asteroid"], draft=False)
    assert offered(game, type="use_action", card=card)

    use_the_action_of(game, card)

    assert player_board(game, 0)["used_actions"] == [card]
    assert not offered(game, type="use_action", card=card)
    end_the_generation(game)
    assert player_board(game, 0)["used_actions"] == []
    pick(game, "Pass")  # Player 2 is first in Generation 2.
    assert offered(game, type="use_action", card=card)


def test_a_cards_action_can_be_used_in_the_generation_it_is_played():
    game = scenario(player(megacredits=27, steel=1, hand=["space_elevator"]), player())

    pick(game, "Play Space Elevator")
    pick(game, "Pay 27 MegaCredits")

    assert offered(game, "Use the action of Space Elevator")


def test_each_card_has_its_own_action_and_using_one_leaves_the_others_open():
    game = scenario(player(steel=1, heat=8, played_cards=["space_elevator", "caretaker_contract"]), player())

    pick(game, "Use the action of Space Elevator")

    assert offered(game, "Use the action of Caretaker Contract")
    assert player_board(game, 1)["used_actions"] == []


def test_only_the_player_who_played_the_card_may_use_its_action():
    game = scenario(player(steel=1), player(steel=1, played_cards=["space_elevator"]))

    assert not offered(game, type="use_action")


def test_an_action_whose_cost_the_player_cannot_pay_is_not_offered():
    game = scenario(player(steel=0, played_cards=["space_elevator"]), player())

    assert not offered(game, type="use_action")


def test_card_actions_come_after_the_cards_to_play_in_card_number_order():
    game = scenario(
        player(megacredits=11, steel=1, heat=8, hand=["mine"], played_cards=["caretaker_contract", "space_elevator"]),
        player(),
    )

    assert labels(game)[:3] == [
        "Play Mine (4 MegaCredits)",
        "Use the action of Space Elevator",
        "Use the action of Caretaker Contract",
    ]


def test_only_active_cards_have_an_action_and_only_actions_have_a_payment_or_resource_alternatives():
    """A Prelude Card's price ("Pay 6 M€") is a `pay` too, but no other card's."""
    for card in tm_engine.card_catalog():
        effects = card.get("effects", {})
        assert "action" not in effects or card["type"] in ("active", "corporation"), card["name"]
        assert "pay" not in effects or card["type"] == "prelude", card["name"]
        assert not effects.get("resources_choice"), card["name"]
        assert "action" not in effects.get("action", {}), card["name"]


def test_an_action_places_at_most_one_tile_and_then_raises_no_global_parameter_that_could_give_another():
    # An action carries out its Tile last on its own, and the 0 °C Ocean of a Temperature or
    # Oxygen step would wait on an Area at the same time.
    for card in tm_engine.card_catalog():
        action = card.get("effects", {}).get("action", {})
        assert len(action.get("tiles", [])) <= 1, card["name"]
        if action.get("tiles"):
            assert not action["temperature"] and not action["oxygen"], card["name"]

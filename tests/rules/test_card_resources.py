"""Card Resources: the markers kept on a card rather than with a Player (see "Card Resources" in
docs/rules-notes.md). The cards that hold them, what a Scenario may put on them, and how they count
for Victory Points."""

import pytest
import tm_engine

from tests.helpers import (
    CARDS_HOLDING_CARD_RESOURCES,
    card_resources,
    final_scores,
    player,
    scenario,
    terraformed_mars,
)

CATALOG = {card["id"]: card for card in tm_engine.card_catalog()}
# Every card with a printed Victory Point count of Card Resources, what it counts, and the Victory
# Points of a position, as the cards are printed: (on the card, Victory Points).
PRINTED_VICTORY_POINTS = {
    "search_for_life": [(0, 0), (1, 3), (5, 3)],
    "ants": [(1, 0), (2, 1), (5, 2)],
    "tardigrades": [(3, 0), (4, 1), (9, 2)],
    "physics_complex": [(0, 0), (1, 2), (4, 8)],
    "decomposers": [(2, 0), (3, 1), (7, 2)],
}


@pytest.mark.parametrize(("card", "points_with"), PRINTED_VICTORY_POINTS.items())
def test_card_resources_count_for_victory_points_as_printed(card, points_with):
    for amount, points in points_with:
        holding = player(played_cards=[card], card_resources={card: amount})
        game = scenario(holding, player(), **terraformed_mars())

        assert final_scores(game)[0]["cards"] == points, f"{amount} on {card}"


def test_a_played_card_not_yet_implemented_counts_as_holding_none():
    # Birds holds animals once ticket 20 is done. Until then, nothing is on it, whatever else is in play.
    holding = player(
        played_cards=["birds", "physics_complex"], card_resources={"physics_complex": 2}
    )
    game = scenario(holding, player(), **terraformed_mars())

    assert final_scores(game)[0]["cards"] == 4


def test_a_card_counts_only_the_card_resources_on_itself():
    holding = player(
        played_cards=["tardigrades", "ants"],
        card_resources={"tardigrades": 3, "ants": 1},
    )
    game = scenario(holding, player(), **terraformed_mars())

    assert final_scores(game)[0]["cards"] == 0


def test_the_view_shows_every_played_card_that_can_hold_some_even_with_none_on_it():
    holding = player(
        played_cards=["tardigrades", "trees", "ants"], card_resources={"ants": 2}
    )
    game = scenario(holding, player(hand=["physics_complex"]))

    assert card_resources(game, 0) == {"ants": 2, "tardigrades": 0}
    assert card_resources(game, 1) == {}


def test_exactly_the_cards_printed_with_a_card_resource_to_hold_hold_one():
    holding = {
        card["id"]: card["effects"]["holds"]
        for card in CATALOG.values()
        if "holds" in card.get("effects", {})
    }

    assert holding == CARDS_HOLDING_CARD_RESOURCES


def test_every_card_that_counts_a_card_resource_holds_that_kind():
    for card in CATALOG.values():
        printed = card["victory_points"]
        if (
            "effects" in card
            and isinstance(printed, dict)
            and "card_resource" in printed["of"]
        ):
            assert card["effects"].get("holds") == printed["of"]["card_resource"], card[
                "id"
            ]


@pytest.mark.parametrize(
    ("described", "complaint"),
    [
        (
            {"played_cards": [], "card_resources": {"tardigrades": 1}},
            "which they have not played",
        ),
        (
            {"played_cards": ["trees"], "card_resources": {"trees": 1}},
            "holds no Card Resources",
        ),
        (
            {"played_cards": ["tardigrades"], "card_resources": {"tardigrades": -1}},
            "cannot hold -1",
        ),
    ],
)
def test_a_scenario_refuses_card_resources_the_rules_never_allow(described, complaint):
    with pytest.raises(ValueError, match=complaint):
        scenario(player(**described), player())


def test_card_resources_stay_with_each_copy_of_a_game():
    game = scenario(player(played_cards=["tardigrades"]), player())
    copied = game.copy()

    copied.pick(
        next(
            o["index"]
            for o in copied.decision["options"]
            if "Tardigrades" in o["label"]
        )
    )

    assert card_resources(copied, 0) == {"tardigrades": 1}
    assert card_resources(game, 0) == {"tardigrades": 0}


def test_replaying_a_scenario_puts_its_card_resources_back():
    game = scenario(
        player(played_cards=["tardigrades"], card_resources={"tardigrades": 3}),
        player(),
    )

    replayed = tm_engine.Game.from_replay(game.replay)

    assert card_resources(replayed, 0) == {"tardigrades": 3}

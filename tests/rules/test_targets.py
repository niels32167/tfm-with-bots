"""The target Decision: a card that lowers "any" Player's Production or removes "any" Player's
Resources (a red-bordered icon) lets its Player pick whom it hits. The rulebook allows any Player,
themselves included; lowering Production must be carried out in full, removing Resources is
optional. Options that only do worse are left out (see docs/rules-notes.md, "Taking from any
Player")."""

import pytest
import tm_engine

from tests.helpers import (
    labels,
    offered,
    options,
    pick,
    player,
    production,
    resources,
    scenario,
)


def targets_offered(game: tm_engine.Game) -> list[tuple[str, int | None]]:
    """The target Decision's Options, as their detail type and target Player."""
    assert game.decision["kind"] == "target"
    return [(option["details"]["type"], option["details"].get("player")) for option in options(game)]


def test_lowering_any_production_offers_exactly_the_opponents_who_can_lose_every_step():
    game = scenario(
        player(hand=["heat_trappers"], production={"heat": 5}),
        player(production={"heat": 2}),
        player(production={"heat": 1}),
        player(production={"heat": 3}),
    )

    pick(game, "Play Heat Trappers")

    assert targets_offered(game) == [("lower_production", 1), ("lower_production", 3)]
    assert labels(game) == ["Lower Player 2's heat Production by 2", "Lower Player 4's heat Production by 2"]


def test_the_target_picked_loses_the_production_and_the_player_gains_their_own():
    game = scenario(player(hand=["heat_trappers"]), player(production={"heat": 2}), player(production={"heat": 4}))

    pick(game, "Play Heat Trappers")
    pick(game, "Lower Player 3's heat Production by 2")

    assert production(game, 2)["heat"] == 2
    assert production(game, 1)["heat"] == 2
    assert production(game, 0)["energy"] == 1
    assert "Player 1 lowers Player 3's heat Production by 2." in game.log
    assert game.decision["kind"] == "action"


def test_with_one_opponent_able_to_lose_the_production_it_is_theirs_without_a_decision():
    game = scenario(player(hand=["heat_trappers"], production={"heat": 2}), player(production={"heat": 2}))

    pick(game, "Play Heat Trappers")

    assert game.decision["kind"] == "action"
    assert production(game, 1)["heat"] == 0
    assert production(game, 0)["heat"] == 2


def test_with_no_opponent_able_to_lose_the_production_the_player_lowers_their_own_without_a_decision():
    game = scenario(player(hand=["heat_trappers"], production={"heat": 3}), player(production={"heat": 1}))

    pick(game, "Play Heat Trappers")

    assert game.decision["kind"] == "action"
    assert production(game, 0)["heat"] == 1
    assert production(game, 1)["heat"] == 1
    assert "Player 1 lowers their own heat Production by 2." in game.log


def test_with_nobody_able_to_lose_the_production_the_card_is_not_offered():
    game = scenario(player(hand=["heat_trappers"], production={"heat": 1}), player(production={"heat": 1}))

    assert not offered(game, "Play Heat Trappers")


def test_removing_resources_offers_each_opponent_who_has_some_the_full_amount_up_to_the_card_and_nothing():
    game = scenario(
        player(megacredits=20, plants=9, hand=["asteroid"]),
        player(plants=5),
        player(plants=0),
        player(plants=2),
    )

    pick(game, "Play Asteroid")

    assert targets_offered(game) == [("remove_resources", 1), ("remove_resources", 3), ("remove_nothing", None)]
    assert labels(game) == ["Remove 3 plants from Player 2", "Remove 2 plants from Player 4", "Remove nothing"]


def test_removing_up_to_more_than_the_target_has_removes_all_they_have():
    game = scenario(player(megacredits=20, hand=["asteroid"]), player(plants=2))

    pick(game, "Play Asteroid")
    pick(game, "Remove 2 plants from Player 2")

    assert resources(game, 1)["plants"] == 0
    assert "Player 1 removes 2 plants from Player 2." in game.log


def test_removing_nothing_leaves_everyone_their_resources():
    game = scenario(player(megacredits=20, hand=["asteroid"]), player(plants=7))

    pick(game, "Play Asteroid")
    pick(game, "Remove nothing")

    assert resources(game, 1)["plants"] == 7
    assert "Player 1 removes nothing with Asteroid." in game.log
    assert game.decision["kind"] == "action"


def test_with_no_opponent_to_remove_from_there_is_no_decision_and_the_players_own_resources_stay():
    game = scenario(player(megacredits=20, plants=8, hand=["asteroid"]), player(plants=0))

    pick(game, "Play Asteroid")

    assert game.decision["kind"] == "action"
    assert resources(game, 0)["plants"] == 8


def test_the_target_decision_comes_after_the_cards_tiles_so_a_trigger_they_set_off_counts():
    # Player 2's Arctic Algae gains 2 plants for Comet's Ocean, which Comet can then remove.
    game = scenario(
        player(megacredits=30, hand=["comet"]), player(plants=1, played_cards=["arctic_algae"]), temperature=-20
    )

    pick(game, "Play Comet")
    assert game.decision["kind"] == "area"
    pick(game, area="A2")

    assert labels(game) == ["Remove 3 plants from Player 2", "Remove nothing"]


@pytest.mark.parametrize("card", ["heat_trappers", "asteroid"])
def test_the_target_decision_is_for_the_player_who_played_the_card(card):
    game = scenario(
        player(megacredits=20, hand=[card]),
        player(plants=5, production={"heat": 2}),
        player(plants=5, production={"heat": 2}),
    )

    pick(game, type="play_card", card=card)

    assert game.decision["player"] == 0
    assert game.decision["kind"] == "target"

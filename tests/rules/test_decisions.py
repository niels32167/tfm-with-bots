"""The engine is always either over or waiting on exactly one Decision for one Player."""

import pytest
import tm_engine

from tests.helpers import end_the_generation, funded, offered, pick, player, resources, scenario, terraformed_mars


def test_a_new_game_waits_on_the_first_player_to_choose_an_action():
    game = tm_engine.Game(seed=1)

    decision = game.decision

    assert decision["player"] == game.player_view(0)["first_player"]
    assert decision["kind"] == "action"
    assert offered(game, "Asteroid")
    assert offered(game, "Pass")
    assert not offered(game, "End Turn")


def test_every_option_has_an_index_a_label_and_structured_details():
    all_three_awards_funded = [funded("landlord", by=1), funded("banker", by=1), funded("miner", by=1)]
    game = scenario(player(megacredits=11), player(), awards=all_three_awards_funded)

    assert game.decision["options"] == [
        {
            "index": 0,
            "label": "Power Plant (11 MegaCredits)",
            "details": {"type": "standard_project", "project": "power_plant", "cost": 11},
        },
        {"index": 1, "label": "Pass", "details": {"type": "pass"}},
    ]


def test_each_decision_carries_the_next_sequence_number():
    game = tm_engine.Game(seed=1)
    first = game.decision["sequence"]

    pick(game, "Asteroid")

    assert game.decision["sequence"] == first + 1


def test_a_pick_naming_the_current_sequence_number_is_accepted():
    game = tm_engine.Game(seed=1)
    decision = game.decision

    game.pick(0, sequence=decision["sequence"])

    assert game.decision["sequence"] == decision["sequence"] + 1


def test_a_pick_carrying_a_stale_sequence_number_is_rejected():
    game = scenario(player(megacredits=42), player(), first_player=0)
    stale = game.decision["sequence"]
    pick(game, "Asteroid")

    with pytest.raises(ValueError, match="stale"):
        game.pick(0, sequence=stale)

    assert resources(game, 0)["megacredits"] == 42 - 14
    assert game.decision["sequence"] == stale + 1


def test_picking_an_option_that_is_not_offered_is_rejected():
    game = scenario(player(megacredits=7), player())  # nothing is affordable, so only Pass

    with pytest.raises(ValueError, match="no Option 1"):
        game.pick(1)


def test_nothing_can_be_picked_once_the_game_is_over():
    game = scenario(player(), player(), **terraformed_mars())
    end_the_generation(game)

    with pytest.raises(ValueError, match="over"):
        game.pick(0)

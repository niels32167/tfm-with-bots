"""The dev panel over the WebSocket: looking at any step of the Game without disturbing it, in full
view, and an edited position as a Scenario that saves, reloads and runs in a scenario test."""

import json
from typing import Any

import pytest
import tm_engine
from fastapi.testclient import TestClient

from server.app import create_app
from tests.helpers import (
    greenery,
    load_game,
    ocean,
    offered,
    pick,
    player_board,
    resources,
)
from tests.server.helpers import Gui, connect


def play_a_few_actions(gui: Gui) -> dict[str, Any]:
    """A human against a Random Bot, into the first Action phase and one Action on."""
    update = gui.skip_drafting_and_buying(gui.start(["human", "random_bot"], seed=12))
    gui.pick(update, "Asteroid")
    return gui.wait_for_human()


def test_the_dev_views_full_view_has_every_hand_and_the_deck_order_though_the_update_hides_them():
    with connect() as gui:
        update = play_a_few_actions(gui)

        shown = gui.dev_view()

    other = 1 - update["viewer"]
    assert update["view"]["players"][other]["hand"] is None
    assert update["view"]["deck"] is None
    assert shown["full_view"]["viewer"] is None
    assert shown["full_view"]["players"][other]["hand"] is not None
    assert len(shown["full_view"]["deck"]) == shown["full_view"]["deck_size"] > 0
    assert shown["seed"] == 12


def test_the_dev_views_view_is_what_the_screen_shows_at_that_step():
    with connect() as gui:
        update = play_a_few_actions(gui)
        replay = gui.save_replay()["replay"]

        latest = gui.dev_view()
        earlier = gui.dev_view(2)

    assert latest["view"] == update["view"]
    assert earlier["view"] == tm_engine.Game.from_replay(replay, step=2).player_view(
        update["viewer"]
    )
    assert earlier["view"]["deck"] is None


def test_looking_in_the_dev_view_goes_only_to_the_gui_that_asked_and_changes_nothing():
    with connect() as gui:
        update = play_a_few_actions(gui)
        before = gui.save_replay()

        for step in (None, 0, 3):
            gui.dev_view(step)

        assert gui.save_replay() == before
        gui.send(
            {"type": "pick", "sequence": update["decision"]["sequence"], "index": 0}
        )
        next_update = gui.next_update()

    assert next_update["viewer"] == update["viewer"]
    assert next_update["view"]["deck"] is None
    assert next_update["log_start"] == len(update["log"]) + update["log_start"]


def test_another_gui_gets_no_dev_view_when_one_asks():
    client = TestClient(create_app())
    with (
        client.websocket_connect("/ws") as first,
        client.websocket_connect("/ws") as second,
    ):
        gui, other = Gui(first), Gui(second)
        gui.start(["human", "human"], seed=12)
        other.next_update()

        gui.dev_view()
        gui.send({"type": "set_bot_delay", "bot_delay": 0.5})
        gui.next_update()

        # The next thing the other GUI hears is that update, with no dev view before it.
        assert other.receive()["type"] == "update"


def test_step_through_goes_forwards_and_backwards_and_shows_the_state_at_each_step():
    with connect() as gui:
        play_a_few_actions(gui)
        latest = gui.dev_view()
        replay = gui.save_replay()["replay"]
        steps = len(replay["picks"])
        assert latest["step"] == latest["steps"] == steps > 3

        walked = [gui.dev_view(step) for step in [0, 1, 2, 1, 0]]

    assert [shown["step"] for shown in walked] == [0, 1, 2, 1, 0]
    assert all(shown["steps"] == steps for shown in walked)
    for shown in walked:
        rebuilt = tm_engine.Game.from_replay(replay, step=shown["step"])
        assert shown["full_view"] == rebuilt.full_view()
        assert shown["decision"] == rebuilt.decision
        assert shown["log"] == rebuilt.log
    assert walked[0]["full_view"] == walked[4]["full_view"]
    assert walked[1]["full_view"] == walked[3]["full_view"]
    assert walked[0]["full_view"] != walked[1]["full_view"]


def test_each_step_says_which_option_was_picked_there():
    with connect() as gui:
        play_a_few_actions(gui)
        replay = gui.save_replay()["replay"]

        first = gui.dev_view(0)
        last = gui.dev_view()

    assert first["picked"] == replay["picks"][0]
    assert last["picked"] is None


def test_a_step_beyond_the_end_shows_the_latest_and_a_step_before_the_start_is_refused():
    with connect() as gui:
        play_a_few_actions(gui)
        latest = gui.dev_view()

        assert gui.dev_view(latest["steps"] + 50)["step"] == latest["steps"]
        gui.send({"type": "dev_view", "step": -1})
        assert "step" in gui.receive_error()


def test_a_step_that_is_no_whole_number_is_refused():
    with connect() as gui:
        gui.start(["human", "human"], seed=12)
        gui.send({"type": "dev_view", "step": "soon"})
        assert "whole number" in gui.receive_error()


def test_there_is_no_dev_view_before_a_game_has_started():
    with connect() as gui:
        gui.send({"type": "dev_view"})
        assert "no Game yet" in gui.receive_error()


def test_the_position_shown_at_a_step_comes_as_a_scenario_that_starts_the_same_position():
    with connect() as gui:
        play_a_few_actions(gui)
        latest = gui.dev_view()

    described = tm_engine.Game.from_scenario(latest["scenario"])
    assert (
        described.full_view()["players"][0]["hand"]
        == latest["full_view"]["players"][0]["hand"]
    )
    assert described.full_view()["deck"] == latest["full_view"]["deck"]


def scenario_file(scenario: dict[str, Any]) -> dict[str, Any]:
    """A Replay file holding `scenario`, for two humans, as the state editor loads one."""
    return {
        "controllers": ["human", "human"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }


def load(gui: Gui, file: dict[str, Any]) -> None:
    gui.send({"type": "load_replay", "file": file, "bot_delay": 0})


def edit_and_reload(gui: Gui, edit: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Edits the Scenario of the position shown, as the state editor does, and starts from it.
    Returns the update and the Replay file saved from it, read as JSON from disk would be."""
    scenario = gui.dev_view()["scenario"]
    edit(scenario)
    load(gui, scenario_file(scenario))
    update = gui.next_update()
    return update, json.loads(json.dumps(gui.save_replay()))


def give_resources(scenario: dict[str, Any]) -> None:
    scenario["players"][0]["resources"]["plants"] = 17


def give_production(scenario: dict[str, Any]) -> None:
    scenario["players"][1]["production"]["heat"] = 6


def set_global_parameters(scenario: dict[str, Any]) -> None:
    scenario["temperature"] = -12
    scenario["oxygen"] = 9
    scenario["tiles"].append(ocean("A2"))


def put_cards(scenario: dict[str, Any]) -> None:
    """Puts two cards where the edit wants them, out of wherever they are, as the editor does."""
    for pile in (
        *(
            board[name]
            for board in scenario["players"]
            for name in ("hand", "played_cards")
        ),
        scenario["deck"],
        scenario["discard"],
    ):
        pile[:] = [card for card in pile if card not in ("mine", "tardigrades")]
    scenario["players"][0]["hand"].append("mine")
    scenario["players"][1]["played_cards"].append("tardigrades")


def set_the_generation(scenario: dict[str, Any]) -> None:
    scenario["generation"] = 7


def place_a_tile(scenario: dict[str, Any]) -> None:
    scenario["tiles"].append(greenery("C3", owner=1))


def set_card_resources(scenario: dict[str, Any]) -> None:
    put_cards(scenario)
    scenario["players"][1]["card_resources"]["tardigrades"] = 4


def set_the_corporation(scenario: dict[str, Any]) -> None:
    scenario["players"][1]["corporation"] = "inventrix"
    scenario["players"][1]["first_action_due"] = True


def set_a_land_claim(scenario: dict[str, Any]) -> None:
    scenario["land_claim"] = {"area": "G1", "player": 1}


EDITS = {
    give_resources: lambda view: view["players"][0]["resources"]["plants"] == 17,
    give_production: lambda view: view["players"][1]["production"]["heat"] == 6,
    set_global_parameters: lambda view: (
        (view["temperature"], view["oxygen"], view["oceans"]) == (-12, 9, 1)
    ),
    put_cards: lambda view: (
        "mine" in view["players"][0]["hand"]
        and "tardigrades" in view["players"][1]["played_cards"]
    ),
    set_the_generation: lambda view: view["generation"] == 7,
    place_a_tile: lambda view: (
        next(area for area in view["board"] if area["area"] == "C3")["tile"]["type"]
        == "greenery"
    ),
    set_card_resources: lambda view: (
        view["players"][1]["card_resources"]["tardigrades"] == 4
    ),
    set_the_corporation: lambda view: (
        view["players"][1]["corporation"] == "inventrix"
        and view["players"][1]["first_action_due"]
    ),
    set_a_land_claim: lambda view: (
        next(area for area in view["board"] if area["area"] == "G1")["claimed_by"] == 1
    ),
}


@pytest.mark.parametrize("edit", EDITS, ids=lambda edit: edit.__name__)
def test_each_state_edit_produces_a_scenario_that_saves_reloads_and_runs_in_a_scenario_test(
    edit, tmp_path
):
    shows_the_edit = EDITS[edit]
    with connect() as gui:
        gui.skip_drafting_and_buying(gui.start(["human", "human"], seed=12))
        update, saved = edit_and_reload(gui, edit)
        shown = gui.dev_view()

        load(gui, saved)
        reloaded = gui.next_update()

    assert shows_the_edit(shown["full_view"])
    assert reloaded["view"] == update["view"]
    assert saved["replay"]["picks"] == []

    path = tmp_path / "found_in_the_gui.json"
    path.write_text(json.dumps(saved))
    game = load_game(path)
    assert shows_the_edit(game.full_view())
    assert game.full_view() == shown["full_view"]


def test_a_saved_scenario_also_goes_straight_into_from_scenario():
    with connect() as gui:
        gui.start(["human", "human"], seed=12)
        _, saved = edit_and_reload(gui, give_resources)

    scenario = saved["replay"]["start"]["scenario"]
    game = tm_engine.Game.from_scenario(scenario)
    assert resources(game, 0)["plants"] == 17


def test_a_scenario_the_engine_refuses_leaves_the_game_as_it_is():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=12)
        scenario = gui.dev_view()["scenario"]
        scenario["players"][0]["corporation"] = "no_such_corporation"

        load(gui, scenario_file(scenario))

        assert "no_such_corporation" in gui.receive_error()
        assert gui.dev_view()["full_view"]["phase"] == update["view"]["phase"]


@pytest.mark.parametrize(
    ("edit", "problem"),
    [
        (
            {
                "tiles": [
                    {"area": "C3", "tile": "city", "owner": 0},
                    {"area": "C4", "tile": "city", "owner": 1},
                ]
            },
            "the Cities on C3 and C4 are next to each other",
        ),
        (
            {
                "tiles": [
                    {
                        "area": "C3",
                        "tile": "special",
                        "card": "nuclear_zone",
                        "owner": 0,
                    }
                ]
            },
            "who has not played its card",
        ),
        (
            {
                "players": [{"played_cards": ["lava_flows"]}, {}],
                "tiles": [
                    {"area": "C3", "tile": "special", "card": "lava_flows", "owner": 0}
                ],
            },
            "is not on a volcano",
        ),
        (
            {"tiles": [{"area": "E3", "tile": "city", "owner": 0}]},
            "its owner has not played the card",
        ),
        ({"land_claim": {"area": "C3", "player": 0}}, "who has not played Land Claim"),
    ],
)
def test_a_position_real_play_cannot_reach_starts_but_the_dev_view_says_why(
    edit, problem
):
    with connect() as gui:
        load(gui, scenario_file(edit))
        gui.next_update()

        shown = gui.dev_view()

    assert any(problem in line for line in shown["position_problems"])


def test_a_position_from_real_play_has_no_problems():
    with connect() as gui:
        play_a_few_actions(gui)
        assert gui.dev_view()["position_problems"] == []


def test_a_scenario_loaded_from_a_file_plays_on_as_a_scenario_test_does(tmp_path):
    players = [
        {"resources": {"megacredits": 30}, "hand": ["mine"]},
        {
            "corporation": "united_nations_mars_initiative",
            "terraform_rating_raised": True,
        },
    ]
    with connect() as gui:
        load(gui, scenario_file({"players": players}))
        gui.next_update()
        path = tmp_path / "found_in_the_gui.json"
        path.write_text(json.dumps(gui.save_replay()))

    game = load_game(path)
    pick(game, "Play Mine")
    assert player_board(game, 0)["production"]["steel"] == 1
    assert offered(game, "End Turn")

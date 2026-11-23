"""The server hosted for anyone with its link (ADR 0014): each Visitor plays their own Game against the bots,
found again by the Visitor id their browser keeps, within limits that keep a small shared computer usable."""

import threading
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ai.controllers import REGISTERED, Registered
from server.app import Hosting, create_app
from tests.server.helpers import Gui

ALICE = "visitor-alice-0001"
BOB = "visitor-bob-0002"


def test_each_visitor_plays_their_own_game_and_finds_it_again_on_coming_back():
    client = TestClient(create_app(hosting=Hosting()))
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        alice = Gui(websocket)
        alices = alice.start(["human", "random_bot"], seed=1)
    with client.websocket_connect(f"/ws?visitor={BOB}") as websocket:
        bob = Gui(websocket)
        bob.send({"type": "undo"})
        assert "no Game yet" in bob.receive_error()
        bobs = bob.start(["human", "random_bot"], seed=2)

    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        again = Gui(websocket).next_update()

    assert (alices["seed"], bobs["seed"], again["seed"]) == (1, 2, 1)
    assert again["decision"] == alices["decision"]


def test_a_hosted_server_needs_a_visitor_id_that_looks_like_one():
    client = TestClient(create_app(hosting=Hosting()))
    for path in ("/ws", "/ws?visitor=", "/ws?visitor=a%20b", f"/ws?visitor={'x' * 65}"):
        with client.websocket_connect(path) as websocket:
            message = websocket.receive_json()
            assert message["type"] == "error"
            assert "visitor id" in message["message"]
            with pytest.raises(WebSocketDisconnect):
                websocket.receive_json()


def test_the_local_server_ignores_visitor_ids_and_shares_its_one_game():
    client = TestClient(create_app())
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        started = Gui(websocket).start(["human", "random_bot"], seed=3)
    with client.websocket_connect(f"/ws?visitor={BOB}") as websocket:
        assert Gui(websocket).next_update()["seed"] == started["seed"] == 3


class Clock:
    """A clock the test moves by hand."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_once_full_a_new_visitor_is_turned_away_until_an_idle_one_is_forgotten():
    clock = Clock()
    client = TestClient(create_app(hosting=Hosting(most_visitors=1, idle_seconds=60, clock=clock)))
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        Gui(websocket).start(["human", "random_bot"], seed=1)

    clock.now = 59
    with client.websocket_connect(f"/ws?visitor={BOB}") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "error"
        assert "full" in message["message"]
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()

    clock.now = 61
    with client.websocket_connect(f"/ws?visitor={BOB}") as websocket:
        Gui(websocket).start(["human", "random_bot"], seed=2)
    clock.now = 200
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        alice = Gui(websocket)
        alice.send({"type": "undo"})
        assert "no Game yet" in alice.receive_error()  # Alice's Game was forgotten.


def test_a_visitor_with_a_connection_open_is_never_forgotten():
    clock = Clock()
    client = TestClient(create_app(hosting=Hosting(most_visitors=1, idle_seconds=60, clock=clock)))
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        alice = Gui(websocket)
        alice.start(["human", "random_bot"], seed=1)
        clock.now = 1_000
        with client.websocket_connect(f"/ws?visitor={BOB}") as other:
            assert "full" in other.receive_json()["message"]
        assert alice.save_replay()["replay"]["start"]["settings"]["seed"] == 1


def test_a_visitor_is_told_the_server_is_hosted_and_gets_the_usual_controllers():
    client = TestClient(create_app(hosting=Hosting()))
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        websocket.receive_json()  # the card catalog
        offered = websocket.receive_json()
    with TestClient(create_app()).websocket_connect("/ws") as websocket:
        websocket.receive_json()
        local = websocket.receive_json()

    assert offered["type"] == "controllers"
    assert (offered["hosted"], local["hosted"]) == (True, False)
    assert offered["controllers"] == local["controllers"]


def test_a_visitor_can_neither_look_through_the_dev_panel_nor_tune_bots_nor_start_a_game_without_a_human():
    client = TestClient(create_app(hosting=Hosting()))
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        alice = Gui(websocket)
        for controllers, refused in (
            (["random_bot", "random_bot"], "a human"),
            (["human", "random_bot?seconds=5"], "settings"),
        ):
            alice.send({"type": "new_game", "controllers": controllers, "bot_delay": 0})
            assert refused in alice.receive_error()
            file = {
                "controllers": controllers,
                "replay": {"start": {"settings": {"players": 2, "seed": 1}}, "picks": []},
            }
            alice.send({"type": "load_replay", "file": file, "bot_delay": 0})
            assert refused in alice.receive_error()

        # Controllers named other than as a list (a dict iterates as its keys) are refused, not let past the checks.
        alice.send({"type": "new_game", "controllers": {"search": 0, "search?seconds=600": 0}, "bot_delay": 0})
        assert "list" in alice.receive_error()

        alice.start(["human", "random_bot"], seed=1)
        alice.send({"type": "dev_view"})
        assert "dev panel" in alice.receive_error()


class Counting:
    """Thinks a while over every pick, and counts how many of its kind think at once."""

    lock = threading.Lock()
    thinking = 0
    most = 0

    def pick(self, handle: Any) -> int:
        with Counting.lock:
            Counting.thinking += 1
            Counting.most = max(Counting.most, Counting.thinking)
        time.sleep(0.1)
        with Counting.lock:
            Counting.thinking -= 1
        return 0


@pytest.mark.parametrize("thinkers", [1, 2])
def test_bots_in_different_visitors_games_think_at_most_as_many_at_once_as_there_are_thinkers(monkeypatch, thinkers):
    monkeypatch.setitem(REGISTERED, "counting", Registered("Counting", Counting))
    Counting.most = 0
    client = TestClient(create_app(hosting=Hosting(thinkers=thinkers)))
    # Player 1 decides first at setup on seed 1, so each bot thinks before its human is asked anything.
    controllers = ["human", "counting"]
    with (
        client.websocket_connect(f"/ws?visitor={ALICE}") as first,
        client.websocket_connect(f"/ws?visitor={BOB}") as second,
    ):
        alice, bob = Gui(first), Gui(second)
        for gui in (alice, bob):
            gui.send({"type": "new_game", "controllers": controllers, "seed": 1, "bot_delay": 0})
        alice.wait_for_human()
        bob.wait_for_human()

    assert Counting.most == thinkers


def test_the_server_sends_the_built_gui_from_a_folder_beside_its_websocket(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<title>Terraforming Mars</title>")
    (tmp_path / "assets" / "app.js").write_text("console.log('hello')")
    client = TestClient(create_app(hosting=Hosting(), gui=tmp_path))

    assert "Terraforming Mars" in client.get("/").text
    assert client.get("/assets/app.js").text == "console.log('hello')"
    assert client.get("/missing.js").status_code == 404
    with client.websocket_connect(f"/ws?visitor={ALICE}") as websocket:
        assert websocket.receive_json()["type"] == "card_catalog"


class Made:
    """Counts how often it is made."""

    count = 0

    def __init__(self) -> None:
        Made.count += 1

    def pick(self, handle: Any) -> int:
        return 0


def test_warming_up_makes_each_available_registered_controller_once(monkeypatch):
    from server.session import warm_up

    monkeypatch.setattr("ai.controllers.REGISTERED", {"made": Registered("Made", Made)})
    Made.count = 0

    warm_up()

    assert Made.count == 1

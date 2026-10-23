"""The GUI draws cards from the card catalog, which the server passes on from the engine
module once to each new connection, before anything else."""

import tm_engine
from fastapi.testclient import TestClient

from server.app import create_app
from tests.server.helpers import Gui, connect


def test_a_new_connection_gets_the_card_catalog_before_there_is_a_game():
    with connect() as gui:
        # Asking for something there is none of yet makes sure some message comes back,
        # so the test can't wait forever.
        gui.send({"type": "undo"})

        assert "no Game yet" in gui.receive_error()
        assert gui.card_catalog == tm_engine.card_catalog()


def test_a_connection_to_a_game_in_progress_gets_the_card_catalog_and_then_the_game():
    client = TestClient(create_app())
    with client.websocket_connect("/ws") as first:
        Gui(first).start(["human", "random_bot"], seed=3)

        with client.websocket_connect("/ws") as second:
            gui = Gui(second)
            assert gui.receive()["type"] == "update"
            assert gui.card_catalog == tm_engine.card_catalog()

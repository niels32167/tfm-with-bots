"""Smoke test for the local server: a whole Game played over the WebSocket."""

from fastapi.testclient import TestClient

from server.app import create_app

# A generous guard so a broken server fails the test instead of hanging it.
MAX_MESSAGES = 10_000


def test_a_random_bot_against_random_bot_game_streams_updates_until_the_game_is_over():
    client = TestClient(create_app())

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            {"type": "new_game", "controllers": ["random_bot", "random_bot"], "seed": 1, "bot_delay": 0}
        )
        log: list[str] = []
        for _ in range(MAX_MESSAGES):
            message = websocket.receive_json()
            assert message["type"] != "error", message
            if message["type"] == "update":
                assert message["decision"] is None  # no human is asked anything
                log = log[: message["log_start"]] + message["log"]
            if message["type"] == "game_over":
                break
        else:
            raise AssertionError(f"no game_over after {MAX_MESSAGES} messages")

    assert [score["player"] for score in message["scores"]] == [0, 1]
    assert log[0].startswith("Generation 1 begins, with Player ")
    assert log[-3] == "The Game is over."

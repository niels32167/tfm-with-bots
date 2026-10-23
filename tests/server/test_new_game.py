"""Starting a Game from the setup screen: Players, Controllers, seed and Random Bot speed."""

import tm_engine

from tests.server.helpers import connect


def test_a_game_can_have_two_to_five_players_each_with_their_own_controller():
    controllers = ["random_bot", "human", "random_bot", "random_bot", "random_bot"]
    with connect() as gui:
        update = gui.start(controllers, seed=3)

    assert update["controllers"] == controllers
    assert len(update["view"]["players"]) == 5


def test_a_single_human_sees_only_their_own_player_view():
    with connect() as gui:
        update = gui.start(["random_bot", "human", "random_bot"], seed=3)

    assert update["viewer"] == 1
    assert update["view"]["viewer"] == 1


def test_a_single_human_sees_their_own_hand_but_neither_the_random_bots_hand_nor_the_deck_order():
    with connect() as gui:
        update = gui.start(["random_bot", "human"], seed=3)

    human, bot = update["view"]["players"][1], update["view"]["players"][0]
    assert human["hand"] is not None and len(human["hand"]) == human["hand_size"]
    assert bot["hand"] is None and bot["hand_size"] > 0
    assert update["view"]["deck"] is None


def test_hotseat_shows_the_full_view_and_asks_the_first_player_to_decide():
    with connect() as gui:
        update = gui.start(["human", "human", "human"], seed=3)

    assert update["viewer"] is None
    assert update["view"]["viewer"] is None
    assert update["decision"]["player"] == update["view"]["first_player"]


def test_a_game_with_only_random_bots_shows_the_full_view():
    with connect() as gui:
        gui.send({"type": "new_game", "controllers": ["random_bot", "random_bot"], "bot_delay": 5})
        update = gui.next_update()

    assert update["viewer"] is None
    assert update["view"]["viewer"] is None


def test_the_entered_seed_starts_the_game_and_is_sent_with_every_update():
    with connect() as gui:
        update = gui.start(["human", "human", "human"], seed=1234)

    assert update["seed"] == 1234
    assert update["view"] == tm_engine.Game(seed=1234, players=3).full_view()


def test_without_an_entered_seed_one_is_picked_at_random():
    with connect() as gui:
        first = gui.start(["human", "human"])
        second = gui.start(["human", "human"])

    assert isinstance(first["seed"], int)
    assert first["seed"] != second["seed"]


def test_a_seed_must_be_a_whole_number_the_engine_can_use():
    with connect() as gui:
        gui.send({"type": "new_game", "controllers": ["human", "human"], "seed": -1})
        assert "seed" in gui.receive_error()
        gui.send({"type": "new_game", "controllers": ["human", "human"], "seed": tm_engine.MAX_SEED + 1})
        assert "seed" in gui.receive_error()


def test_a_game_needs_two_to_five_known_controllers():
    with connect() as gui:
        gui.send({"type": "new_game", "controllers": ["human"]})
        assert "2 to 5 Players" in gui.receive_error()
        gui.send({"type": "new_game", "controllers": ["human", "trained_ai"]})
        assert "unknown Controller" in gui.receive_error()


def test_random_bot_speed_is_set_with_the_game_and_can_be_changed_during_it():
    with connect() as gui:
        update = gui.start(["human", "random_bot"], seed=3, bot_delay=0.25)
        assert update["bot_delay"] == 0.25

        gui.send({"type": "set_bot_delay", "bot_delay": 1.5})
        assert gui.next_update()["bot_delay"] == 1.5

        gui.send({"type": "set_bot_delay", "bot_delay": -1})
        assert "delay" in gui.receive_error()

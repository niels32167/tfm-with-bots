"""Starting a Game from the setup screen: Players, Controllers, seed and Random Bot speed."""

import time

import tm_engine

from tests.helpers import end_the_action_phase, skip_buying
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


def test_a_single_human_sees_the_cards_dealt_to_them_but_neither_the_random_bots_nor_the_deck_order():
    with connect() as gui:
        update = gui.start(["random_bot", "human"], seed=3)

    human, bot = update["view"]["players"][1], update["view"]["players"][0]
    assert update["decision"]["kind"] == "buy_cards"
    assert len(human["buying"]["dealt"]) == 10
    assert (bot["buying"], bot["hand"]) == (None, None)
    assert (update["view"]["deck"], update["view"]["discard"]) == (None, None)


def test_a_random_bot_buys_its_cards_without_pausing_so_waiting_on_it_reveals_nothing():
    # A seed whose first player is Player 1, the Random Bot, so it buys before the human.
    seed = next(seed for seed in range(100) if tm_engine.Game(seed=seed).full_view()["first_player"] == 0)
    with connect() as gui:
        started = time.monotonic()
        update = gui.start(["random_bot", "human"], seed=seed, bot_delay=5)
        waited = time.monotonic() - started

    assert (update["decision"]["kind"], update["decision"]["player"]) == ("buy_cards", 1)
    assert waited < 2


def test_a_new_game_can_deal_the_implemented_cards_first():
    with connect() as gui:
        gui.start(["human", "human"], seed=3, implemented_cards_first=True)
        assert gui.save_replay()["replay"]["start"]["settings"]["implemented_cards_first"] is True

        gui.send({"type": "new_game", "controllers": ["human", "human"], "implemented_cards_first": "yes"})
        assert "implemented_cards_first must be true or false" in gui.receive_error()


def test_a_new_game_has_the_draft_unless_it_is_switched_off():
    with connect() as gui:
        gui.start(["human", "human"], seed=3)
        assert gui.save_replay()["replay"]["start"]["settings"]["draft"] is True
        gui.start(["human", "human"], seed=3, draft=False)
        assert gui.save_replay()["replay"]["start"]["settings"]["draft"] is False

        gui.send({"type": "new_game", "controllers": ["human", "human"], "draft": "no"})
        assert "draft must be true or false" in gui.receive_error()


def test_a_random_bot_drafts_without_pausing_so_waiting_on_it_reveals_nothing():
    # A seed whose first player in Generation 2 is Player 1, the Random Bot, so it drafts first.
    seed = next(seed for seed in range(100) if tm_engine.Game(seed=seed).full_view()["first_player"] == 1)
    game = tm_engine.Game(seed=seed)
    skip_buying(game)
    end_the_action_phase(game)
    file = {"controllers": ["random_bot", "human"], "replay": game.replay}
    with connect() as gui:
        started = time.monotonic()
        gui.send({"type": "load_replay", "file": file, "bot_delay": 5})
        update = gui.wait_for_human()
        waited = time.monotonic() - started

    assert (update["decision"]["kind"], update["decision"]["player"]) == ("draft", 1)
    assert len(update["view"]["players"][1]["drafting"]["kept"]) == 0
    assert waited < 2


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

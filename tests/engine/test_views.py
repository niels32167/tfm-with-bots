"""What each Player may see (the Player View), and the full view for Hotseat and the dev panel."""

from typing import Any

import tm_engine

from tests.helpers import PROJECT_CARDS, buy, buying, end_the_action_phase, player, scenario

CARD_NAMES = {card["id"]: card["name"] for card in tm_engine.card_catalog()}


def cards_named_in(value: Any) -> set[str]:
    """Every Project Card id anywhere in `value`. Give it a view without its board, whose Areas
    reserved for cards are named after them, and without its phase: "research" is a card too."""
    if isinstance(value, dict):
        return set().union(*map(cards_named_in, value.values()))
    if isinstance(value, list):
        return set().union(*map(cards_named_in, value))
    return {value} if value in PROJECT_CARDS else set()


def test_the_full_view_belongs_to_no_single_player():
    game = scenario(player(), player(), player())

    assert game.full_view()["viewer"] is None
    assert game.player_view(1)["viewer"] == 1


def test_a_player_sees_their_own_hand_and_only_the_size_of_anyone_elses():
    game = scenario(player(hand=["mine", "trees"]), player(hand=["grass"], played_cards=["windmills"]))

    boards = game.player_view(0)["players"]

    assert (boards[0]["hand"], boards[0]["hand_size"]) == (["mine", "trees"], 2)
    assert (boards[1]["hand"], boards[1]["hand_size"]) == (None, 1)
    assert boards[1]["played_cards"] == ["windmills"]


def test_the_full_view_shows_every_hand_and_the_deck_order_and_otherwise_what_every_player_view_shows():
    game = scenario(player(megacredits=30, hand=["mine"]), player(hand=["grass"]), first_player=1, deck=["trees"])

    full_view = game.full_view()

    assert [board["hand"] for board in full_view["players"]] == [["mine"], ["grass"]]
    assert full_view["deck"][0] == "trees"
    for viewer in (0, 1):
        own_view = game.player_view(viewer)
        assert (own_view["deck"], own_view["discard"]) == (None, None)
        for index, board in enumerate(own_view["players"]):
            board["hand"] = full_view["players"][index]["hand"]
        assert full_view == {**own_view, "viewer": None, "deck": full_view["deck"], "discard": []}


def log_names_none_of_the_cards_dealt(game: tm_engine.Game, before: list[dict[str, Any]]) -> bool:
    """Whether no game log line names a card dealt to any Player to buy from."""
    names = [CARD_NAMES[card] for board in before for card in board["buying"]["dealt"]]
    return not any(name in line for name in names for line in game.log)


def assert_no_player_view_shows_what_others_buy(game: tm_engine.Game, before: list[dict[str, Any]]) -> None:
    """While Players buy: each Player View shows only cards dealt to its viewer or seen by all,
    and every other Player's MegaCredits and hand as they were `before` the buying began."""
    seen_by_all = {card for board in before for card in board["played_cards"]}
    for viewer, own in enumerate(before):
        view = game.player_view(viewer)
        dealt = set(view["players"][viewer]["buying"]["dealt"])
        assert cards_named_in({**view, "board": None, "phase": None}) <= dealt | set(own["hand"]) | seen_by_all
        assert (view["deck"], view["discard"]) == (None, None)
        for index, board in enumerate(view["players"]):
            if index != viewer:
                assert (board["hand"], board["buying"]) == (None, None)
                assert (board["resources"], board["hand_size"]) == (before[index]["resources"], before[index]["hand_size"])


def test_while_players_buy_at_setup_no_player_view_shows_what_another_player_was_dealt_or_bought():
    game = tm_engine.Game(seed=7, players=3)
    before = game.full_view()["players"]

    for _ in range(2):  # the first two Players buy two cards each and are done; the third is deciding
        buy(game, *buying(game, game.decision["player"])["dealt"][:2])

    assert game.full_view()["phase"] == "setup"
    assert_no_player_view_shows_what_others_buy(game, before)
    assert game.player_view(0)["discard_size"] == 0
    assert log_names_none_of_the_cards_dealt(game, before)


def test_while_players_buy_in_a_research_phase_no_player_view_shows_what_another_player_drew_or_bought():
    hands = [PROJECT_CARDS[0:3], PROJECT_CARDS[3:5], PROJECT_CARDS[5:6]]
    game = scenario(*[player(hand=held, played_cards=[PROJECT_CARDS[10 + index]]) for index, held in enumerate(hands)])
    end_the_action_phase(game)
    before = game.full_view()["players"]

    for _ in range(2):
        buy(game, buying(game, game.decision["player"])["dealt"][0])

    assert game.full_view()["phase"] == "research"
    assert_no_player_view_shows_what_others_buy(game, before)
    assert log_names_none_of_the_cards_dealt(game, before)


def test_once_everyone_is_done_buying_the_log_says_how_many_cards_each_player_bought_but_not_which():
    game = tm_engine.Game(seed=7, players=2)
    before = game.full_view()["players"]
    for _ in range(2):
        buy(game, buying(game, game.decision["player"])["dealt"][0])

    assert [board["hand_size"] for board in game.player_view(0)["players"]] == [1, 1]
    assert game.player_view(0)["discard_size"] == 18
    assert "Player 1 buys 1 of their 10 cards for 3 MegaCredits." in game.log
    assert log_names_none_of_the_cards_dealt(game, before)

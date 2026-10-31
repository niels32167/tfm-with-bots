"""What each Player may see (the Player View), and the full view for Hotseat and the dev panel."""

from typing import Any

import tm_engine

from tests.helpers import (
    CARD_NAMES,
    PROJECT_CARDS,
    buy,
    buying,
    end_the_action_phase,
    keep_the_first_cards_offered,
    pick,
    player,
    scenario,
)


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
            for hidden in ("hand", "card_costs", "passed_in_draft"):
                board[hidden] = full_view["players"][index][hidden]
        assert full_view == {**own_view, "viewer": None, "deck": full_view["deck"], "discard": []}


def log_names_none_of(game: tm_engine.Game, cards: list[str]) -> bool:
    """Whether no game log line names any of `cards`."""
    return not any(CARD_NAMES[card] in line for card in cards for line in game.log)


def cards_dealt(before: list[dict[str, Any]]) -> list[str]:
    """The cards dealt to every Player to draft or to buy from, from the player boards of the full view."""
    dealt = []
    for board in before:
        dealt += board["buying"]["dealt"] if board["buying"] else board["drafting"]["picking_from"]
    return dealt


def cards_seen_by(own: dict[str, Any]) -> set[str]:
    """The cards a Player has seen, from their own player board: their hand, the cards they are
    buying from or drafting, and those they passed in the Draft."""
    seen = set(own["hand"])
    if own["buying"]:
        seen |= set(own["buying"]["dealt"])
    if own["drafting"]:
        seen |= set(own["drafting"]["picking_from"] + own["drafting"]["kept"])
    return seen.union(*(passed["cards"] for passed in own["passed_in_draft"]))


def assert_no_player_view_shows_what_others_draft_or_buy(
    game: tm_engine.Game, before: list[dict[str, Any]]
) -> None:
    """While Players draft or buy: each Player View shows only cards its viewer has seen or that
    everyone has, and every other Player's MegaCredits and hand as they were `before` it began."""
    seen_by_all = {card for board in before for card in board["played_cards"]}
    for viewer in range(len(before)):
        view = game.player_view(viewer)
        seen = cards_seen_by(view["players"][viewer])
        assert cards_named_in({**view, "board": None, "phase": None}) <= seen | seen_by_all
        assert (view["deck"], view["discard"]) == (None, None)
        for index, board in enumerate(view["players"]):
            if index != viewer:
                assert (board["hand"], board["buying"]) == (None, None)
                assert (board["drafting"], board["passed_in_draft"]) == (None, None)
                assert (board["resources"], board["hand_size"]) == (before[index]["resources"], before[index]["hand_size"])


def test_while_players_buy_at_setup_no_player_view_shows_what_another_player_was_dealt_or_bought():
    game = tm_engine.Game(seed=7, players=3)
    before = game.full_view()["players"]

    for _ in range(2):  # the first two Players buy two cards each and are done; the third is deciding
        buy(game, *buying(game, game.decision["player"])["dealt"][:2])

    assert game.full_view()["phase"] == "setup"
    assert_no_player_view_shows_what_others_draft_or_buy(game, before)
    assert game.player_view(0)["discard_size"] == 0
    assert log_names_none_of(game, cards_dealt(before))


def research_phase_of_three_players_with_cards(*, draft: bool) -> tm_engine.Game:
    """Generation 2's Research phase, with or without the Draft, for three Players who each hold
    and have played different cards."""
    hands = [PROJECT_CARDS[0:3], PROJECT_CARDS[3:5], PROJECT_CARDS[5:6]]
    players = [player(hand=held, played_cards=[PROJECT_CARDS[10 + index]]) for index, held in enumerate(hands)]
    game = scenario(*players, draft=draft)
    end_the_action_phase(game)
    return game


def test_while_players_buy_in_a_research_phase_no_player_view_shows_what_another_player_drew_or_bought():
    game = research_phase_of_three_players_with_cards(draft=False)
    before = game.full_view()["players"]

    for _ in range(2):
        buy(game, buying(game, game.decision["player"])["dealt"][0])

    assert game.full_view()["phase"] == "research"
    assert_no_player_view_shows_what_others_draft_or_buy(game, before)
    assert log_names_none_of(game, cards_dealt(before))


def test_while_players_draft_no_player_view_shows_what_another_player_holds_kept_or_passed():
    game = research_phase_of_three_players_with_cards(draft=True)
    before = game.full_view()["players"]
    dealt = cards_dealt(before)

    game.pick(0)  # Player 2, the first player, keeps a card; then Player 3
    game.pick(1)
    assert game.full_view()["phase"] == "draft"
    assert_no_player_view_shows_what_others_draft_or_buy(game, before)

    game.pick(2)  # Player 1 keeps a card, and every Player passes the rest on
    assert all(board["passed_in_draft"] for board in game.full_view()["players"])
    assert_no_player_view_shows_what_others_draft_or_buy(game, before)

    keep_the_first_cards_offered(game)
    assert game.full_view()["phase"] == "research"
    assert_no_player_view_shows_what_others_draft_or_buy(game, before)
    assert log_names_none_of(game, dealt)


def test_once_everyone_is_done_buying_the_log_says_how_many_cards_each_player_bought_but_not_which():
    game = tm_engine.Game(seed=7, players=2)
    before = game.full_view()["players"]
    for _ in range(2):
        buy(game, buying(game, game.decision["player"])["dealt"][0])

    assert [board["hand_size"] for board in game.player_view(0)["players"]] == [1, 1]
    assert game.player_view(0)["discard_size"] == 18
    assert "Player 1 buys 1 of their 10 cards for 3 MegaCredits." in game.log
    assert log_names_none_of(game, cards_dealt(before))


def test_while_a_player_keeps_cards_they_look_at_no_other_player_view_shows_them():
    game = scenario(player(hand=["business_contacts"]), player(), deck=["mine", "trees", "birds", "fish"])
    looked_at = ["fish", "mine", "trees", "birds"]

    pick(game, "Play Business Contacts")
    pick(game, type="keep_card", card="trees")

    assert game.player_view(0)["players"][0]["keeping"]["looking_at"] == ["fish", "mine", "birds"]
    assert game.full_view()["players"][0]["keeping"]["kept"] == ["trees"]
    other = game.player_view(1)
    assert other["players"][0]["keeping"] is None
    # Only Business Contacts itself, which lies among the played cards.
    assert cards_named_in({key: value for key, value in other.items() if key not in ("board", "phase")}) == {
        "business_contacts"
    }
    assert log_names_none_of(game, looked_at)


def test_while_a_player_looks_at_the_card_inventors_guild_offers_them_no_other_player_view_shows_it():
    game = scenario(player(megacredits=3, played_cards=["inventors_guild"]), player(), deck=["mine", "trees"])

    pick(game, "Use the action of Inventors' Guild")

    assert game.player_view(0)["players"][0]["keeping"]["looking_at"] == ["mine"]
    other = game.player_view(1)
    assert other["players"][0]["keeping"] is None
    assert cards_named_in({key: value for key, value in other.items() if key not in ("board", "phase")}) == {
        "inventors_guild"
    }
    pick(game, "Buy Mine")
    assert log_names_none_of(game, ["mine"])


def test_every_player_view_shows_which_actions_each_player_has_used_this_generation():
    game = scenario(player(steel=1, played_cards=["space_elevator"]), player())

    pick(game, "Use the action of Space Elevator")

    for viewer in (0, 1):
        assert game.player_view(viewer)["players"][0]["used_actions"] == ["space_elevator"]
        assert game.player_view(viewer)["players"][1]["used_actions"] == []


def test_only_the_player_sees_what_their_cards_cost_and_everyone_sees_what_waits_on_their_next_card():
    game = scenario(player(megacredits=10, hand=["special_design", "mine"]), player())

    pick(game, "Play Special Design")

    assert game.player_view(1)["players"][0]["card_costs"] is None
    assert game.player_view(1)["players"][0]["next_card"] == "special_design"
    assert game.player_view(0)["players"][0]["card_costs"] == {"mine": 4}

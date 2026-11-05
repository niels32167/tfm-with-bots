"""The Draft, on by default: from Generation 2, each Player is dealt 4 cards in the Research
phase, keeps one and passes the rest to their neighbour, until every card is kept. Passing goes
clockwise (to the next Player) in even Generations and counter-clockwise in odd ones. Players
pick one at a time in player order from the first player, and the cards passed reach their
new owner only once everyone has picked. Then each buys any of the cards they kept for 3
MegaCredits each."""

import pytest
import tm_engine

from tests.helpers import (
    CARD_NAMES,
    PROJECT_CARDS,
    buy,
    buying,
    drafting,
    end_the_action_phase,
    end_the_generation,
    hand,
    keep_the_first_cards_offered,
    labels,
    pick,
    player,
    player_board,
    resources,
    scenario,
    skip_buying,
)

DRAFT_CARDS = 4


@pytest.mark.parametrize("players", [2, 3, 4, 5])
def test_from_generation_2_each_player_is_dealt_4_cards_to_draft_and_the_first_player_keeps_one_first(players):
    game = scenario(*[player()] * players, first_player=0, deck=PROJECT_CARDS[: DRAFT_CARDS * players])

    end_the_action_phase(game)

    view = game.full_view()
    assert (view["generation"], view["phase"], view["first_player"]) == (2, "draft", 1)
    order = [(1 + offset) % players for offset in range(players)]
    for offset, index in enumerate(order):
        dealt = PROJECT_CARDS[DRAFT_CARDS * offset : DRAFT_CARDS * offset + DRAFT_CARDS]
        assert drafting(game, index)["picking_from"] == dealt
        assert drafting(game, index)["kept"] == []
        assert view["players"][index]["buying"] is None
    decision = game.decision
    assert (decision["kind"], decision["player"]) == ("draft", 1)
    first_cards = PROJECT_CARDS[:DRAFT_CARDS]
    assert [option["details"] for option in decision["options"]] == [
        {"type": "draft_card", "card": card} for card in first_cards
    ]
    assert labels(game) == [f"Keep {CARD_NAMES[card]}" for card in first_cards]


def test_players_keep_a_card_in_player_order_and_the_rest_pass_on_only_once_everyone_has_kept_one():
    game = scenario(player(), player(), player(), deck=PROJECT_CARDS[:12])
    end_the_action_phase(game)  # Generation 2, with Player 2 as first player
    dealt = {index: drafting(game, index)["picking_from"] for index in (1, 2, 0)}

    pick(game, type="draft_card", card=dealt[1][2])

    assert drafting(game, 1) == {"picking_from": without(dealt[1], 2), "kept": [dealt[1][2]], "passing_to": 2}
    assert drafting(game, 2)["picking_from"] == dealt[2]
    assert game.decision["player"] == 2
    pick(game, type="draft_card", card=dealt[2][0])
    assert drafting(game, 0)["picking_from"] == dealt[0]
    assert game.decision["player"] == 0
    pick(game, type="draft_card", card=dealt[0][3])

    # Generation 2 is even, so each Player passed to the next one.
    assert drafting(game, 2)["picking_from"] == without(dealt[1], 2)
    assert drafting(game, 0)["picking_from"] == without(dealt[2], 0)
    assert drafting(game, 1)["picking_from"] == without(dealt[0], 3)
    assert [drafting(game, index)["kept"] for index in (1, 2, 0)] == [[dealt[1][2]], [dealt[2][0]], [dealt[0][3]]]
    assert (game.decision["kind"], game.decision["player"]) == ("draft", 1)


def without(cards: list[str], position: int) -> list[str]:
    """`cards` without the one at `position`."""
    return cards[:position] + cards[position + 1 :]


@pytest.mark.parametrize("players", [3, 4, 5])
@pytest.mark.parametrize(
    ("generation", "step", "direction"),
    [(1, +1, "clockwise, to the next Player"), (2, -1, "counter-clockwise, to the Player before them")],
)
def test_cards_pass_clockwise_in_even_generations_and_counter_clockwise_in_odd_ones(
    players, generation, step, direction
):
    game = scenario(*[player()] * players, generation=generation)
    end_the_action_phase(game)  # Generation `generation + 1` begins
    picking_from = [drafting(game, index)["picking_from"] for index in range(players)]

    for _ in range(players):
        game.pick(0)  # each keeps the first of their cards

    for index in range(players):
        passing_to = (index + step) % players
        assert drafting(game, index)["passing_to"] == passing_to
        assert drafting(game, passing_to)["picking_from"] == picking_from[index][1:]
    assert game.log[game.log.index(f"Generation {generation + 1} begins, with Player 2 as first player.") + 1] == (
        f"Research phase, with the Draft: each Player is dealt 4 cards, keeps one and passes the rest {direction}, "
        "until every card is kept. Then they may buy any of the cards they kept for 3 MegaCredits each."
    )


@pytest.mark.parametrize("generation", [1, 2])
def test_with_2_players_cards_always_pass_to_the_other_player(generation):
    game = scenario(player(), player(), generation=generation)
    end_the_action_phase(game)
    picking_from = [drafting(game, index)["picking_from"] for index in (0, 1)]

    game.pick(0)  # each keeps the first of their cards
    game.pick(0)

    assert [drafting(game, index)["passing_to"] for index in (0, 1)] == [1, 0]
    assert [drafting(game, index)["picking_from"] for index in (1, 0)] == [cards[1:] for cards in picking_from]
    assert "passes the rest to the other Player, until every card is kept." in game.log[-1]


def test_the_last_card_of_each_hand_is_kept_without_a_decision_and_then_players_buy_from_the_cards_they_kept():
    game = scenario(player(), player(), deck=PROJECT_CARDS[:8])
    end_the_action_phase(game)  # Player 2 is dealt the first 4 cards and Player 1 the next 4
    cards = PROJECT_CARDS

    deciding = keep_the_first_cards_offered(game)

    assert deciding == [1, 0] * 3  # picking from 4 cards, then 3, then 2
    # Player 2 keeps #1, then #6 of the cards passed back, then #3, and is passed #8.
    assert buying(game, 1) == {"dealt": [cards[0], cards[2], cards[5], cards[7]], "bought": []}
    assert buying(game, 0) == {"dealt": [cards[1], cards[3], cards[4], cards[6]], "bought": []}
    assert [drafting(game, index) for index in (0, 1)] == [None, None]
    assert game.full_view()["phase"] == "research"
    assert game.log[-1] == "The Draft is over."
    assert (game.decision["kind"], game.decision["player"]) == ("buy_cards", 1)

    buy(game, cards[5])
    buy(game, cards[1], cards[3])

    assert (hand(game, 1), hand(game, 0)) == ([cards[5]], [cards[1], cards[3]])
    assert [resources(game, index)["megacredits"] for index in (0, 1)] == [42 + 20 - 6, 42 + 20 - 3]
    assert game.full_view()["phase"] == "action"


def test_a_player_view_lists_the_cards_its_player_passed_and_to_whom_for_the_rest_of_the_game():
    game = scenario(player(), player(), deck=PROJECT_CARDS[:8])
    end_the_action_phase(game)
    keep_the_first_cards_offered(game)
    cards = PROJECT_CARDS

    passed = player_board(game, 0)["passed_in_draft"]

    assert passed == [
        {"generation": 2, "to": 1, "cards": [cards[5], cards[6], cards[7]]},
        {"generation": 2, "to": 1, "cards": [cards[2], cards[3]]},
        {"generation": 2, "to": 1, "cards": [cards[7]]},
    ]
    assert game.player_view(1)["players"][0]["passed_in_draft"] is None
    skip_buying(game)
    end_the_generation(game)
    assert player_board(game, 0)["passed_in_draft"][:3] == passed
    assert [pass_["generation"] for pass_ in player_board(game, 0)["passed_in_draft"]] == [2, 2, 2, 3, 3, 3]


def test_a_player_left_with_fewer_cards_when_the_deck_and_discard_pile_run_out_still_keeps_every_card_passed():
    held = PROJECT_CARDS[:202]
    game = scenario(player(hand=held[:101]), player(hand=held[101:]), deck=PROJECT_CARDS[202:])
    end_the_action_phase(game)
    assert [len(drafting(game, index)["picking_from"]) for index in (1, 0)] == [4, 2]

    deciding = keep_the_first_cards_offered(game)

    # Player 1 picks from 2, then 3. Player 2 picks from 4, keeps the 1 card passed back, then picks from 2.
    assert deciding == [1, 0, 0, 1]
    kept = [buying(game, index)["dealt"] for index in (0, 1)]
    assert set(kept[0] + kept[1]) == set(PROJECT_CARDS[202:])
    assert [len(cards) for cards in kept] == [3, 3]
    assert "The deck and the discard pile are empty, so Player 1 draws no more cards." in game.log


def test_there_is_no_draft_at_setup_where_each_player_buys_from_the_10_cards_dealt():
    game = tm_engine.Game(seed=7)

    assert game.full_view()["phase"] == "setup"
    assert game.decision["kind"] == "corporation"
    game.pick(0)
    assert game.decision["kind"] == "buy_cards"
    assert all(len(board["buying"]["dealt"]) == 10 for board in game.full_view()["players"])


def test_with_the_draft_off_the_research_phase_deals_4_cards_straight_to_buy_from():
    game = scenario(player(), player(), deck=PROJECT_CARDS[:8], draft=False)

    end_the_action_phase(game)

    assert game.full_view()["phase"] == "research"
    assert buying(game, 1) == {"dealt": PROJECT_CARDS[:4], "bought": []}
    assert drafting(game, 1) is None
    assert game.decision["kind"] == "buy_cards"


def test_the_draft_is_on_unless_switched_off_and_a_replay_from_before_the_draft_existed_reads_as_off():
    assert tm_engine.Game(seed=7).replay["start"]["settings"]["draft"] is True
    assert tm_engine.Game(seed=7, draft=False).replay["start"]["settings"]["draft"] is False

    replay = tm_engine.Game(seed=7).replay
    del replay["start"]["settings"]["draft"]

    assert tm_engine.Game.from_replay(replay).replay["start"]["settings"]["draft"] is False


def test_a_scenario_has_the_draft_unless_switched_off_but_one_in_a_replay_from_before_the_draft_existed_does_not():
    assert scenario().replay["start"]["scenario"]["draft"] is True

    replay = scenario().replay
    del replay["start"]["scenario"]["draft"]
    game = tm_engine.Game.from_replay(replay)
    end_the_action_phase(game)

    assert game.replay["start"]["scenario"]["draft"] is False
    assert game.full_view()["phase"] == "research"

"""Buying Project Cards: the 10 dealt at setup, and the 4 drawn in each Research phase from
Generation 2. Buying is a chain of single picks ending with Done, one Player at a time in
player order from the first player. Nothing is paid or revealed until every Player is done;
then each pays 3 MegaCredits per card bought, and the rest go face down to the discard pile."""

import pytest
import tm_engine

from tests.helpers import (
    PROJECT_CARDS,
    buy,
    buying,
    end_the_action_phase,
    hand,
    labels,
    pick,
    player,
    player_board,
    resources,
    scenario,
)

SETUP_CARDS = 10
RESEARCH_CARDS = 4
CARD_PRICE = 3
# A Terraform Rating of 5 and MegaCredit Production of -5 leave a Player's MegaCredits as they
# are in the Production phase, so a test can set what they buy with in the Research phase.
NO_INCOME = {"terraform_rating": 5, "production": {"megacredits": -5}}


@pytest.mark.parametrize("players", [2, 3, 4, 5])
def test_a_new_game_deals_each_player_10_cards_to_buy_from_before_generation_1(players):
    game = tm_engine.Game(seed=7, players=players)

    view = game.full_view()
    assert view["phase"] == "setup"
    assert view["generation"] == 1
    for board in view["players"]:
        assert len(board["buying"]["dealt"]) == SETUP_CARDS
        assert board["buying"]["bought"] == []
        assert board["hand"] == []
    dealt = [card for board in view["players"] for card in board["buying"]["dealt"]]
    assert sorted(dealt + view["deck"]) == sorted(PROJECT_CARDS)
    assert view["deck_size"] == 208 - SETUP_CARDS * players
    assert game.decision["kind"] == "buy_cards"
    assert game.decision["player"] == view["first_player"]


def test_the_deal_comes_from_the_seed():
    def dealt(seed):
        return [board["buying"]["dealt"] for board in tm_engine.Game(seed=seed).full_view()["players"]]

    assert dealt(7) == dealt(7)
    assert dealt(7) != dealt(8)


def test_a_player_may_buy_any_card_dealt_to_them_for_3_megacredits_or_be_done():
    game = tm_engine.Game(seed=7)
    first = game.decision["player"]
    dealt = buying(game, first)["dealt"]
    names = {card["id"]: card["name"] for card in tm_engine.card_catalog()}

    assert labels(game) == [f"Buy {names[card]} (3 MegaCredits)" for card in dealt] + ["Done"]
    assert game.decision["options"][0]["details"] == {"type": "buy_card", "card": dealt[0], "cost": CARD_PRICE}

    pick(game, type="buy_card", card=dealt[3])

    assert buying(game, first) == {"dealt": dealt, "bought": [dealt[3]]}
    assert labels(game) == [f"Buy {names[card]} (3 MegaCredits)" for card in dealt if card != dealt[3]] + ["Done"]


def test_players_buy_in_player_order_from_the_first_player_and_pay_once_everyone_is_done():
    game = tm_engine.Game(seed=7, players=3)
    first = game.decision["player"]
    order = [(first + offset) % 3 for offset in range(3)]
    dealt = {index: buying(game, index)["dealt"] for index in order}

    deciding = []
    for index, count in zip(order, (2, 0, 1), strict=True):
        deciding.append(game.decision["player"])
        assert resources(game, order[0])["megacredits"] == 42
        buy(game, *dealt[index][:count])

    assert deciding == order
    assert [resources(game, index)["megacredits"] for index in order] == [42 - 6, 42, 42 - 3]
    assert [hand(game, index) for index in order] == [dealt[order[0]][:2], [], dealt[order[2]][:1]]
    view = game.full_view()
    assert view["discard_size"] == 30 - 3
    assert sorted(view["discard"]) == sorted(dealt[order[0]][2:] + dealt[order[1]] + dealt[order[2]][1:])
    assert all(board["buying"] is None for board in view["players"])
    assert game.log[-4:] == [
        f"Player {order[0] + 1} buys 2 of their 10 cards for 6 MegaCredits.",
        f"Player {order[1] + 1} buys none of their 10 cards.",
        f"Player {order[2] + 1} buys 1 of their 10 cards for 3 MegaCredits.",
        f"Generation 1 begins, with Player {first + 1} as first player.",
    ]
    assert view["phase"] == "action"
    assert game.decision["kind"] == "action"
    assert game.decision["player"] == first


def test_a_player_who_buys_every_card_dealt_is_done_without_picking_done():
    game = tm_engine.Game(seed=7)
    first = game.decision["player"]

    for card in buying(game, first)["dealt"]:
        pick(game, type="buy_card", card=card)

    assert game.decision["player"] != first
    assert len(buying(game, first)["bought"]) == SETUP_CARDS


def test_until_corporations_exist_every_player_starts_with_42_megacredits_to_buy_cards_with():
    game = tm_engine.Game(seed=7)

    assert [player_board(game, index)["resources"]["megacredits"] for index in (0, 1)] == [42, 42]
    assert game.log[0] == (
        "Setup: each Player is dealt 10 Project Cards and may buy any of them for 3 MegaCredits each."
    )


def test_a_scenario_starts_in_the_action_phase_with_nothing_to_buy():
    game = tm_engine.Game.from_scenario({"players": [player(hand=["mine"]), player()]})

    assert game.full_view()["phase"] == "action"
    assert game.full_view()["players"][0]["buying"] is None


@pytest.mark.parametrize("players", [2, 3, 4, 5])
def test_from_generation_2_the_research_phase_deals_each_player_4_cards_in_player_order(players):
    game = scenario(*[player()] * players, first_player=0, deck=PROJECT_CARDS[: 4 * players])

    end_the_action_phase(game)

    view = game.full_view()
    assert (view["generation"], view["phase"], view["first_player"]) == (2, "research", 1)
    order = [(1 + offset) % players for offset in range(players)]
    for offset, index in enumerate(order):
        assert buying(game, index) == {"dealt": PROJECT_CARDS[4 * offset : 4 * offset + 4], "bought": []}
    assert (game.decision["kind"], game.decision["player"]) == ("buy_cards", 1)
    assert game.log[-2:] == [
        "Generation 2 begins, with Player 2 as first player.",
        "Research phase: each Player draws 4 cards and may buy any of them for 3 MegaCredits each.",
    ]
    for _ in range(players):
        buy(game)
    assert (game.full_view()["phase"], game.decision["player"]) == ("action", 1)


def test_research_cards_not_bought_go_face_down_to_the_discard_pile_and_then_the_action_phase_begins():
    game = scenario(player(megacredits=10, **NO_INCOME), player(megacredits=10, **NO_INCOME), deck=PROJECT_CARDS[:8])
    end_the_action_phase(game)

    buy(game, PROJECT_CARDS[1])  # Player 2, the first player of Generation 2
    buy(game, PROJECT_CARDS[4], PROJECT_CARDS[7])

    assert [resources(game, index)["megacredits"] for index in (0, 1)] == [10 - 6, 10 - 3]
    assert hand(game, 0) == [PROJECT_CARDS[4], PROJECT_CARDS[7]]
    assert hand(game, 1) == [PROJECT_CARDS[1]]
    assert game.full_view()["discard"] == [PROJECT_CARDS[index] for index in (0, 2, 3, 5, 6)]
    assert game.log[-2:] == [
        "Player 2 buys 1 of their 4 cards for 3 MegaCredits.",
        "Player 1 buys 2 of their 4 cards for 6 MegaCredits.",
    ]
    assert game.full_view()["phase"] == "action"
    assert (game.decision["kind"], game.decision["player"]) == ("action", 1)


def test_a_player_buys_only_as_many_cards_as_they_can_pay_for_and_with_none_is_not_asked():
    game = scenario(
        player(megacredits=7, **NO_INCOME), player(megacredits=2, **NO_INCOME), first_player=1, deck=PROJECT_CARDS[:8]
    )
    end_the_action_phase(game)  # Player 1 is first player in Generation 2

    pick(game, type="buy_card", card=PROJECT_CARDS[0])
    assert len(labels(game)) == RESEARCH_CARDS - 1 + 1  # three cards left, and Done
    pick(game, type="buy_card", card=PROJECT_CARDS[1])  # 6 MegaCredits for two; 1 left over is too few for a third

    assert game.full_view()["phase"] == "action"
    assert hand(game, 0) == PROJECT_CARDS[:2]
    assert resources(game, 0)["megacredits"] == 1
    assert hand(game, 1) == []
    assert resources(game, 1)["megacredits"] == 2
    assert "Player 2 buys none of their 4 cards." in game.log


def test_the_research_phase_draws_from_the_reshuffled_discard_pile_once_the_deck_runs_out():
    held = PROJECT_CARDS[:200]
    game = scenario(
        player(hand=held[:100]), player(hand=held[100:]), deck=PROJECT_CARDS[200:206], discard=PROJECT_CARDS[206:]
    )

    end_the_action_phase(game)

    dealt = [set(buying(game, index)["dealt"]) for index in (0, 1)]
    assert dealt[1] == set(PROJECT_CARDS[200:204])
    assert dealt[0] == set(PROJECT_CARDS[204:])
    assert "The deck has run out, so the discard pile is shuffled into a new deck of 2 cards." in game.log

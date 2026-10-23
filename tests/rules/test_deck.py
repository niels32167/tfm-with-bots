"""The deck, and the cards each Player holds: what a new Game deals, and how a Scenario places
cards in hands, among played cards and on top of the deck."""

import pytest
import tm_engine

from tests.helpers import PROJECT_CARDS, hand, played_cards, player, scenario

# Until Corporations and buying cards exist (ticket 09), a new Game deals out these 11 cards.
STARTER_SET = [
    "black_polar_dust",
    "nuclear_power",
    "lake_marineris",
    "mine",
    "trees",
    "grass",
    "solar_power",
    "strip_mine",
    "power_plant",
    "titanium_mine",
    "windmills",
]


@pytest.mark.parametrize("players", [2, 3, 4, 5])
def test_until_ticket_09_a_new_game_deals_out_the_starter_set_round_robin_from_the_first_player(players):
    view = tm_engine.Game(seed=7, players=players).full_view()

    first = view["first_player"]
    hands = [view["players"][(first + offset) % players]["hand"] for offset in range(players)]
    assert sorted(card for held in hands for card in held) == sorted(STARTER_SET)
    assert [len(held) for held in hands] == [len(STARTER_SET[offset::players]) for offset in range(players)]


def test_every_other_project_card_is_in_the_deck():
    view = tm_engine.Game(seed=7).full_view()

    assert view["deck_size"] == 208 - len(STARTER_SET)
    assert sorted(view["deck"]) == sorted(set(PROJECT_CARDS) - set(STARTER_SET))


def test_the_deal_and_the_deck_order_come_from_the_seed():
    def cards(seed):
        view = tm_engine.Game(seed=seed).full_view()
        return [board["hand"] for board in view["players"]], view["deck"]

    assert cards(7) == cards(7)
    assert cards(7)[1] != cards(8)[1]


def test_only_the_full_view_shows_the_deck_order():
    game = tm_engine.Game(seed=7)

    assert game.player_view(0)["deck"] is None
    assert game.player_view(0)["deck_size"] == 197


def test_a_scenario_puts_cards_in_hands_and_among_played_cards():
    game = scenario(player(hand=["mine", "trees"], played_cards=["windmills"]), player(hand=["grass"]))

    assert hand(game, 0) == ["mine", "trees"]
    assert played_cards(game, 0) == ["windmills"]
    assert hand(game, 1) == ["grass"]
    assert played_cards(game, 1) == []


def test_a_scenario_puts_its_deck_on_top_in_drawing_order_and_shuffles_every_other_card_beneath():
    game = scenario(player(hand=["mine"]), player(played_cards=["trees"]), deck=["grass", "windmills"], seed=3)

    deck = game.full_view()["deck"]
    assert deck[:2] == ["grass", "windmills"]
    assert sorted(deck[2:]) == sorted(set(PROJECT_CARDS) - {"mine", "trees", "grass", "windmills"})
    assert game.full_view()["deck_size"] == 206


def test_a_scenario_without_cards_has_every_project_card_in_the_deck():
    view = scenario().full_view()

    assert view["deck_size"] == 208
    assert [board["hand"] for board in view["players"]] == [[], []]


def test_a_scenario_names_only_project_cards_and_each_at_most_once():
    with pytest.raises(ValueError, match="no Project Card 'minne'"):
        scenario(player(hand=["minne"]), player())
    with pytest.raises(ValueError, match="no Project Card 'credicor'"):
        scenario(player(played_cards=["credicor"]), player())
    with pytest.raises(ValueError, match="'mine' card in only one place"):
        scenario(player(hand=["mine"]), player(played_cards=["mine"]))
    with pytest.raises(ValueError, match="'mine' card in only one place"):
        scenario(player(hand=["mine"]), player(), deck=["mine"])

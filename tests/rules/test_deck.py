"""The deck, and the cards each Player holds: what a new Game deals, and how a Scenario places
cards in hands, among played cards and on top of the deck."""

import pytest
import tm_engine

from tests.helpers import PROJECT_CARDS, hand, pick, played_cards, player, scenario


def dealt_cards(view):
    """Every card dealt to a Player to buy from, as the full view shows them."""
    return [card for board in view["players"] for card in board["buying"]["dealt"]]


def test_the_deck_order_comes_from_the_seed():
    def deck(seed):
        return tm_engine.Game(seed=seed).full_view()["deck"]

    assert deck(7) == deck(7)
    assert deck(7) != deck(8)


def test_only_the_full_view_shows_the_deck_order():
    game = tm_engine.Game(seed=7)

    assert game.player_view(0)["deck"] is None
    assert game.player_view(0)["deck_size"] == 208 - 2 * 10


def test_a_new_game_deals_from_the_whole_shuffled_deck():
    view = tm_engine.Game(seed=7, players=5).full_view()

    assert sorted(dealt_cards(view) + view["deck"]) == sorted(PROJECT_CARDS)


def test_a_new_replay_does_not_name_the_old_setting_for_dealing_implemented_cards_first():
    assert "implemented_cards_first" not in tm_engine.Game(seed=7).replay["start"]["settings"]


def test_a_replay_saved_with_the_implemented_cards_dealt_first_still_deals_the_same_cards():
    # The GUI had that setting on by default until ticket 24, so most saved Replays name it. It meant
    # one more shuffle, so this seed deals as it did then; these cards were recorded at ticket 23.
    settings = {"players": 2, "seed": 7, "implemented_cards_first": True, "draft": True, "corporations": True}

    game = tm_engine.Game.from_replay({"start": {"settings": settings}, "picks": []})

    view = game.full_view()
    assert view["players"][0]["buying"]["dealt"] == [
        "nuclear_power",
        "miranda_resort",
        "urbanized_area",
        "sabotage",
        "power_plant",
        "nitrite_reducing_bacteria",
        "power_supply_consortium",
        "permafrost_extraction",
        "energy_tapping",
        "special_design",
    ]
    assert view["deck"][:3] == ["bushes", "physics_complex", "advanced_ecosystems"]
    assert game.replay["start"]["settings"] == settings


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


def test_a_scenario_puts_cards_face_down_in_the_discard_pile_which_only_the_full_view_lists():
    game = scenario(player(hand=["mine"]), player(), discard=["windmills", "trees"])

    assert game.full_view()["discard"] == ["trees", "windmills"]
    assert game.full_view()["discard_size"] == 2
    assert game.full_view()["deck_size"] == 205
    assert game.player_view(0)["discard"] is None
    assert game.player_view(0)["discard_size"] == 2


def test_a_scenario_without_cards_has_every_project_card_in_the_deck():
    view = scenario().full_view()

    assert view["deck_size"] == 208
    assert view["discard_size"] == 0
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
    with pytest.raises(ValueError, match="'mine' card in only one place"):
        scenario(player(), player(), deck=["mine"], discard=["mine"])


def test_when_the_deck_runs_out_the_discard_pile_is_shuffled_into_a_new_deck():
    held, deck, discarded = PROJECT_CARDS[:204], PROJECT_CARDS[204:205], PROJECT_CARDS[205:]
    game = scenario(player(megacredits=18, hand=held[:150]), player(hand=held[150:]), deck=deck, discard=discarded)

    pick(game, project="aquifer")
    pick(game, area="B6")  # its placement bonus draws 2 cards: the last one in the deck, then one more

    drawn = set(hand(game, 0)) - set(held)
    assert len(drawn) == 2
    assert deck[0] in drawn
    assert sorted(game.full_view()["deck"] + list(drawn - set(deck))) == sorted(discarded)
    assert game.full_view()["deck_size"] == 2
    assert game.full_view()["discard_size"] == 0
    assert "The deck has run out, so the discard pile is shuffled into a new deck of 3 cards." in game.log


def test_the_reshuffled_deck_comes_from_the_games_own_random_numbers():
    def reshuffled_deck(seed):
        game = scenario(
            player(megacredits=18, hand=PROJECT_CARDS[:150]), player(), discard=PROJECT_CARDS[150:], seed=seed
        )
        pick(game, project="aquifer")
        pick(game, area="B6")
        return game.full_view()["deck"]

    assert reshuffled_deck(1) == reshuffled_deck(1)
    assert reshuffled_deck(1) != reshuffled_deck(2)

"""Corporations at setup. Each Player is dealt 2 Corporations and 10 Project Cards, chooses one of
the Corporations and which cards to buy, and nothing shows until every Player is done: then, in
player order, each reveals their Corporation, gets its starting Resources and Production, and pays 3
MegaCredits per card. Each Corporation's own values and ability are in tests/cards/test_<id>.py."""

import pytest
import tm_engine

from tests.helpers import (
    CARD_NAMES,
    CARDS,
    CORPORATIONS,
    PROJECT_CARDS,
    buy,
    choosing_corporation,
    everything_about,
    hand,
    labels,
    pick,
    played_cards,
    player,
    player_board,
    resources,
    scenario,
    skip_buying,
    start_as,
)

SETUP_CARDS = 10
CARD_PRICE = 3
CORPORATIONS_DEALT = 2


@pytest.mark.parametrize("players", [2, 3, 4, 5])
def test_each_player_is_dealt_two_corporations_none_of_them_dealt_twice(players):
    view = tm_engine.Game(seed=7, players=players).full_view()

    dealt = [board["choosing_corporation"]["dealt"] for board in view["players"]]
    assert all(len(corporations) == CORPORATIONS_DEALT for corporations in dealt)
    everyone_was_dealt = [
        corporation for corporations in dealt for corporation in corporations
    ]
    assert len(set(everyone_was_dealt)) == CORPORATIONS_DEALT * players
    assert set(everyone_was_dealt) <= set(CORPORATIONS)


def test_the_corporations_dealt_come_from_the_seed():
    def dealt(seed):
        return [
            board["choosing_corporation"]["dealt"]
            for board in tm_engine.Game(seed=seed).full_view()["players"]
        ]

    assert dealt(7) == dealt(7)
    assert any(dealt(7) != dealt(seed) for seed in range(8, 18))


def test_the_project_cards_are_still_dealt_from_the_deck_and_no_corporation_is_among_them():
    view = tm_engine.Game(seed=7, players=3).full_view()

    for board in view["players"]:
        assert len(board["buying"]["dealt"]) == SETUP_CARDS
        assert set(board["buying"]["dealt"]) <= set(PROJECT_CARDS)
    assert set(view["deck"]) <= set(PROJECT_CARDS)


def test_the_first_player_decides_first_and_may_choose_either_corporation_dealt():
    game = tm_engine.Game(seed=7)
    first = game.full_view()["first_player"]

    assert game.decision["kind"] == "corporation"
    assert game.decision["player"] == first
    dealt = choosing_corporation(game, first)["dealt"]
    assert [option["details"] for option in game.decision["options"]] == [
        {"type": "choose_corporation", "card": corporation} for corporation in dealt
    ]
    assert all(label.startswith("Choose ") for label in labels(game))


def test_a_player_chooses_their_corporation_then_buys_and_then_the_next_player_chooses():
    game = tm_engine.Game(seed=7)
    first = game.full_view()["first_player"]

    game.pick(0)
    assert game.decision["kind"] == "buy_cards"
    assert game.decision["player"] == first

    pick(game, "Done")
    assert game.decision["kind"] == "corporation"
    assert game.decision["player"] == 1 - first


def test_what_a_player_chose_shows_only_in_their_own_view_until_every_player_is_done():
    game = tm_engine.Game(seed=7)
    first = game.full_view()["first_player"]
    other = 1 - first

    assert game.player_view(first)["players"][other]["choosing_corporation"] is None
    game.pick(0)

    chosen = choosing_corporation(game, first)["picked"]
    assert chosen in choosing_corporation(game, first)["dealt"]
    assert game.player_view(other)["players"][first]["choosing_corporation"] is None
    assert game.player_view(other)["players"][first]["corporation"] is None
    assert game.player_view(first)["players"][first]["corporation"] is None
    assert not any(CARD_NAMES[chosen] in line for line in game.log)


def test_while_players_choose_and_buy_nobody_has_anything_to_show():
    game = tm_engine.Game(seed=7)

    game.pick(0)
    pick(
        game,
        type="buy_card",
        card=player_board(game, game.decision["player"])["buying"]["dealt"][0],
    )

    for board in game.full_view()["players"]:
        assert set(board["resources"].values()) == {0}
        assert set(board["production"].values()) == {0}
        assert set(board["tags"].values()) == {0}


def test_once_every_player_is_done_they_reveal_their_corporations_and_get_their_starting_values():
    game, first = start_as("credicor")
    other = 1 - first

    assert player_board(game, first)["corporation"] == "credicor"
    assert game.player_view(other)["players"][first]["corporation"] == "credicor"
    assert game.player_view(first)["players"][other]["corporation"] in CORPORATIONS
    assert resources(game, first)["megacredits"] == 57
    assert player_board(game, first)["choosing_corporation"] is None
    assert f"Player {first + 1} reveals CrediCor." in game.log
    assert game.full_view()["phase"] == "action"
    assert game.full_view()["generation"] == 1


def test_they_pay_for_the_cards_they_bought_out_of_their_starting_megacredits():
    game = tm_engine.Game(seed=7)
    first = game.full_view()["first_player"]

    corporation = choosing_corporation(game, first)["dealt"][0]
    pick(game, type="choose_corporation", card=corporation)
    bought = player_board(game, first)["buying"]["dealt"][:2]
    buy(game, *bought)
    skip_buying(game)

    starting = CARDS[corporation]["effects"]["resources"]["megacredits"]
    assert resources(game, first)["megacredits"] == starting - 2 * CARD_PRICE
    assert hand(game, first) == sorted(bought, key=PROJECT_CARDS.index)


def test_a_player_buys_only_as_many_cards_as_their_corporations_starting_megacredits_pay_for():
    game, first = start_as("phobolog", buy_everything=True)

    assert len(hand(game, first)) == 23 // CARD_PRICE
    assert resources(game, first)["megacredits"] == 23 % CARD_PRICE


def test_what_a_player_has_to_buy_with_is_shown_to_them_while_nothing_is_paid():
    game = tm_engine.Game(seed=7)
    first = game.full_view()["first_player"]
    corporation = choosing_corporation(game, first)["dealt"][1]

    pick(game, type="choose_corporation", card=corporation)

    assert (
        player_board(game, first)["buying"]["megacredits"]
        == CARDS[corporation]["effects"]["resources"]["megacredits"]
    )


def test_a_corporation_is_not_among_the_played_project_cards_and_its_tags_count():
    game, first = start_as("mining_guild")

    assert played_cards(game, first) == []
    assert player_board(game, first)["tags"]["building"] == 2


def test_the_corporation_not_chosen_goes_back_in_the_box():
    game = tm_engine.Game(seed=7)
    first = game.decision["player"]
    chosen, not_chosen = choosing_corporation(game, first)["dealt"]

    pick(game, type="choose_corporation", card=chosen)
    skip_buying(game)

    view = game.full_view()
    assert player_board(game, first)["corporation"] == chosen
    assert not_chosen not in [board["corporation"] for board in view["players"]]
    assert not set(CORPORATIONS) & (set(view["deck"]) | set(view["discard"]))


def test_a_game_with_corporations_is_rebuilt_the_same_from_its_replay():
    game = tm_engine.Game(seed=7, players=3)
    game.play_randomly(seed=3, picks=60)

    rebuilt = tm_engine.Game.from_replay(game.replay)

    assert everything_about(rebuilt) == everything_about(game)
    assert game.replay["start"]["settings"]["corporations"] is True


def test_a_replay_saved_before_corporations_existed_plays_as_it_was_played():
    saved_without_them = {
        "settings": {
            "players": 2,
            "seed": 7,
            "implemented_cards_first": False,
            "draft": True,
        }
    }

    game = tm_engine.Game.from_replay({"start": saved_without_them, "picks": []})

    assert game.decision["kind"] == "buy_cards"
    for board in game.full_view()["players"]:
        assert board["resources"]["megacredits"] == 42
        assert board["choosing_corporation"] is None
    skip_buying(game)
    assert player_board(game, 0)["corporation"] is None


def test_the_picks_of_a_replay_saved_before_corporations_existed_are_played_the_same():
    played = tm_engine.Game(seed=7, players=3, corporations=False)
    played.play_randomly(seed=3)
    settings = {"players": 3, "seed": 7, "implemented_cards_first": False, "draft": True}

    rebuilt = tm_engine.Game.from_replay({"start": {"settings": settings}, "picks": played.replay["picks"]})

    assert rebuilt.is_over
    assert rebuilt.scores == played.scores


def test_without_a_corporation_a_scenario_player_has_42_megacredits():
    game = scenario(player(), player())

    assert resources(game, 0)["megacredits"] == 42
    assert player_board(game, 0)["corporation"] is None


def test_a_scenario_names_a_players_corporation_without_giving_its_starting_values():
    game = scenario(player(corporation="phobolog", megacredits=5), player())

    assert player_board(game, 0)["corporation"] == "phobolog"
    assert resources(game, 0)["megacredits"] == 5
    assert resources(game, 0)["titanium"] == 0
    assert player_board(game, 0)["tags"]["space"] == 1


def test_a_scenario_refuses_an_unknown_corporation_or_one_named_twice():
    with pytest.raises(ValueError, match="there is no Corporation 'mine'"):
        scenario(player(corporation="mine"), player())
    with pytest.raises(ValueError, match="only one place"):
        scenario(player(corporation="helion"), player(corporation="helion"))
    with pytest.raises(ValueError, match="no Project Card 'helion'"):
        scenario(player(played_cards=["helion"]), player())


def test_a_replay_of_a_scenario_with_a_corporation_is_rebuilt_the_same():
    game = scenario(player(corporation="helion"), player(corporation="thorgate"))
    game.play_randomly(seed=3, picks=20)

    assert everything_about(
        tm_engine.Game.from_replay(game.replay)
    ) == everything_about(game)

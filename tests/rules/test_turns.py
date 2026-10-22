"""Turns in the Action phase: one or two Actions, or Pass."""

from tests.helpers import offered, pick, player, player_board, scenario


def test_after_one_action_the_player_may_take_a_second_action_end_their_turn_or_pass():
    game = scenario(player(megacredits=40), player(megacredits=40))

    pick(game, "Asteroid")

    assert game.decision["player"] == 0
    assert offered(game, "Asteroid")
    assert offered(game, "End Turn")
    assert offered(game, "Pass")


def test_after_two_actions_the_turn_passes_to_the_next_player():
    game = scenario(player(megacredits=40), player(megacredits=40))

    pick(game, "Asteroid")
    pick(game, "Asteroid")

    assert game.decision["player"] == 1
    assert not offered(game, "End Turn")


def test_ending_the_turn_after_one_action_hands_the_turn_to_the_next_player():
    game = scenario(player(megacredits=40), player(megacredits=40))

    pick(game, "Asteroid")
    pick(game, "End Turn")

    assert game.decision["player"] == 1
    assert not offered(game, "End Turn")


def test_a_player_who_passes_gets_no_more_turns_while_the_others_carry_on():
    game = scenario(player(megacredits=40), player(megacredits=60))

    pick(game, "Pass")
    pick(game, "Asteroid")
    pick(game, "Asteroid")

    assert game.decision["player"] == 1
    assert player_board(game, 0)["passed"]


def test_a_player_may_pass_straight_after_their_first_action():
    game = scenario(player(megacredits=40), player(megacredits=60))

    pick(game, "Asteroid")
    pick(game, "Pass")
    pick(game, "Asteroid")
    pick(game, "Asteroid")

    assert game.decision["player"] == 1


def test_end_turn_is_not_offered_once_every_other_player_has_passed():
    game = scenario(player(megacredits=40), player(megacredits=60))

    pick(game, "Pass")
    pick(game, "Asteroid")

    assert not offered(game, "End Turn")
    assert offered(game, "Pass")


def test_everyone_can_see_whose_turn_it_is_and_how_many_actions_they_have_taken():
    game = scenario(player(megacredits=40), player(megacredits=40))

    pick(game, "Asteroid")

    view = game.player_view(1)
    assert view["current_player"] == 0
    assert view["actions_this_turn"] == 1

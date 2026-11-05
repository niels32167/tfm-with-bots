"""Inventrix (science Tag): Effect: your temperature, oxygen and ocean requirements are +2 or -2 steps,
your choice in each case. As your first action in the game, draw 3 cards. You start with 45
MegaCredits."""

import pytest

from tests.helpers import (
    hand,
    labels,
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_inventrix_starts_with_45_megacredits_a_science_tag_and_no_cards_drawn_yet():
    game, first = start_as("inventrix")

    assert resources(game, first) == {
        "megacredits": 45,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert set(production(game, first).values()) == {0}
    assert player_board(game, first)["tags"]["science"] == 1
    assert hand(game, first) == []


def test_its_first_action_draws_3_cards_and_is_all_it_may_do_first_but_passing():
    game, first = start_as("inventrix")

    assert labels(game) == ["First action of Inventrix: draw 3 cards", "Pass"]
    assert game.decision["options"][0]["details"] == {
        "type": "first_action",
        "card": "inventrix",
    }
    assert player_board(game, first)["first_action_due"] is True

    pick(game, "First action")

    assert len(hand(game, first)) == 3
    assert player_board(game, first)["first_action_due"] is False
    assert game.full_view()["actions_this_turn"] == 1
    assert not offered(game, "First action")


def test_if_they_pass_instead_the_first_action_waits_for_their_next_turn():
    game = scenario(player(corporation="inventrix", first_action_due=True), player())

    pick(game, "Pass")
    pick(game, "Pass")
    while game.decision["kind"] != "action":
        game.pick(0)

    while game.decision["player"] != 0:
        pick(game, "Pass")
    assert offered(game, "First action")


def test_a_scenario_says_whether_the_first_action_is_still_due():
    game = scenario(player(corporation="inventrix"), player())
    assert not offered(game, "First action")

    game = scenario(player(corporation="inventrix", first_action_due=True), player())
    assert offered(game, "First action")


def test_a_scenario_refuses_a_first_action_due_without_a_corporation_that_has_one():
    with pytest.raises(ValueError, match="has no first action"):
        scenario(player(corporation="helion", first_action_due=True), player())
    with pytest.raises(ValueError, match="has no first action"):
        scenario(player(first_action_due=True), player())


def test_a_requirement_on_a_global_parameter_is_2_steps_easier_at_either_end():
    with_heat = player(production={"heat": 1})
    too_low = scenario(
        player(corporation="inventrix", hand=["cloud_seeding"]), with_heat
    )
    assert not offered(too_low, "Play Cloud Seeding")

    tiles = [{"area": "A2", "tile": "ocean"}]
    with_one_ocean = scenario(
        player(corporation="inventrix", hand=["cloud_seeding"]), with_heat, tiles=tiles
    )
    assert offered(with_one_ocean, "Play Cloud Seeding")

    with_a_maximum = scenario(
        player(corporation="inventrix", hand=["search_for_life"]), player(), oxygen=8
    )
    assert offered(with_a_maximum, "Play Search for Life")
    beyond_it = scenario(
        player(corporation="inventrix", hand=["search_for_life"]), player(), oxygen=9
    )
    assert not offered(beyond_it, "Play Search for Life")


def test_another_players_requirements_are_as_printed():
    game = scenario(
        player(hand=["search_for_life"]), player(corporation="inventrix"), oxygen=8
    )

    assert not offered(game, "Play Search for Life")

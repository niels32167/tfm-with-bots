"""Mining Guild (2 building Tags): Effect: each time you get any steel or titanium as a placement
bonus on the map, increase your steel Production 1 step. You start with 30 MegaCredits, 5 steel and 1
steel Production."""

import pytest

from tests.helpers import (
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_mining_guild_starts_with_30_megacredits_5_steel_1_steel_production_and_2_building_tags():
    game, first = start_as("mining_guild")

    assert resources(game, first) == {
        "megacredits": 30,
        "steel": 5,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert production(game, first) == {
        "megacredits": 0,
        "steel": 1,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert player_board(game, first)["tags"]["building"] == 2


@pytest.mark.parametrize(
    ("area", "steel", "titanium"),
    [("B2", 1, 0), ("A1", 2, 0), ("H6", 0, 1), ("D1", 0, 1)],
)
def test_a_tile_on_a_steel_or_titanium_bonus_raises_steel_production_1_step_whatever_the_amount(
    area, steel, titanium
):
    game = scenario(player(corporation="mining_guild", steel=0), player())

    pick(game, "City (25 MegaCredits)")
    pick(game, type="area", area=area)

    assert production(game, 0)["steel"] == 1
    assert resources(game, 0)["steel"] == steel
    assert resources(game, 0)["titanium"] == titanium


def test_an_ocean_on_a_steel_or_titanium_bonus_raises_it_too():
    game = scenario(player(corporation="mining_guild", steel=0), player())

    pick(game, "Aquifer")
    pick(game, type="area", area="J5")

    assert production(game, 0)["steel"] == 1
    assert resources(game, 0)["titanium"] == 2


def test_a_tile_on_another_bonus_or_none_changes_nothing():
    game = scenario(player(corporation="mining_guild", steel=0), player())

    pick(game, "City (25 MegaCredits)")
    pick(game, type="area", area="C3")

    assert production(game, 0)["steel"] == 0


def test_another_players_bonus_changes_nothing():
    game = scenario(player(), player(corporation="mining_guild"))

    pick(game, "City (25 MegaCredits)")
    pick(game, type="area", area="B2")

    assert production(game, 1)["steel"] == 0


def test_robotic_workforce_may_copy_its_printed_steel_production():
    game = scenario(
        player(corporation="mining_guild", hand=["robotic_workforce"]), player()
    )

    assert offered(game, "Play Robotic Workforce")
    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["steel"] == 1
    assert "Player 1 copies the production box of Mining Guild." in game.log

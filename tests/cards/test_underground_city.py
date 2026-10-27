"""#032 Underground City (18 MegaCredits, building and city Tags): place a City Tile. Decrease your
energy Production 2 steps and increase your steel Production 2 steps."""

from tests.helpers import area, final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_underground_city_needs_2_energy_production_to_lower():
    one = scenario(player(hand=["underground_city"], production={"energy": 1}), player())
    two = scenario(player(hand=["underground_city"], production={"energy": 2}), player())

    assert not offered(one, "Play Underground City")
    assert offered(two, "Play Underground City")


def test_underground_city_trades_2_energy_production_for_2_steel_production_and_places_a_city():
    game = scenario(player(megacredits=18, hand=["underground_city"], production={"energy": 2}), player())

    pick(game, "Play Underground City (18 MegaCredits)")
    pick(game, area="C3")

    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["steel"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_underground_city_is_worth_no_victory_points():
    game = scenario(player(played_cards=["underground_city"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

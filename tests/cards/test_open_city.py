"""#108 Open City (23 MegaCredits, building and city Tags, 1 Victory Point): requires 12 % Oxygen.
Gain 2 plants. Place a City Tile. Decrease your energy Production 1 step and increase your
MegaCredit Production 4 steps."""

from tests.helpers import area, final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_open_city_needs_12_percent_oxygen():
    with_energy = player(hand=["open_city"], production={"energy": 1})

    assert not offered(scenario(with_energy, player(), oxygen=11), "Play Open City")
    assert offered(scenario(with_energy, player(), oxygen=12), "Play Open City")


def test_open_city_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["open_city"]), player(), oxygen=12), "Play Open City")


def test_open_city_gives_2_plants_trades_production_and_places_a_city():
    game = scenario(player(megacredits=23, hand=["open_city"], production={"energy": 1}), player(), oxygen=12)

    pick(game, "Play Open City (23 MegaCredits)")

    assert resources(game, 0)["plants"] == 2
    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 4
    assert game.decision["kind"] == "area"
    pick(game, area="C3")
    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert game.decision["kind"] == "action"


def test_open_city_is_worth_1_victory_point():
    game = scenario(player(played_cards=["open_city"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

"""#029 Cupola City (16 MegaCredits, building and city Tags): Oxygen must be 9 % or less. Place a
City Tile. Decrease your energy Production 1 step and increase your MegaCredit Production 3 steps."""

from tests.helpers import area, final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_cupola_city_needs_oxygen_at_9_percent_or_less():
    with_energy = player(hand=["cupola_city"], production={"energy": 1})

    assert offered(scenario(with_energy, player(), oxygen=9), "Play Cupola City")
    assert not offered(scenario(with_energy, player(), oxygen=10), "Play Cupola City")


def test_cupola_city_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["cupola_city"]), player()), "Play Cupola City")


def test_cupola_city_trades_production_and_places_a_city():
    game = scenario(player(megacredits=16, hand=["cupola_city"], production={"energy": 1}), player())

    pick(game, "Play Cupola City (16 MegaCredits)")
    pick(game, area="C3")

    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 3
    assert resources(game, 0)["megacredits"] == 0


def test_cupola_city_is_worth_no_victory_points():
    game = scenario(player(played_cards=["cupola_city"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

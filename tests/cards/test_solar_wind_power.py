"""#077 Solar Wind Power (11 MegaCredits, power, space and science Tags): increase your energy
Production 1 step and gain 2 titanium."""

from tests.helpers import pick, player, production, resources, scenario


def test_solar_wind_power_raises_energy_production_by_1_and_gives_2_titanium():
    game = scenario(player(megacredits=11, hand=["solar_wind_power"]), player())

    pick(game, "Play Solar Wind Power")

    assert production(game, 0)["energy"] == 1
    assert resources(game, 0)["titanium"] == 2
    assert resources(game, 0)["megacredits"] == 0

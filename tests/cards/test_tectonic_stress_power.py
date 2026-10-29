"""#145 Tectonic Stress Power (18 MegaCredits, building and power Tags, 1 Victory Point): requires
2 science Tags. Increase your energy Production 3 steps."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_tectonic_stress_power_needs_2_science_tags():
    # Inventors' Guild and Search for Life have a science Tag each.
    one = player(hand=["tectonic_stress_power"], played_cards=["inventors_guild"])
    two = player(hand=["tectonic_stress_power"], played_cards=["inventors_guild", "search_for_life"])

    assert not offered(scenario(one, player()), "Play Tectonic Stress Power")
    assert offered(scenario(two, player()), "Play Tectonic Stress Power")


def test_tectonic_stress_power_raises_energy_production_by_3():
    played = ["inventors_guild", "search_for_life"]
    game = scenario(player(megacredits=18, hand=["tectonic_stress_power"], played_cards=played), player())

    pick(game, "Play Tectonic Stress Power (18 MegaCredits)")

    assert production(game, 0)["energy"] == 3
    assert resources(game, 0)["megacredits"] == 0


def test_tectonic_stress_power_is_worth_1_victory_point():
    game = scenario(player(played_cards=["tectonic_stress_power"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

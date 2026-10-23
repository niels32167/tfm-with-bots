"""#139 Wave Power (8 MegaCredits, power Tag, 1 Victory Point): requires 3 Ocean Tiles.
Increase your energy Production 1 step."""

from tests.helpers import final_scores, ocean, offered, pick, player, production, scenario, terraformed_mars

TWO_OCEANS = [ocean("A2"), ocean("A4")]
THREE_OCEANS = [*TWO_OCEANS, ocean("A5")]


def test_wave_power_needs_3_oceans():
    assert not offered(scenario(player(hand=["wave_power"]), player(), tiles=TWO_OCEANS), "Play Wave Power")
    assert offered(scenario(player(hand=["wave_power"]), player(), tiles=THREE_OCEANS), "Play Wave Power")


def test_wave_power_raises_energy_production_by_1():
    game = scenario(player(hand=["wave_power"]), player(), tiles=THREE_OCEANS)

    pick(game, "Play Wave Power")

    assert production(game, 0)["energy"] == 1


def test_wave_power_is_worth_1_victory_point():
    game = scenario(player(played_cards=["wave_power"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

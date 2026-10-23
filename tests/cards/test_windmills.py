"""#168 Windmills (6 MegaCredits, building and power Tags, 1 Victory Point): requires 7 %
Oxygen. Increase your energy Production 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_windmills_needs_7_percent_oxygen():
    assert not offered(scenario(player(hand=["windmills"]), player(), oxygen=6), "Play Windmills")
    assert offered(scenario(player(hand=["windmills"]), player(), oxygen=7), "Play Windmills")


def test_windmills_raises_energy_production_by_1():
    game = scenario(player(hand=["windmills"]), player(), oxygen=7)

    pick(game, "Play Windmills (6 MegaCredits)")

    assert production(game, 0)["energy"] == 1


def test_windmills_is_worth_1_victory_point():
    game = scenario(player(played_cards=["windmills"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

"""#129 Zeppelins (13 MegaCredits): requires 5 % Oxygen. Increase your MegaCredit Production 1 step
for each City Tile on Mars. 1 Victory Point."""

from tests.helpers import city, final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_zeppelins_requires_5_percent_oxygen():
    assert not offered(scenario(player(hand=["zeppelins"]), player(), oxygen=4), "Play Zeppelins")
    assert offered(scenario(player(hand=["zeppelins"]), player(), oxygen=5), "Play Zeppelins (13 MegaCredits)")


def test_zeppelins_raises_megacredit_production_1_step_for_each_city_on_mars_whoever_owns_it():
    cities = [city("A1", owner=0), city("C3", owner=1), city("G2", owner=1)]
    game = scenario(player(hand=["zeppelins"]), player(), oxygen=5, tiles=cities)

    pick(game, "Play Zeppelins")

    assert production(game, 0)["megacredits"] == 3
    assert production(game, 1)["megacredits"] == 0


def test_zeppelins_is_worth_1_victory_point():
    game = scenario(player(played_cards=["zeppelins"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

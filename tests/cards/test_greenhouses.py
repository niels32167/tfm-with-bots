"""#096 Greenhouses (6 MegaCredits, building and plant Tags): gain 1 plant for each City Tile in
play."""

from tests.helpers import city, final_scores, pick, player, resources, scenario, terraformed_mars


def test_greenhouses_gains_1_plant_for_each_city_in_play_whoever_owns_it():
    cities = [city("A1", owner=0), city("C3", owner=1), city("G2", owner=1)]
    game = scenario(player(megacredits=6, hand=["greenhouses"]), player(), tiles=cities)

    pick(game, "Play Greenhouses (6 MegaCredits)")

    assert resources(game, 0)["plants"] == 3
    assert resources(game, 1)["plants"] == 0


def test_greenhouses_with_no_city_in_play_gains_nothing():
    game = scenario(player(megacredits=6, hand=["greenhouses"]), player())

    pick(game, "Play Greenhouses")

    assert resources(game, 0)["plants"] == 0


def test_greenhouses_has_no_victory_points():
    game = scenario(player(played_cards=["greenhouses"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

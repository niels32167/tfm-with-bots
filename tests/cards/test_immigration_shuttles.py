"""#198 Immigration Shuttles (31 MegaCredits, space and earth Tags, 1 Victory Point for every
3rd City in play): increase your MegaCredit Production 5 steps."""

from tests.helpers import LAND_AREAS, city, final_scores, pick, player, production, scenario, terraformed_mars

# Land Areas far enough apart for Cities, whoever owns them.
APART = ["A1", "A3", "C1", "C3", "C5", "E1"]


def test_immigration_shuttles_raises_megacredit_production_by_5():
    game = scenario(player(hand=["immigration_shuttles"]), player())

    pick(game, "Play Immigration Shuttles")

    assert production(game, 0)["megacredits"] == 5


def test_immigration_shuttles_is_worth_1_victory_point_for_every_3rd_city_in_play():
    assert set(APART) <= set(LAND_AREAS)

    def card_points(cities):
        tiles = [city(area, owner=index % 2) for index, area in enumerate(APART[:cities])]
        game = scenario(player(played_cards=["immigration_shuttles"]), player(), **terraformed_mars(tiles=tiles))
        return final_scores(game)[0]["cards"]

    assert [card_points(cities) for cities in (2, 3, 5, 6)] == [0, 1, 1, 2]

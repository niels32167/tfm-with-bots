"""#158 Industrial Microbes (12 MegaCredits, building and microbe Tags): increase your energy
Production and your steel Production 1 step each."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_industrial_microbes_raises_energy_and_steel_production_by_1_each():
    game = scenario(player(megacredits=12, hand=["industrial_microbes"]), player())

    pick(game, "Play Industrial Microbes (12 MegaCredits)")

    assert production(game, 0)["energy"] == 1
    assert production(game, 0)["steel"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_industrial_microbes_is_worth_no_victory_points():
    game = scenario(player(played_cards=["industrial_microbes"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

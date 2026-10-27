"""#057 Vesta Shipyard (Corporate Era, 15 MegaCredits, space and jovian Tags, 1 Victory Point):
increase your titanium Production 1 step."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_vesta_shipyard_has_no_requirement_and_raises_titanium_production_by_1():
    game = scenario(player(megacredits=15, hand=["vesta_shipyard"]), player())

    pick(game, "Play Vesta Shipyard (15 MegaCredits)")

    assert production(game, 0)["titanium"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_vesta_shipyard_is_worth_1_victory_point():
    game = scenario(player(played_cards=["vesta_shipyard"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

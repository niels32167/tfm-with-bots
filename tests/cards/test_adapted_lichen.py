"""#048 Adapted Lichen (9 MegaCredits, plant Tag): increase your plant Production 1 step."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_adapted_lichen_has_no_requirement_and_raises_plant_production_by_1():
    game = scenario(player(megacredits=9, hand=["adapted_lichen"]), player())

    pick(game, "Play Adapted Lichen (9 MegaCredits)")

    assert production(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their plant Production by 1." in game.log


def test_adapted_lichen_is_worth_no_victory_points():
    game = scenario(player(played_cards=["adapted_lichen"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

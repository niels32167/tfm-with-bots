"""#083 Giant Space Mirror (17 MegaCredits, space and power Tags): increase your energy Production
3 steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_giant_space_mirror_raises_energy_production_by_3():
    game = scenario(player(megacredits=17, hand=["giant_space_mirror"]), player())

    pick(game, "Play Giant Space Mirror (17 MegaCredits)")

    assert production(game, 0)["energy"] == 3
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their energy Production by 3." in game.log


def test_giant_space_mirror_is_worth_no_victory_points():
    game = scenario(player(played_cards=["giant_space_mirror"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

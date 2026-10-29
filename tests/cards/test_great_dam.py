"""#136 Great Dam (12 MegaCredits, building and power Tags, 1 Victory Point): requires 4 Ocean
Tiles. Increase your energy Production 2 steps."""

from tests.helpers import final_scores, ocean, offered, pick, player, production, resources, scenario, terraformed_mars

FOUR_OCEANS = [ocean("A2"), ocean("A4"), ocean("A5"), ocean("B6")]


def test_great_dam_needs_4_oceans():
    assert not offered(scenario(player(hand=["great_dam"]), player(), tiles=FOUR_OCEANS[:3]), "Play Great Dam")
    assert offered(scenario(player(hand=["great_dam"]), player(), tiles=FOUR_OCEANS), "Play Great Dam")


def test_great_dam_raises_energy_production_by_2():
    game = scenario(player(megacredits=12, hand=["great_dam"]), player(), tiles=FOUR_OCEANS)

    pick(game, "Play Great Dam (12 MegaCredits)")

    assert production(game, 0)["energy"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their energy Production by 2." in game.log


def test_great_dam_is_worth_1_victory_point():
    game = scenario(player(played_cards=["great_dam"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

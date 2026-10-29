"""#122 Moss (4 MegaCredits, plant Tag): requires 3 Ocean Tiles and that you lose 1 plant.
Increase your plant Production 1 step."""

from tests.helpers import final_scores, ocean, offered, pick, player, production, resources, scenario, terraformed_mars

THREE_OCEANS = [ocean("A2"), ocean("A4"), ocean("A5")]


def test_moss_needs_3_oceans():
    holding = player(hand=["moss"], plants=1)

    assert not offered(scenario(holding, player(), tiles=THREE_OCEANS[:2]), "Play Moss")
    assert offered(scenario(holding, player(), tiles=THREE_OCEANS), "Play Moss")


def test_moss_needs_a_plant_to_lose():
    assert not offered(scenario(player(hand=["moss"]), player(), tiles=THREE_OCEANS), "Play Moss")


def test_moss_loses_1_plant_and_raises_plant_production_by_1():
    game = scenario(player(megacredits=4, hand=["moss"], plants=1), player(), tiles=THREE_OCEANS)

    pick(game, "Play Moss (4 MegaCredits)")

    assert resources(game, 0)["plants"] == 0
    assert production(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 loses 1 plant." in game.log


def test_moss_is_worth_no_victory_points():
    game = scenario(player(played_cards=["moss"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

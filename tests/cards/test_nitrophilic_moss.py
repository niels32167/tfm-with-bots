"""#146 Nitrophilic Moss (8 MegaCredits, plant Tag): requires 3 Ocean Tiles and that you lose 2
plants. Increase your plant Production 2 steps."""

from tests.helpers import final_scores, ocean, offered, pick, player, production, resources, scenario, terraformed_mars

THREE_OCEANS = [ocean("A2"), ocean("A4"), ocean("A5")]


def test_nitrophilic_moss_needs_3_oceans():
    holding = player(hand=["nitrophilic_moss"], plants=2)

    assert not offered(scenario(holding, player(), tiles=THREE_OCEANS[:2]), "Play Nitrophilic Moss")
    assert offered(scenario(holding, player(), tiles=THREE_OCEANS), "Play Nitrophilic Moss")


def test_nitrophilic_moss_needs_2_plants_to_lose():
    one_plant = player(hand=["nitrophilic_moss"], plants=1)

    assert not offered(scenario(one_plant, player(), tiles=THREE_OCEANS), "Play Nitrophilic Moss")


def test_nitrophilic_moss_loses_2_plants_and_raises_plant_production_by_2():
    game = scenario(player(megacredits=8, hand=["nitrophilic_moss"], plants=3), player(), tiles=THREE_OCEANS)

    pick(game, "Play Nitrophilic Moss (8 MegaCredits)")

    assert resources(game, 0)["plants"] == 1
    assert production(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 loses 2 plants." in game.log


def test_nitrophilic_moss_is_worth_no_victory_points():
    game = scenario(player(played_cards=["nitrophilic_moss"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

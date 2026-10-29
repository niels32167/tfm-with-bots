"""#037 Nitrogen-Rich Asteroid (31 MegaCredits, Event and space Tags): raise your Terraform Rating
2 steps and Temperature 1 step. Increase your plant Production 1 step, or 4 steps if you have 3
plant Tags."""

from tests.helpers import final_scores, pick, player, player_board, production, resources, scenario, terraformed_mars

# Trees, Grass and Heather have a plant Tag each.
THREE_PLANT_TAGS = ["trees", "grass", "heather"]


def test_nitrogen_rich_asteroid_raises_terraform_rating_temperature_and_plant_production_by_1():
    game = scenario(player(megacredits=31, hand=["nitrogen_rich_asteroid"]), player())

    pick(game, "Play Nitrogen-Rich Asteroid (31 MegaCredits)")

    assert player_board(game, 0)["terraform_rating"] == 23
    assert game.player_view(0)["temperature"] == -28
    assert production(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "action"


def test_with_2_plant_tags_nitrogen_rich_asteroid_raises_plant_production_by_1():
    game = scenario(player(hand=["nitrogen_rich_asteroid"], played_cards=THREE_PLANT_TAGS[:2]), player())

    pick(game, "Play Nitrogen-Rich Asteroid")

    assert production(game, 0)["plants"] == 1


def test_with_3_plant_tags_nitrogen_rich_asteroid_raises_plant_production_by_4():
    game = scenario(player(hand=["nitrogen_rich_asteroid"], played_cards=THREE_PLANT_TAGS), player())

    pick(game, "Play Nitrogen-Rich Asteroid")

    assert production(game, 0)["plants"] == 4
    assert "Player 1 raises their plant Production by 1." in game.log
    assert "Player 1 raises their plant Production by 3." in game.log


def test_with_more_than_3_plant_tags_nitrogen_rich_asteroid_still_raises_plant_production_by_4():
    played = [*THREE_PLANT_TAGS, "bushes", "lichen", "algae"]
    game = scenario(player(hand=["nitrogen_rich_asteroid"], played_cards=played), player())

    pick(game, "Play Nitrogen-Rich Asteroid")

    assert production(game, 0)["plants"] == 4


def test_nitrogen_rich_asteroid_has_no_victory_points():
    game = scenario(player(played_cards=["nitrogen_rich_asteroid"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

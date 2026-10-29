"""#148 Insects (9 MegaCredits, microbe Tag): requires 6 % Oxygen. Increase your plant Production 1
step for each plant Tag you have."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_insects_needs_6_percent_oxygen():
    assert not offered(scenario(player(hand=["insects"]), player(), oxygen=5), "Play Insects")
    assert offered(scenario(player(hand=["insects"]), player(), oxygen=6), "Play Insects")


def test_insects_raises_plant_production_by_1_for_each_plant_tag():
    # Algae and Moss have a plant Tag each.
    game = scenario(player(megacredits=9, hand=["insects"], played_cards=["algae", "moss"]), player(), oxygen=6)

    pick(game, "Play Insects (9 MegaCredits)")

    assert production(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their plant Production by 2." in game.log


def test_insects_with_no_plant_tag_raises_nothing():
    # Insects' own Tag is a microbe Tag.
    game = scenario(player(hand=["insects"]), player(), oxygen=6)

    pick(game, "Play Insects")

    assert production(game, 0)["plants"] == 0
    assert not any("plant Production" in line for line in game.log)


def test_insects_is_worth_no_victory_points():
    game = scenario(player(played_cards=["insects"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

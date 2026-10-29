"""#130 Worms (8 MegaCredits, microbe Tag): requires 4 % Oxygen. Increase your plant Production 1
step for every 2 microbe Tags you have, including this."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_worms_needs_4_percent_oxygen():
    assert not offered(scenario(player(hand=["worms"]), player(), oxygen=3), "Play Worms")
    assert offered(scenario(player(hand=["worms"]), player(), oxygen=4), "Play Worms")


def test_worms_raises_plant_production_by_1_for_every_2_microbe_tags_including_its_own():
    # Ants and Tardigrades have a microbe Tag each: with Worms' own that makes 3, so 1 step.
    game = scenario(player(megacredits=8, hand=["worms"], played_cards=["ants", "tardigrades"]), player(), oxygen=4)

    pick(game, "Play Worms (8 MegaCredits)")

    assert production(game, 0)["plants"] == 1
    assert "Player 1 raises their plant Production by 1." in game.log


def test_worms_with_its_own_microbe_tag_and_one_more_raises_plant_production_by_1():
    game = scenario(player(hand=["worms"], played_cards=["ants"]), player(), oxygen=4)

    pick(game, "Play Worms")

    assert production(game, 0)["plants"] == 1


def test_worms_with_only_its_own_microbe_tag_raises_nothing():
    game = scenario(player(hand=["worms"]), player(), oxygen=4)

    pick(game, "Play Worms")

    assert production(game, 0)["plants"] == 0
    assert not any("plant Production" in line for line in game.log)


def test_worms_is_worth_no_victory_points():
    game = scenario(player(played_cards=["worms"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

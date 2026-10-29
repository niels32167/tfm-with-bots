"""#175 Satellites (Corporate Era, 10 MegaCredits, space Tag): increase your MegaCredit Production 1
step for each space Tag you have, including this one."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_satellites_raises_megacredit_production_by_1_for_each_space_tag_including_its_own():
    # Methane From Titan has a space Tag.
    game = scenario(player(megacredits=10, hand=["satellites"], played_cards=["methane_from_titan"]), player())

    pick(game, "Play Satellites (10 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_satellites_with_only_its_own_space_tag_raises_megacredit_production_by_1():
    game = scenario(player(hand=["satellites"]), player())

    pick(game, "Play Satellites")

    assert production(game, 0)["megacredits"] == 1


def test_satellites_is_worth_no_victory_points():
    game = scenario(player(played_cards=["satellites"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

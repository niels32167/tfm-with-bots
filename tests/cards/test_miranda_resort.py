"""#051 Miranda Resort (Corporate Era, 12 MegaCredits, space and jovian Tags, 1 Victory Point):
increase your MegaCredit Production 1 step for each Earth Tag you have."""

from tests.helpers import final_scores, pick, player, production, scenario, terraformed_mars


def test_miranda_resort_raises_megacredit_production_by_1_for_each_earth_tag_in_play():
    # Lunar Beam and Immigration Shuttles have an Earth Tag each; so does Business Contacts,
    # an Event, but no Tag on a played Event counts.
    played = ["lunar_beam", "immigration_shuttles", "business_contacts"]
    game = scenario(player(megacredits=12, hand=["miranda_resort"], played_cards=played), player())

    pick(game, "Play Miranda Resort (12 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert "Player 1 raises their MegaCredit Production by 2." in game.log


def test_miranda_resort_with_no_earth_tag_raises_nothing():
    game = scenario(player(hand=["miranda_resort"], played_cards=["business_contacts"]), player())

    pick(game, "Play Miranda Resort")

    assert production(game, 0)["megacredits"] == 0
    assert not any("MegaCredit Production" in line for line in game.log)


def test_miranda_resort_is_worth_1_victory_point():
    game = scenario(player(played_cards=["miranda_resort"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

"""#137 Cartel (Corporate Era, 8 MegaCredits, Earth Tag): increase your MegaCredit Production 1 step
for each Earth Tag you have, including this."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_cartel_raises_megacredit_production_by_1_for_each_earth_tag_including_its_own():
    # Sponsors has an Earth Tag; so does Business Contacts, an Event, but no Tag on a played
    # Event counts.
    played = ["sponsors", "business_contacts"]
    game = scenario(player(megacredits=8, hand=["cartel"], played_cards=played), player())

    pick(game, "Play Cartel (8 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their MegaCredit Production by 2." in game.log


def test_cartel_with_only_its_own_earth_tag_raises_megacredit_production_by_1():
    game = scenario(player(hand=["cartel"]), player())

    pick(game, "Play Cartel")

    assert production(game, 0)["megacredits"] == 1


def test_cartel_is_worth_no_victory_points():
    game = scenario(player(played_cards=["cartel"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

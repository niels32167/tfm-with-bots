"""#027 Interstellar Colony Ship (24 MegaCredits, Event, space and Earth Tags, 4 Victory Points):
requires that you have 5 science Tags."""

from tests.helpers import final_scores, offered, pick, played_cards, player, resources, scenario, terraformed_mars

# Research has 2 science Tags; Gene Repair, Medical Lab and Fusion Power 1 each.
FOUR_SCIENCE_TAGS = ["research", "gene_repair", "medical_lab"]
FIVE_SCIENCE_TAGS = [*FOUR_SCIENCE_TAGS, "fusion_power"]


def test_interstellar_colony_ship_needs_5_science_tags():
    four = scenario(player(hand=["interstellar_colony_ship"], played_cards=FOUR_SCIENCE_TAGS), player())
    five = scenario(player(hand=["interstellar_colony_ship"], played_cards=FIVE_SCIENCE_TAGS), player())

    assert not offered(four, "Play Interstellar Colony Ship")
    assert offered(five, "Play Interstellar Colony Ship")


def test_interstellar_colony_ship_does_nothing_else_when_played():
    game = scenario(player(megacredits=24, hand=["interstellar_colony_ship"], played_cards=FIVE_SCIENCE_TAGS), player())

    pick(game, "Play Interstellar Colony Ship (24 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert "interstellar_colony_ship" in played_cards(game, 0)
    assert game.decision["kind"] == "action"


def test_interstellar_colony_ship_is_worth_4_victory_points():
    game = scenario(player(played_cards=["interstellar_colony_ship"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [4, 0]

"""#046 Lightning Harvest (Corporate Era, 8 MegaCredits, power Tag, 1 Victory Point): requires 3
science Tags. Increase your energy Production and your MegaCredit Production 1 step each."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars

# Research has two science Tags and Gene Repair one.
THREE_SCIENCE_TAGS = ["research", "gene_repair"]


def test_lightning_harvest_needs_3_science_tags_in_play():
    two = scenario(player(hand=["lightning_harvest"], played_cards=["research"]), player())
    three = scenario(player(hand=["lightning_harvest"], played_cards=THREE_SCIENCE_TAGS), player())

    assert not offered(two, "Play Lightning Harvest")
    assert offered(three, "Play Lightning Harvest")


def test_lightning_harvest_raises_energy_and_megacredit_production_by_1_each():
    game = scenario(player(hand=["lightning_harvest"], played_cards=THREE_SCIENCE_TAGS), player())

    pick(game, "Play Lightning Harvest (8 MegaCredits)")

    assert production(game, 0)["energy"] == 1
    assert production(game, 0)["megacredits"] == 1


def test_lightning_harvest_is_worth_1_victory_point():
    game = scenario(player(played_cards=["lightning_harvest"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

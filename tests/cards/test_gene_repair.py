"""#091 Gene Repair (Corporate Era, 12 MegaCredits, science Tag, 2 Victory Points): requires 3
science Tags. Increase your MegaCredit Production 2 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_gene_repair_needs_3_science_tags():
    # Research has two science Tags and Trans-Neptune Probe one. Gene Repair's own doesn't count
    # while it is in the hand.
    two = player(hand=["gene_repair"], played_cards=["research"])
    three = player(hand=["gene_repair"], played_cards=["research", "trans_neptune_probe"])

    assert not offered(scenario(two, player()), "Play Gene Repair")
    assert offered(scenario(three, player()), "Play Gene Repair")


def test_gene_repair_raises_megacredit_production_by_2():
    holding = player(megacredits=12, hand=["gene_repair"], played_cards=["research", "trans_neptune_probe"])
    game = scenario(holding, player())

    pick(game, "Play Gene Repair (12 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert "Player 1 raises their MegaCredit Production by 2." in game.log


def test_gene_repair_is_worth_2_victory_points():
    game = scenario(player(played_cards=["gene_repair"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]

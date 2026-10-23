"""#092 Io Mining Industries (41 MegaCredits, space and jovian Tags, 1 Victory Point per jovian
Tag you have): increase your titanium Production 2 steps and your MegaCredit Production 2 steps."""

from tests.helpers import final_scores, pick, player, production, scenario, terraformed_mars


def test_io_mining_industries_raises_titanium_and_megacredit_production_by_2():
    game = scenario(player(hand=["io_mining_industries"]), player())

    pick(game, "Play Io Mining Industries (41 MegaCredits)")

    assert production(game, 0)["titanium"] == 2
    assert production(game, 0)["megacredits"] == 2


def test_io_mining_industries_is_worth_1_victory_point_per_jovian_tag_in_play_its_own_included():
    # Colonizer Training Camp has a jovian Tag (and 2 Victory Points of its own); the jovian
    # Tag on Vesta Shipyard in hand does not count.
    game = scenario(
        player(played_cards=["io_mining_industries", "colonizer_training_camp"], hand=["vesta_shipyard"]),
        player(),
        **terraformed_mars(),
    )

    assert [score["cards"] for score in final_scores(game)] == [2 + 2, 0]

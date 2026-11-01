"""#004 Cloud Seeding (11 MegaCredits): requires 3 Ocean Tiles. Decrease your MegaCredit Production
1 step and any heat Production 1 step. Increase your plant Production 2 steps."""

from tests.helpers import (
    OCEAN_AREAS,
    final_scores,
    ocean,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)

THREE_OCEANS = [ocean(name) for name in OCEAN_AREAS[:3]]


def test_cloud_seeding_requires_3_oceans():
    two = [ocean(name) for name in OCEAN_AREAS[:2]]
    assert not offered(
        scenario(player(hand=["cloud_seeding"]), player(production={"heat": 1}), tiles=two), "Play Cloud Seeding"
    )
    assert offered(
        scenario(player(hand=["cloud_seeding"]), player(production={"heat": 1}), tiles=THREE_OCEANS),
        "Play Cloud Seeding (11 MegaCredits)",
    )


def test_cloud_seeding_trades_megacredit_production_for_plant_production_and_lowers_an_opponents_heat():
    game = scenario(player(hand=["cloud_seeding"]), player(production={"heat": 1}), tiles=THREE_OCEANS)

    pick(game, "Play Cloud Seeding")

    assert production(game, 0) == {"megacredits": -1, "steel": 0, "titanium": 0, "plants": 2, "energy": 0, "heat": 0}
    assert production(game, 1)["heat"] == 0


def test_cloud_seeding_needs_someone_with_heat_production_to_lower():
    game = scenario(player(hand=["cloud_seeding"]), player(), tiles=THREE_OCEANS)

    assert not offered(game, "Play Cloud Seeding")


def test_cloud_seeding_cannot_take_megacredit_production_below_minus_5():
    game = scenario(
        player(hand=["cloud_seeding"], production={"megacredits": -5}),
        player(production={"heat": 1}),
        tiles=THREE_OCEANS,
    )

    assert not offered(game, "Play Cloud Seeding")


def test_cloud_seeding_has_no_victory_points():
    game = scenario(player(played_cards=["cloud_seeding"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

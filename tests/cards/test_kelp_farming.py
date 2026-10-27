"""#055 Kelp Farming (17 MegaCredits, plant Tag, 1 Victory Point): requires 6 Ocean Tiles. Increase
your MegaCredit Production 2 steps and your plant Production 3 steps. Gain 2 plants."""

from tests.helpers import (
    OCEAN_AREAS,
    final_scores,
    ocean,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)

FIVE_OCEANS = [ocean(name) for name in OCEAN_AREAS[:5]]
SIX_OCEANS = [ocean(name) for name in OCEAN_AREAS[:6]]


def test_kelp_farming_needs_6_oceans():
    assert not offered(scenario(player(hand=["kelp_farming"]), player(), tiles=FIVE_OCEANS), "Play Kelp Farming")
    assert offered(scenario(player(hand=["kelp_farming"]), player(), tiles=SIX_OCEANS), "Play Kelp Farming")


def test_kelp_farming_raises_megacredit_and_plant_production_and_gives_2_plants():
    game = scenario(player(megacredits=17, hand=["kelp_farming"]), player(), tiles=SIX_OCEANS)

    pick(game, "Play Kelp Farming (17 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert production(game, 0)["plants"] == 3
    assert resources(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_kelp_farming_is_worth_1_victory_point():
    game = scenario(player(played_cards=["kelp_farming"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

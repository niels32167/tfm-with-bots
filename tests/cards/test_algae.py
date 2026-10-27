"""#047 Algae (10 MegaCredits, plant Tag): requires 5 Ocean Tiles. Gain 1 plant and increase your
plant Production 2 steps."""

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

FOUR_OCEANS = [ocean(name) for name in OCEAN_AREAS[:4]]
FIVE_OCEANS = [ocean(name) for name in OCEAN_AREAS[:5]]


def test_algae_needs_5_oceans():
    assert not offered(scenario(player(hand=["algae"]), player(), tiles=FOUR_OCEANS), "Play Algae")
    assert offered(scenario(player(hand=["algae"]), player(), tiles=FIVE_OCEANS), "Play Algae")


def test_algae_gives_1_plant_and_raises_plant_production_by_2():
    game = scenario(player(megacredits=10, hand=["algae"]), player(), tiles=FIVE_OCEANS)

    pick(game, "Play Algae (10 MegaCredits)")

    assert resources(game, 0)["plants"] == 1
    assert production(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_algae_is_worth_no_victory_points():
    game = scenario(player(played_cards=["algae"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

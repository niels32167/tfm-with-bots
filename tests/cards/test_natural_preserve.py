"""#044 Natural Preserve (9 MegaCredits, building and science Tags, 1 Victory Point): Oxygen must be 4 %
or less. Place this Tile NEXT TO NO OTHER TILE. Increase your MegaCredit Production 1 step."""

from tests.helpers import (
    ADJACENT_AREAS,
    LAND_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    labels,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    special,
    terraformed_mars,
)


def test_natural_preserve_needs_oxygen_at_4_percent_or_less():
    holding = player(megacredits=9, hand=["natural_preserve"])

    assert offered(scenario(holding, player(), oxygen=4), "Play Natural Preserve")
    assert not offered(scenario(holding, player(), oxygen=5), "Play Natural Preserve")


def test_natural_preserve_raises_megacredit_production_and_places_its_tile_next_to_no_other_tile():
    game = scenario(
        player(megacredits=9, hand=["natural_preserve"]),
        player(),
        tiles=[city("C3", owner=1)],
    )

    pick(game, "Play Natural Preserve (9 MegaCredits)")

    assert production(game, 0)["megacredits"] == 1
    next_to_the_city = ["C3", *ADJACENT_AREAS["C3"]]
    assert areas_offered(game) == [
        name for name in LAND_AREAS if name not in next_to_the_city
    ]
    assert offered(game, area="J3", on="next_to_no_other_tile", card="natural_preserve")
    pick(game, "Place the Natural Preserve Tile on J3")
    assert area(game, "J3")["tile"] == {
        "type": "special",
        "card": "natural_preserve",
        "owner": 0,
    }


def test_flooding_may_remove_4_megacredits_from_the_owner_of_a_special_tile_next_to_its_ocean():
    # A2 is next to A1, A3, B2 and B3.
    tiles = [special("B2", "natural_preserve", owner=1)]
    game = scenario(
        player(megacredits=7, hand=["flooding"]), player(megacredits=10), tiles=tiles
    )

    pick(game, "Play Flooding")
    pick(game, area="A2")
    assert labels(game) == ["Remove 4 MegaCredits from Player 2", "Remove nothing"]
    pick(game, "Remove 4 MegaCredits from Player 2")

    assert resources(game, 1)["megacredits"] == 6


def test_natural_preserve_is_worth_1_victory_point():
    game = scenario(
        player(played_cards=["natural_preserve"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

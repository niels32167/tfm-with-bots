"""#188 Flooding (7 MegaCredits, Event Tag): place an Ocean Tile. If there are Tiles next to this
Ocean Tile, you may remove 4 MegaCredits from the owner of one of those Tiles. −1 Victory Point."""

from tests.helpers import (
    OCEAN_AREAS,
    city,
    final_scores,
    greenery,
    labels,
    ocean,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)

# A2 is next to A1, A3, B2 and B3.


def test_flooding_may_remove_4_megacredits_from_the_owner_of_a_tile_next_to_its_ocean():
    tiles = [city("A1", owner=1), greenery("B3", owner=2), city("J1", owner=3)]
    game = scenario(
        player(megacredits=7, hand=["flooding"]),
        player(megacredits=10),
        player(megacredits=3),
        player(megacredits=10),
        tiles=tiles,
    )

    pick(game, "Play Flooding (7 MegaCredits)")
    pick(game, area="A2")
    assert labels(game) == [
        "Remove 4 MegaCredits from Player 2",
        "Remove 3 MegaCredits from Player 3",
        "Remove nothing",
    ]
    pick(game, "Remove 4 MegaCredits from Player 2")

    assert resources(game, 1)["megacredits"] == 6
    assert game.decision["kind"] == "action"


def test_floodings_own_tiles_next_to_its_ocean_offer_nothing():
    game = scenario(player(megacredits=17, hand=["flooding"]), player(megacredits=10), tiles=[city("A1", owner=0)])

    pick(game, "Play Flooding")
    pick(game, area="A2")

    assert game.decision["kind"] == "action"
    assert resources(game, 1)["megacredits"] == 10


def test_once_9_oceans_are_placed_flooding_places_none_and_removes_nothing():
    tiles = [ocean(name) for name in OCEAN_AREAS[:9]] + [city("A1", owner=1)]
    game = scenario(player(megacredits=7, hand=["flooding"]), player(megacredits=10), tiles=tiles)

    pick(game, "Play Flooding")

    assert game.decision["kind"] == "action"
    assert resources(game, 1)["megacredits"] == 10


def test_flooding_is_worth_minus_1_victory_point():
    game = scenario(player(played_cards=["flooding"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-1, 0]

"""#066 Land Claim (Corporate Era, 1 MegaCredit, Event Tag): place your marker on a non-reserved Area.
Only you may place a Tile there."""

import pytest

from tests.helpers import (
    LAND_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    greenery,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def test_land_claim_claims_a_free_area_on_mars_reserved_for_nothing():
    game = scenario(
        player(megacredits=1, hand=["land_claim"]),
        player(),
        tiles=[city("C3", owner=1)],
    )

    pick(game, "Play Land Claim (1 MegaCredit)")

    assert game.decision["kind"] == "area"
    assert areas_offered(game) == [name for name in LAND_AREAS if name != "C3"]
    assert offered(game, type="claim_area", area="A1")
    pick(game, "Claim A1")
    assert area(game, "A1")["claimed_by"] == 0
    assert area(game, "A1")["tile"] is None
    assert "Player 1 claims A1 with Land Claim." in game.log
    assert game.decision["kind"] == "action"


def test_only_the_claiming_player_may_place_a_tile_on_the_claimed_area():
    others = scenario(
        player(megacredits=25), player(), land_claim={"area": "A1", "player": 1}
    )
    pick(others, "City (25 MegaCredits)")
    assert "A1" not in areas_offered(others)

    own = scenario(
        player(megacredits=25), player(), land_claim={"area": "A1", "player": 0}
    )
    pick(own, "City (25 MegaCredits)")
    pick(own, "Place the City on A1")
    # The placement bonus printed on it still goes to its Player.
    assert resources(own, 0)["steel"] == 2


def test_a_claimed_area_is_kept_from_every_other_tile_an_ocean_on_land_included():
    # A Greenery goes next to its owner's Tiles if it can. B1 is next to A1, B2, C1 and C2, so only the
    # claimed A1 is left there, and the Greenery may go on any other free land instead.
    tiles = [
        city("B1", owner=0),
        city("B2", owner=1),
        greenery("C1", owner=1),
        greenery("C2", owner=1),
    ]
    claimed_by_other = {"area": "A1", "player": 1}
    game = scenario(
        player(megacredits=23), player(), tiles=tiles, land_claim=claimed_by_other
    )

    pick(game, "Greenery (23 MegaCredits)")
    assert "A1" not in areas_offered(game)
    assert "J3" in areas_offered(game)

    lake = scenario(
        player(megacredits=15, hand=["artificial_lake"]),
        player(),
        temperature=-6,
        land_claim=claimed_by_other,
    )
    pick(lake, "Play Artificial Lake")
    assert "A1" not in areas_offered(lake)


def test_land_claim_needs_a_free_area_on_mars_reserved_for_nothing():
    tiles = [city(name, owner=1) for name in LAND_AREAS]

    assert not offered(
        scenario(player(megacredits=1, hand=["land_claim"]), player(), tiles=tiles),
        "Play Land Claim",
    )


def test_a_scenarios_land_claim_is_on_free_land_or_under_its_players_tile():
    scenario(
        player(),
        player(),
        tiles=[city("A1", owner=0)],
        land_claim={"area": "A1", "player": 0},
    )
    with pytest.raises(ValueError, match="A2, which is reserved"):
        scenario(player(), player(), land_claim={"area": "A2", "player": 0})
    with pytest.raises(ValueError, match="claimed by Player 1"):
        scenario(
            player(),
            player(),
            tiles=[city("A1", owner=1)],
            land_claim={"area": "A1", "player": 0},
        )


def test_land_claim_is_worth_no_victory_points():
    game = scenario(player(played_cards=["land_claim"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

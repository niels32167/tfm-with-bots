"""#193 Plantation (15 MegaCredits, plant Tag): requires 2 science Tags. Place a Greenery Tile and
raise Oxygen 1 step."""

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
    player_board,
    resources,
    scenario,
    terraformed_mars,
)

TWO_SCIENCE_TAGS = ["inventors_guild", "search_for_life"]


def test_plantation_needs_2_science_tags():
    one = player(hand=["plantation"], played_cards=TWO_SCIENCE_TAGS[:1])
    two = player(hand=["plantation"], played_cards=TWO_SCIENCE_TAGS)

    assert not offered(scenario(one, player()), "Play Plantation")
    assert offered(scenario(two, player()), "Play Plantation")


def test_plantation_places_a_greenery_next_to_the_players_own_tiles_and_raises_oxygen():
    holding = player(megacredits=15, hand=["plantation"], played_cards=TWO_SCIENCE_TAGS)
    game = scenario(holding, player(), oxygen=5, tiles=[city("C3", owner=0)])

    pick(game, "Play Plantation (15 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "area"
    assert areas_offered(game) == ["B2", "B3", "C2", "C4", "D3", "D4"]
    pick(game, area="D3")
    assert area(game, "D3")["tile"] == {"type": "greenery", "owner": 0}
    assert game.player_view(0)["oxygen"] == 6
    assert player_board(game, 0)["terraform_rating"] == 21
    assert "Player 1 places a Greenery on D3." in game.log
    assert game.decision["kind"] == "action"


def test_plantation_is_not_offered_without_an_area_for_its_greenery():
    every_land_area_but_a1 = [greenery(name, owner=1) for name in LAND_AREAS if name != "A1"]
    holding = player(hand=["plantation"], played_cards=TWO_SCIENCE_TAGS)

    assert offered(scenario(holding, player(), tiles=every_land_area_but_a1), "Play Plantation")
    assert not offered(
        scenario(holding, player(), tiles=[*every_land_area_but_a1, greenery("A1", owner=1)]), "Play Plantation"
    )


def test_plantation_is_worth_no_victory_points():
    game = scenario(player(played_cards=["plantation"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

"""#064 Mining Area (Corporate Era, 4 MegaCredits, building Tag): place this Tile on an Area with a steel
or titanium placement bonus, adjacent to another of your Tiles. Increase your Production of that
resource 1 step."""

from tests.helpers import (
    area,
    areas_offered,
    city,
    final_scores,
    greenery,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    special,
    terraformed_mars,
)


def test_mining_area_needs_free_land_with_a_steel_or_titanium_bonus_next_to_its_players_tile():
    holding = player(megacredits=4, hand=["mining_area"])

    assert not offered(scenario(holding, player()), "Play Mining Area")
    # C6 is next to C7, which has a steel bonus; G3 is next to no such Area.
    assert not offered(
        scenario(holding, player(), tiles=[city("C6", owner=1)]), "Play Mining Area"
    )
    assert not offered(
        scenario(holding, player(), tiles=[city("G3", owner=0)]), "Play Mining Area"
    )
    assert offered(
        scenario(holding, player(), tiles=[city("C6", owner=0)]), "Play Mining Area"
    )


def test_mining_area_places_its_tile_next_to_its_players_tile_and_raises_that_production():
    # H5 is next to H6 (titanium bonus); B3 is next to B2 (Tharsis Tholus, steel bonus) and A2 (an Ocean Area).
    tiles = [
        greenery("H5", owner=0),
        special("B3", "nuclear_zone", owner=0),
        city("C7", owner=1),
    ]
    game = scenario(player(megacredits=4, hand=["mining_area"]), player(), tiles=tiles)

    pick(game, "Play Mining Area (4 MegaCredits)")

    assert areas_offered(game) == ["B2", "H6"]
    assert offered(game, area="H6", on="steel_or_titanium_bonus_next_to_own_tile")
    pick(game, "Place the Mining Area Tile on H6")
    assert area(game, "H6")["tile"] == {
        "type": "special",
        "card": "mining_area",
        "owner": 0,
    }
    assert production(game, 0)["titanium"] == 1
    assert resources(game, 0)["titanium"] == 1


def test_robotic_workforce_copies_the_production_mining_areas_tile_gave():
    holding = player(
        megacredits=9, hand=["robotic_workforce"], played_cards=["mining_area"]
    )
    game = scenario(holding, player(), tiles=[special("C7", "mining_area", owner=0)])

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["steel"] == 1


def test_mining_area_is_worth_no_victory_points():
    game = scenario(
        player(played_cards=["mining_area"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

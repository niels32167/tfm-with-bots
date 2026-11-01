"""#123 Industrial Center (Corporate Era, 4 MegaCredits, building Tag): Action: spend 7 MegaCredits to
increase your steel Production 1 step. Place this Tile ADJACENT TO A CITY TILE."""

from tests.helpers import (
    ADJACENT_AREAS,
    LAND_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    special,
    terraformed_mars,
)


def test_industrial_center_needs_free_land_next_to_a_city():
    holding = player(megacredits=4, hand=["industrial_center"])

    assert not offered(scenario(holding, player()), "Play Industrial Center")
    assert offered(
        scenario(holding, player(), tiles=[city("C3", owner=1)]),
        "Play Industrial Center",
    )


def test_industrial_center_places_its_tile_next_to_a_city_whoever_owns_it():
    tiles = [city("C3", owner=1), special("J3", "capital", owner=0)]
    game = scenario(
        player(megacredits=4, hand=["industrial_center"]), player(), tiles=tiles
    )

    pick(game, "Play Industrial Center (4 MegaCredits)")

    next_to_a_city = ADJACENT_AREAS["C3"] + ADJACENT_AREAS["J3"]
    assert areas_offered(game) == [
        name for name in LAND_AREAS if name in next_to_a_city
    ]
    assert offered(game, area="C4", on="next_to_a_city")
    pick(game, "Place the Industrial Center Tile on C4")
    assert area(game, "C4")["tile"] == {
        "type": "special",
        "card": "industrial_center",
        "owner": 0,
    }


def test_industrial_centers_action_spends_7_megacredits_to_raise_steel_production_1_step():
    tiles = [city("C3", owner=0), special("C4", "industrial_center", owner=0)]
    game = scenario(
        player(megacredits=7, played_cards=["industrial_center"]), player(), tiles=tiles
    )

    pick(game, "Use the action of Industrial Center")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["steel"] == 1


def test_robotic_workforce_cannot_copy_industrial_centers_production_box_in_its_action():
    holding = player(
        megacredits=9, hand=["robotic_workforce"], played_cards=["industrial_center"]
    )

    assert not offered(scenario(holding, player()), "Play Robotic Workforce")


def test_industrial_center_is_worth_no_victory_points():
    game = scenario(
        player(played_cards=["industrial_center"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

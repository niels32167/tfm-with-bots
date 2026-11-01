"""#081 Ganymede Colony (20 MegaCredits, jovian, space and city Tags): place a City Tile ON THE RESERVED
AREA. 1 Victory Point per jovian Tag you have."""

from tests.helpers import (
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
    terraformed_mars,
)

GANYMEDE = "ganymede_colony"


def test_ganymede_colony_places_its_city_off_mars():
    game = scenario(player(megacredits=20, hand=["ganymede_colony"]), player())

    pick(game, "Play Ganymede Colony (20 MegaCredits)")

    assert areas_offered(game) == [GANYMEDE]
    assert offered(game, area=GANYMEDE, on="ganymede_colony")
    pick(game, "Place the City on Ganymede Colony")
    assert area(game, GANYMEDE)["tile"] == {"type": "city", "owner": 0}
    assert resources(game, 0)["megacredits"] == 0


def test_ganymede_colonys_city_sets_off_rover_construction_and_immigrant_city():
    other = player(megacredits=0, played_cards=["rover_construction", "immigrant_city"])
    game = scenario(player(megacredits=20, hand=["ganymede_colony"]), other)

    pick(game, "Play Ganymede Colony")
    pick(game, area=GANYMEDE)

    assert resources(game, 1)["megacredits"] == 2
    assert production(game, 1)["megacredits"] == 1


def test_martian_rails_leaves_out_the_city_off_mars():
    tiles = [city(GANYMEDE, owner=1)]
    game = scenario(
        player(megacredits=0, energy=1, played_cards=["martian_rails"]),
        player(),
        tiles=tiles,
    )

    pick(game, "Use the action of Martian Rails")

    assert resources(game, 0)["megacredits"] == 0


def test_ganymede_colony_is_worth_1_victory_point_per_jovian_tag_its_own_included():
    played = ["ganymede_colony", "io_mining_industries", "acquired_company"]
    game = scenario(
        player(played_cards=played),
        player(),
        **terraformed_mars(tiles=[city(GANYMEDE, owner=0)]),
    )

    # Io Mining Industries is worth 1 Victory Point per jovian Tag too; Acquired Company has none.
    assert final_scores(game)[0]["cards"] == 4

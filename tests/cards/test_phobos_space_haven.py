"""#021 Phobos Space Haven (25 MegaCredits, space and city Tags, 3 Victory Points): increase your
titanium Production 1 step and place a City Tile ON THE RESERVED AREA."""

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

PHOBOS = "phobos_space_haven"
CITY_ON_PHOBOS = city(PHOBOS, owner=1)


def test_phobos_space_haven_raises_titanium_production_and_places_its_city_off_mars():
    game = scenario(player(megacredits=25, hand=["phobos_space_haven"]), player())

    pick(game, "Play Phobos Space Haven (25 MegaCredits)")

    assert production(game, 0)["titanium"] == 1
    assert areas_offered(game) == [PHOBOS]
    assert offered(game, area=PHOBOS, on="phobos_space_haven")
    pick(game, "Place the City on Phobos Space Haven")
    assert area(game, PHOBOS)["tile"] == {"type": "city", "owner": 0}
    assert game.decision["kind"] == "action"


def test_phobos_space_havens_city_sets_off_rover_construction_and_immigrant_city():
    other = player(megacredits=0, played_cards=["rover_construction", "immigrant_city"])
    game = scenario(player(megacredits=25, hand=["phobos_space_haven"]), other)

    pick(game, "Play Phobos Space Haven")
    pick(game, area=PHOBOS)

    assert resources(game, 1)["megacredits"] == 2
    assert production(game, 1)["megacredits"] == 1


def test_martian_rails_leaves_out_the_city_off_mars():
    tiles = [CITY_ON_PHOBOS, city("C3", owner=1)]
    game = scenario(
        player(megacredits=0, energy=1, played_cards=["martian_rails"]),
        player(),
        tiles=tiles,
    )

    pick(game, "Use the action of Martian Rails")

    assert resources(game, 0)["megacredits"] == 1


def test_zeppelins_leaves_out_the_city_off_mars():
    game = scenario(
        player(megacredits=13, hand=["zeppelins"]),
        player(),
        oxygen=5,
        tiles=[CITY_ON_PHOBOS],
    )

    pick(game, "Play Zeppelins")

    assert production(game, 0)["megacredits"] == 0


def test_greenhouses_and_energy_saving_count_the_city_off_mars():
    holding = player(megacredits=21, hand=["greenhouses", "energy_saving"])
    game = scenario(holding, player(), tiles=[CITY_ON_PHOBOS, city("C3", owner=1)])

    pick(game, "Play Greenhouses")
    pick(game, "Play Energy Saving")

    assert resources(game, 0)["plants"] == 2
    assert production(game, 0)["energy"] == 2


def test_phobos_space_haven_is_worth_3_victory_points():
    game = scenario(
        player(played_cards=["phobos_space_haven"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [3, 0]

"""#067 Mining Rights (9 MegaCredits, building Tag): place this Tile on an Area with a steel or titanium
placement bonus. Increase that Production 1 step."""

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
    special,
    terraformed_mars,
)

# The free land with a steel or titanium placement bonus. A2 and J5 have one too, but are reserved
# for Oceans.
STEEL_OR_TITANIUM = ["A1", "B2", "C7", "D1", "H1", "H6", "J1", "J2"]


def test_mining_rights_places_its_tile_on_free_land_with_a_steel_or_titanium_bonus():
    game = scenario(
        player(megacredits=9, hand=["mining_rights"]),
        player(),
        tiles=[city("C7", owner=1)],
    )

    pick(game, "Play Mining Rights (9 MegaCredits)")

    assert areas_offered(game) == [name for name in STEEL_OR_TITANIUM if name != "C7"]
    assert offered(game, area="A1", on="steel_or_titanium_bonus")
    pick(game, "Place the Mining Rights Tile on A1")
    assert area(game, "A1")["tile"] == {
        "type": "special",
        "card": "mining_rights",
        "owner": 0,
    }


def test_mining_rights_on_a_steel_bonus_raises_steel_production_and_gives_the_bonus():
    game = scenario(player(megacredits=9, hand=["mining_rights"]), player())

    pick(game, "Play Mining Rights")
    pick(game, area="A1")

    assert production(game, 0)["steel"] == 1
    assert production(game, 0)["titanium"] == 0
    assert resources(game, 0)["steel"] == 2


def test_mining_rights_on_a_titanium_bonus_raises_titanium_production():
    game = scenario(player(megacredits=9, hand=["mining_rights"]), player())

    pick(game, "Play Mining Rights")
    pick(game, area="D1")

    assert production(game, 0)["titanium"] == 1
    assert production(game, 0)["steel"] == 0


def test_mining_rights_needs_a_free_area_with_a_steel_or_titanium_bonus():
    tiles = [city(name, owner=1) for name in ["A1", "C7", "H1", "J1"]] + [
        special(name, "nuclear_zone", owner=1) for name in ["B2", "D1", "H6", "J2"]
    ]

    assert not offered(
        scenario(player(megacredits=9, hand=["mining_rights"]), player(), tiles=tiles),
        "Play Mining Rights",
    )


def test_robotic_workforce_copies_the_production_mining_rights_tile_gave():
    holding = player(
        megacredits=9, hand=["robotic_workforce"], played_cards=["mining_rights"]
    )
    game = scenario(holding, player(), tiles=[special("H6", "mining_rights", owner=0)])

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["titanium"] == 1
    assert production(game, 0)["steel"] == 0


def test_mining_rights_is_worth_no_victory_points():
    game = scenario(
        player(played_cards=["mining_rights"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

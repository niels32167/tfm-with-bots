"""#P37 Lava Tube Settlement (Prelude's Project Card, 15 MegaCredits, building and city Tags): decrease your energy
Production 1 step and increase your MegaCredit Production 2 steps. Place a City Tile on a VOLCANIC AREA regardless of
adjacent cities."""

from tests.helpers import (
    area,
    areas_offered,
    city,
    final_scores,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)

HOLDING = player(megacredits=15, hand=["lava_tube_settlement"], production={"energy": 1})


def test_lava_tube_settlement_needs_1_energy_production_to_lower():
    game = scenario(player(megacredits=15, hand=["lava_tube_settlement"]), player(), prelude=True)

    assert not offered(game, "Play Lava Tube Settlement")


def test_lava_tube_settlement_places_its_city_on_a_free_volcano_even_next_to_another_city():
    # C1 (Ascraeus Mons) is taken, and D2 is next to D1 (Pavonis Mons).
    game = scenario(HOLDING, player(), prelude=True, tiles=[city("C1", owner=1), city("D2", owner=1)])

    pick(game, "Play Lava Tube Settlement (15 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 2
    assert areas_offered(game) == ["B2", "D1", "E1"]
    pick(game, "Place the City on D1 (Pavonis Mons)")
    assert area(game, "D1")["tile"] == {"type": "city", "owner": 0}


def test_lava_tube_settlement_needs_a_free_volcano():
    tiles = [city(name, owner=1) for name in ["B2", "C1", "D1", "E1"]]

    assert not offered(scenario(HOLDING, player(), prelude=True, tiles=tiles), "Play Lava Tube Settlement")


def test_lava_tube_settlement_is_worth_no_victory_points():
    game = scenario(player(played_cards=["lava_tube_settlement"]), player(), prelude=True, **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

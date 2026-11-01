"""#140 Lava Flows (18 MegaCredits, Event Tag): raise Temperature 2 steps and place this Tile ON EITHER
THARSIS THOLUS, ASCRAEUS MONS, PAVONIS MONS OR ARSIA MONS."""

from tests.helpers import (
    area,
    areas_offered,
    city,
    final_scores,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)

# Tharsis Tholus, Ascraeus Mons, Pavonis Mons and Arsia Mons.
VOLCANOES = ["B2", "C1", "D1", "E1"]


def test_lava_flows_raises_temperature_2_steps_and_places_its_tile_on_a_free_volcano():
    game = scenario(
        player(megacredits=18, hand=["lava_flows"]),
        player(),
        tiles=[city("C1", owner=1)],
    )

    pick(game, "Play Lava Flows (18 MegaCredits)")

    assert game.player_view(0)["temperature"] == -26
    assert areas_offered(game) == ["B2", "D1", "E1"]
    assert offered(game, area="B2", on="volcanoes")
    pick(game, "Place the Lava Flows Tile on D1 (Pavonis Mons)")
    assert area(game, "D1")["tile"] == {
        "type": "special",
        "card": "lava_flows",
        "owner": 0,
    }


def test_lava_flows_needs_a_free_volcano():
    tiles = [city(name, owner=1) for name in VOLCANOES[:2]] + [
        city(name, owner=0) for name in VOLCANOES[2:]
    ]

    assert not offered(
        scenario(player(megacredits=18, hand=["lava_flows"]), player(), tiles=tiles),
        "Play Lava Flows",
    )


def test_lava_flows_is_worth_no_victory_points():
    game = scenario(player(played_cards=["lava_flows"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

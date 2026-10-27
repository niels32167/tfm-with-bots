"""#016 Domed Crater (24 MegaCredits, building and city Tags, 1 Victory Point): Oxygen must be 7 %
or less. Gain 3 plants. Place a City Tile. Decrease your energy Production 1 step and increase your
MegaCredit Production 3 steps."""

from tests.helpers import area, final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_domed_crater_needs_oxygen_at_7_percent_or_less():
    with_energy = player(hand=["domed_crater"], production={"energy": 1})

    assert offered(scenario(with_energy, player(), oxygen=7), "Play Domed Crater")
    assert not offered(scenario(with_energy, player(), oxygen=8), "Play Domed Crater")


def test_domed_crater_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["domed_crater"]), player()), "Play Domed Crater")


def test_domed_crater_gives_3_plants_trades_production_and_places_a_city():
    game = scenario(player(megacredits=24, hand=["domed_crater"], production={"energy": 1}), player())

    pick(game, "Play Domed Crater (24 MegaCredits)")

    assert resources(game, 0)["plants"] == 3
    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 3
    assert game.decision["kind"] == "area"
    pick(game, area="C3")
    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "action"


def test_domed_crater_is_worth_1_victory_point():
    game = scenario(player(played_cards=["domed_crater"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

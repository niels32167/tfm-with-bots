"""#042 Archaebacteria (6 MegaCredits, microbe Tag): it must be -18 °C or colder. Increase your
plant Production 1 step."""

from tests.helpers import offered, pick, player, production, scenario


def test_archaebacteria_needs_minus_18_degrees_or_colder():
    assert offered(scenario(player(hand=["archaebacteria"]), player(), temperature=-18), "Play Archaebacteria")
    assert not offered(scenario(player(hand=["archaebacteria"]), player(), temperature=-16), "Play Archaebacteria")


def test_archaebacteria_raises_plant_production_by_1():
    game = scenario(player(hand=["archaebacteria"]), player())

    pick(game, "Play Archaebacteria")

    assert production(game, 0)["plants"] == 1

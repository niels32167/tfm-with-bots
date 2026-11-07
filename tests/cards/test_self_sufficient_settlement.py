"""#P29 Self-Sufficient Settlement (Prelude Card, building and city Tags): increase your MegaCredit
Production 2 steps. Place a City Tile."""

from tests.helpers import area, pick, player, production, scenario


def test_self_sufficient_settlement_raises_megacredit_production_by_2_and_places_a_city():
    game = scenario(player(prelude_cards=["self_sufficient_settlement"]), player(), prelude=True)

    pick(game, area="H2")

    assert production(game, 0)["megacredits"] == 2
    assert area(game, "H2")["tile"] == {"type": "city", "owner": 0}

"""#P20 Metals Company (Prelude Card): increase your MegaCredit, steel and titanium Production 1 step."""

from tests.helpers import player, production, scenario


def test_metals_company_raises_megacredit_steel_and_titanium_production_by_1():
    game = scenario(player(prelude_cards=["metals_company"]), player(), prelude=True)

    raised = production(game, 0)
    assert (raised["megacredits"], raised["steel"], raised["titanium"]) == (1, 1, 1)

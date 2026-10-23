"""#144 Titanium Mine (Corporate Era, 7 MegaCredits, building Tag): increase your titanium
Production 1 step."""

from tests.helpers import pick, player, production, scenario


def test_titanium_mine_raises_titanium_production_by_1():
    game = scenario(player(hand=["titanium_mine"]), player())

    pick(game, "Play Titanium Mine (7 MegaCredits)")

    assert production(game, 0)["titanium"] == 1

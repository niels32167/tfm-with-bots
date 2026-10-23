"""#056 Mine (Corporate Era, 4 MegaCredits, building Tag): increase your steel Production 1 step."""

from tests.helpers import hand, pick, played_cards, player, production, resources, scenario


def test_mine_raises_steel_production_by_1():
    game = scenario(player(megacredits=10, hand=["mine"]), player())

    pick(game, "Play Mine")

    assert production(game, 0)["steel"] == 1
    assert resources(game, 0)["megacredits"] == 6
    assert hand(game, 0) == []
    assert played_cards(game, 0) == ["mine"]
    assert "Player 1 plays Mine, paying 4 MegaCredits." in game.log
    assert "Player 1 raises their steel Production by 1." in game.log

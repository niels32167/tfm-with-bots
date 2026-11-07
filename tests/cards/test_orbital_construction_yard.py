"""#P25 Orbital Construction Yard (Prelude Card, space Tag): increase your titanium Production 1 step.
Gain 4 titanium."""

from tests.helpers import player, player_board, production, resources, scenario


def test_orbital_construction_yard_raises_titanium_production_and_gains_4_titanium():
    game = scenario(player(prelude_cards=["orbital_construction_yard"]), player(), prelude=True)

    assert production(game, 0)["titanium"] == 1
    assert resources(game, 0)["titanium"] == 4
    assert player_board(game, 0)["tags"]["space"] == 1

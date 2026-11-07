"""#P13 Galilean Mining (Prelude Card): increase your titanium Production 2 steps. Pay 5 MegaCredits."""

from tests.helpers import player, player_board, production, resources, scenario


def test_galilean_mining_raises_titanium_production_2_steps_and_costs_5_megacredits():
    game = scenario(player(prelude_cards=["galilean_mining"]), player(), prelude=True)

    assert production(game, 0)["titanium"] == 2
    assert resources(game, 0)["megacredits"] == 37
    assert player_board(game, 0)["tags"]["jovian"] == 1
    assert "Player 1 pays 5 MegaCredits for Galilean Mining." in game.log


def test_with_fewer_than_5_megacredits_it_cant_be_played_and_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["galilean_mining"], megacredits=4), player(), prelude=True)

    assert resources(game, 0)["megacredits"] == 19
    assert production(game, 0)["titanium"] == 0
    assert player_board(game, 0)["played_prelude_cards"] == []

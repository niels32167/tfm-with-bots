"""#205 Rad-Chem Factory (8 MegaCredits, building Tag): decrease your energy Production 1 step.
Raise your Terraform Rating 2 steps."""

from tests.helpers import offered, pick, player, player_board, production, scenario


def test_rad_chem_factory_needs_energy_production_to_lower():
    assert not offered(scenario(player(hand=["rad_chem_factory"]), player()), "Play Rad-Chem Factory")


def test_rad_chem_factory_trades_1_energy_production_for_2_terraform_rating():
    game = scenario(player(hand=["rad_chem_factory"], production={"energy": 1}), player())

    pick(game, "Play Rad-Chem Factory")

    assert production(game, 0)["energy"] == 0
    assert player_board(game, 0)["terraform_rating"] == 22
    assert "Player 1 raises their Terraform Rating by 2." in game.log

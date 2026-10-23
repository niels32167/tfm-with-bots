"""#138 Strip Mine (25 MegaCredits, building Tag): decrease your energy Production 2 steps.
Increase your steel Production 2 steps and your titanium Production 1 step. Raise Oxygen 2 steps."""

from tests.helpers import offered, pick, player, player_board, production, scenario


def test_strip_mine_needs_2_energy_production_to_lower():
    assert not offered(scenario(player(hand=["strip_mine"], production={"energy": 1}), player()), "Play Strip Mine")
    assert offered(scenario(player(hand=["strip_mine"], production={"energy": 2}), player()), "Play Strip Mine")


def test_strip_mine_trades_energy_production_for_steel_and_titanium_production_and_raises_oxygen_2_steps():
    game = scenario(player(hand=["strip_mine"], production={"energy": 2}), player())

    pick(game, "Play Strip Mine (25 MegaCredits)")

    assert production(game, 0) == {"megacredits": 0, "steel": 2, "titanium": 1, "plants": 0, "energy": 0, "heat": 0}
    assert game.player_view(0)["oxygen"] == 2
    assert player_board(game, 0)["terraform_rating"] == 22


def test_strip_mine_reaching_8_percent_oxygen_and_0_degrees_gives_the_ocean_to_place_last():
    game = scenario(player(hand=["strip_mine"], production={"energy": 2}), player(), oxygen=7, temperature=-2)

    pick(game, "Play Strip Mine")
    assert game.decision["kind"] == "area"
    assert (game.player_view(0)["oxygen"], game.player_view(0)["temperature"]) == (9, 0)

    pick(game, area="A2")

    assert player_board(game, 0)["terraform_rating"] == 24  # 2 Oxygen steps, a Temperature step and an Ocean
    assert game.decision["kind"] == "action"

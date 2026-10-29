"""#102 Power Grid (18 MegaCredits, power Tag): increase your energy Production 1 step for each
power Tag you have, including this."""

from tests.helpers import final_scores, pick, player, production, scenario, terraformed_mars


def test_power_grid_raises_energy_production_by_1_for_each_power_tag_including_its_own():
    # Peroxide Power and Giant Space Mirror have a power Tag each.
    game = scenario(player(hand=["power_grid"], played_cards=["peroxide_power", "giant_space_mirror"]), player())

    pick(game, "Play Power Grid (18 MegaCredits)")

    assert production(game, 0)["energy"] == 3
    assert "Player 1 raises their energy Production by 3." in game.log


def test_power_grid_on_its_own_raises_energy_production_by_1():
    game = scenario(player(hand=["power_grid"]), player())

    pick(game, "Play Power Grid")

    assert production(game, 0)["energy"] == 1


def test_power_grid_is_worth_no_victory_points():
    game = scenario(player(played_cards=["power_grid"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

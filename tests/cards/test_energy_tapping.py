"""#201 Energy Tapping (3 MegaCredits, power Tag): decrease any energy Production 1 step and increase
your own 1 step. −1 Victory Point."""

from tests.helpers import final_scores, labels, pick, player, production, scenario, terraformed_mars


def test_energy_tapping_takes_an_energy_production_step_from_the_opponent_picked():
    game = scenario(
        player(hand=["energy_tapping"], production={"energy": 4}),
        player(production={"energy": 1}),
        player(production={"energy": 1}),
    )

    pick(game, "Play Energy Tapping (3 MegaCredits)")
    assert labels(game) == ["Lower Player 2's energy Production by 1", "Lower Player 3's energy Production by 1"]
    pick(game, "Player 2")

    assert [production(game, each)["energy"] for each in range(3)] == [5, 0, 1]


def test_energy_tapping_never_offers_the_players_own_energy_production_while_an_opponent_has_some():
    game = scenario(player(hand=["energy_tapping"], production={"energy": 4}), player(production={"energy": 1}))

    pick(game, "Play Energy Tapping")

    assert game.decision["kind"] == "action"
    assert production(game, 1)["energy"] == 0


def test_with_nobody_with_energy_production_energy_tapping_raises_and_lowers_the_players_own():
    game = scenario(player(hand=["energy_tapping"]), player())

    pick(game, "Play Energy Tapping")

    assert production(game, 0)["energy"] == 0
    assert "Player 1 raises their energy Production by 1." in game.log
    assert "Player 1 lowers their own energy Production by 1." in game.log


def test_energy_tapping_is_worth_minus_1_victory_point():
    game = scenario(player(played_cards=["energy_tapping"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-1, 0]

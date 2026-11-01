"""#178 Heat Trappers (6 MegaCredits, building and power Tags): decrease any heat Production 2 steps
and increase your energy Production 1 step. −1 Victory Point."""

from tests.helpers import final_scores, labels, offered, pick, player, production, scenario, terraformed_mars


def test_heat_trappers_lowers_an_opponents_heat_production_2_steps_and_raises_energy_production():
    game = scenario(player(hand=["heat_trappers"]), player(production={"heat": 3}))

    pick(game, "Play Heat Trappers (6 MegaCredits)")

    assert production(game, 0)["energy"] == 1
    assert production(game, 1)["heat"] == 1


def test_heat_trappers_needs_someone_with_2_heat_production():
    assert not offered(scenario(player(hand=["heat_trappers"]), player(production={"heat": 1})), "Play Heat Trappers")


def test_robotic_workforce_copying_heat_trappers_picks_whose_heat_production_to_lower_again():
    game = scenario(
        player(hand=["robotic_workforce"], played_cards=["heat_trappers"]),
        player(production={"heat": 2}),
        player(production={"heat": 2}),
    )

    pick(game, "Play Robotic Workforce")
    assert labels(game) == ["Lower Player 2's heat Production by 2", "Lower Player 3's heat Production by 2"]
    pick(game, "Player 3")

    assert production(game, 0)["energy"] == 1
    assert [production(game, each)["heat"] for each in (1, 2)] == [2, 0]
    assert game.decision["kind"] == "action"


def test_robotic_workforce_cannot_copy_heat_trappers_with_nobody_to_lower_2_heat_production_steps():
    game = scenario(player(hand=["robotic_workforce"], played_cards=["heat_trappers"]), player(production={"heat": 1}))

    assert not offered(game, "Play Robotic Workforce")


def test_heat_trappers_is_worth_minus_1_victory_point():
    game = scenario(player(played_cards=["heat_trappers"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-1, 0]

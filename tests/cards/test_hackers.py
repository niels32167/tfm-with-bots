"""#125 Hackers (3 MegaCredits): decrease your energy Production 1 step and any MegaCredit Production
2 steps. Increase your MegaCredit Production 2 steps. −1 Victory Point."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_hackers_needs_energy_production_to_lower():
    assert not offered(scenario(player(hand=["hackers"]), player()), "Play Hackers")
    assert offered(
        scenario(player(hand=["hackers"], production={"energy": 1}), player()), "Play Hackers (3 MegaCredits)"
    )


def test_hackers_takes_2_megacredit_production_steps_from_an_opponent_down_to_minus_5():
    game = scenario(player(hand=["hackers"], production={"energy": 1}), player(production={"megacredits": -3}))

    pick(game, "Play Hackers")

    assert production(game, 0)["megacredits"] == 2
    assert production(game, 0)["energy"] == 0
    assert production(game, 1)["megacredits"] == -5


def test_with_every_opponent_at_minus_4_megacredit_production_hackers_lowers_the_players_own_after_raising_it():
    # Raising their own MegaCredit Production first is never worse, so even at -5 they can play it.
    game = scenario(
        player(hand=["hackers"], production={"energy": 1, "megacredits": -5}), player(production={"megacredits": -4})
    )

    pick(game, "Play Hackers")

    assert production(game, 0)["megacredits"] == -5
    assert production(game, 1)["megacredits"] == -4
    assert "Player 1 lowers their own MegaCredit Production by 2." in game.log


def test_hackers_is_worth_minus_1_victory_point():
    game = scenario(player(played_cards=["hackers"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-1, 0]

"""#160 Power Supply Consortium (5 MegaCredits, power Tag): requires 2 power Tags. Decrease any
energy Production 1 step and increase your own 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars

TWO_POWER_TAGS = ["lunar_beam", "lightning_harvest"]


def test_power_supply_consortium_requires_2_power_tags():
    one = scenario(
        player(hand=["power_supply_consortium"], played_cards=["lunar_beam"]), player(production={"energy": 1})
    )
    assert not offered(one, "Play Power Supply Consortium")
    two = scenario(
        player(hand=["power_supply_consortium"], played_cards=TWO_POWER_TAGS), player(production={"energy": 1})
    )
    assert offered(two, "Play Power Supply Consortium (5 MegaCredits)")


def test_power_supply_consortium_takes_an_energy_production_step_from_an_opponent():
    game = scenario(
        player(hand=["power_supply_consortium"], played_cards=TWO_POWER_TAGS), player(production={"energy": 2})
    )

    pick(game, "Play Power Supply Consortium")

    assert production(game, 0)["energy"] == 1
    assert production(game, 1)["energy"] == 1


def test_with_nobody_with_energy_production_power_supply_consortium_is_played_raising_and_lowering_the_players_own():
    game = scenario(player(hand=["power_supply_consortium"], played_cards=TWO_POWER_TAGS), player())

    pick(game, "Play Power Supply Consortium")

    assert production(game, 0)["energy"] == 0
    assert "Player 1 lowers their own energy Production by 1." in game.log


def test_power_supply_consortium_has_no_victory_points():
    game = scenario(player(played_cards=["power_supply_consortium"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

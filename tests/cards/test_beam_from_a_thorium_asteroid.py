"""#058 Beam from a Thorium Asteroid (32 MegaCredits, power, space and jovian Tags, 1 Victory
Point): requires a jovian Tag. Increase your heat Production and energy Production 3 steps each."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_beam_from_a_thorium_asteroid_needs_a_jovian_tag_in_play_and_its_own_does_not_count():
    without = scenario(player(hand=["beam_from_a_thorium_asteroid"]), player())
    with_one = scenario(player(hand=["beam_from_a_thorium_asteroid"], played_cards=["io_mining_industries"]), player())

    assert not offered(without, "Play Beam from a Thorium Asteroid")
    assert offered(with_one, "Play Beam from a Thorium Asteroid")


def test_beam_from_a_thorium_asteroid_raises_heat_and_energy_production_by_3_each():
    game = scenario(
        player(megacredits=32, hand=["beam_from_a_thorium_asteroid"], played_cards=["io_mining_industries"]), player()
    )

    pick(game, "Play Beam from a Thorium Asteroid (32 MegaCredits)")

    assert production(game, 0)["heat"] == 3
    assert production(game, 0)["energy"] == 3


def test_beam_from_a_thorium_asteroid_is_worth_1_victory_point():
    game = scenario(player(played_cards=["beam_from_a_thorium_asteroid"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

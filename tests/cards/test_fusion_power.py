"""#132 Fusion Power (14 MegaCredits, building, power and science Tags): requires 2 power Tags.
Increase your energy Production 3 steps."""

from tests.helpers import offered, pick, player, production, scenario


def test_fusion_power_needs_2_power_tags_in_play():
    one = scenario(player(hand=["fusion_power"], played_cards=["power_plant"]), player())
    two = scenario(player(hand=["fusion_power"], played_cards=["power_plant", "windmills"]), player())

    assert not offered(one, "Play Fusion Power")
    assert offered(two, "Play Fusion Power")


def test_power_tags_in_hand_do_not_count_fusion_powers_own_included():
    game = scenario(player(hand=["fusion_power", "power_plant"], played_cards=["windmills"]), player())

    assert not offered(game, "Play Fusion Power")


def test_fusion_power_raises_energy_production_by_3():
    game = scenario(player(hand=["fusion_power"], played_cards=["power_plant", "windmills"]), player())

    pick(game, "Play Fusion Power")

    assert production(game, 0)["energy"] == 3

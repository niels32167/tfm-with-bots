"""#095 Physics Complex (12 MegaCredits, building and science Tags): Action: spend 6 energy to add a
science to this card. 2 Victory Points for each science on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def test_physics_complex_has_no_requirements_and_steel_helps_pay_for_it():
    game = scenario(player(megacredits=2, steel=5, hand=["physics_complex"]), player())

    pick(game, "Play Physics Complex (12 MegaCredits)")

    assert card_resources(game, 0) == {"physics_complex": 0}
    assert resources(game, 0)["steel"] == 0


def test_physics_complex_spends_6_energy_to_add_a_science():
    game = scenario(player(energy=7, played_cards=["physics_complex"]), player())

    pick(game, "Use the action of Physics Complex")

    assert resources(game, 0)["energy"] == 1
    assert card_resources(game, 0) == {"physics_complex": 1}
    assert "Player 1 adds 1 science to Physics Complex." in game.log


def test_physics_complex_action_needs_6_energy():
    game = scenario(player(energy=5, played_cards=["physics_complex"]), player())

    assert not offered(game, "Use the action of Physics Complex")


def test_physics_complex_scores_2_victory_points_per_science():
    for science, points in ((0, 0), (1, 2), (3, 6)):
        holding = player(
            played_cards=["physics_complex"],
            card_resources={"physics_complex": science},
        )
        game = scenario(holding, player(), **terraformed_mars())

        assert final_scores(game)[0]["cards"] == points

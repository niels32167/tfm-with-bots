"""#183 Biomass Combustors (4 MegaCredits, building and power Tags): requires 6 % Oxygen. Decrease
any plant Production 1 step and increase your energy Production 2 steps. −1 Victory Point."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_biomass_combustors_requires_6_percent_oxygen():
    opponent = player(production={"plants": 1})
    assert not offered(scenario(player(hand=["biomass_combustors"]), opponent, oxygen=5), "Play Biomass Combustors")
    assert offered(
        scenario(player(hand=["biomass_combustors"]), opponent, oxygen=6), "Play Biomass Combustors (4 MegaCredits)"
    )


def test_biomass_combustors_lowers_an_opponents_plant_production_and_raises_energy_production_2_steps():
    game = scenario(player(hand=["biomass_combustors"]), player(production={"plants": 2}), oxygen=6)

    pick(game, "Play Biomass Combustors")

    assert production(game, 0)["energy"] == 2
    assert production(game, 1)["plants"] == 1


def test_biomass_combustors_needs_someone_with_plant_production():
    assert not offered(scenario(player(hand=["biomass_combustors"]), player(), oxygen=6), "Play Biomass Combustors")


def test_robotic_workforce_copying_biomass_combustors_lowers_a_plant_production_step_again():
    game = scenario(
        player(hand=["robotic_workforce"], played_cards=["biomass_combustors"]), player(production={"plants": 1})
    )

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["energy"] == 2
    assert production(game, 1)["plants"] == 0


def test_biomass_combustors_is_worth_minus_1_victory_point():
    game = scenario(player(played_cards=["biomass_combustors"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-1, 0]

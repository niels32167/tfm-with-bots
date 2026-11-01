"""#189 Energy Saving (15 MegaCredits, power Tag): increase your energy Production 1 step for each
City Tile in play."""

from tests.helpers import city, final_scores, pick, player, production, scenario, terraformed_mars


def test_energy_saving_raises_energy_production_1_step_for_each_city_in_play_whoever_owns_it():
    cities = [city("A1", owner=0), city("C3", owner=1)]
    game = scenario(player(hand=["energy_saving"]), player(), tiles=cities)

    pick(game, "Play Energy Saving (15 MegaCredits)")

    assert production(game, 0)["energy"] == 2


def test_energy_saving_with_no_city_in_play_changes_no_production():
    game = scenario(player(hand=["energy_saving"]), player())

    pick(game, "Play Energy Saving")

    assert production(game, 0)["energy"] == 0


def test_energy_saving_has_no_victory_points():
    game = scenario(player(played_cards=["energy_saving"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

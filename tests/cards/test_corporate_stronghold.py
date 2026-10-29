"""#182 Corporate Stronghold (Corporate Era, 11 MegaCredits, building and city Tags, −2 Victory
Points): decrease your energy Production 1 step and increase your MegaCredit Production 3 steps.
Place a City Tile."""

from tests.helpers import area, final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_corporate_stronghold_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["corporate_stronghold"]), player()), "Play Corporate Stronghold")


def test_corporate_stronghold_trades_production_and_places_a_city():
    game = scenario(player(megacredits=11, hand=["corporate_stronghold"], production={"energy": 1}), player())

    pick(game, "Play Corporate Stronghold (11 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 3
    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "area"
    pick(game, area="C3")
    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert game.decision["kind"] == "action"


def test_corporate_stronghold_is_worth_minus_2_victory_points():
    game = scenario(player(played_cards=["corporate_stronghold"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-2, 0]

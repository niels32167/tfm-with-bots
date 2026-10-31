"""#200 Immigrant City (13 MegaCredits, building and city Tags): Effect: when a City Tile is placed,
including this, increase your MegaCredit Production 1 step. Decrease your energy Production 1 step
and decrease your MegaCredit Production 2 steps. Place a City Tile."""

from tests.helpers import (
    LAND_AREAS,
    area,
    city,
    final_scores,
    greenery,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)


def test_immigrant_city_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(megacredits=13, hand=["immigrant_city"]), player()), "Play Immigrant City")


def test_immigrant_city_needs_an_area_for_its_city():
    every_free_area_taken = [greenery(name, owner=1) for name in LAND_AREAS]
    holding = player(megacredits=13, hand=["immigrant_city"], production={"energy": 1})

    assert not offered(scenario(holding, player(), tiles=every_free_area_taken), "Play Immigrant City")


def test_immigrant_city_places_its_city_and_counts_it_before_lowering_production():
    game = scenario(player(megacredits=13, hand=["immigrant_city"], production={"energy": 1}), player())

    pick(game, "Play Immigrant City (13 MegaCredits)")
    assert production(game, 0) == {**production(game, 0), "energy": 1, "megacredits": 0}
    pick(game, "Place the City on C3")

    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == -1
    log = game.log
    assert log.index("Player 1's Immigrant City takes effect.") < log.index(
        "Player 1 lowers their MegaCredit Production by 2."
    )


def test_immigrant_city_can_be_played_at_minus_4_megacredit_production_thanks_to_its_own_city():
    holding = player(megacredits=13, hand=["immigrant_city"], production={"energy": 1, "megacredits": -4})
    game = scenario(holding, player())

    pick(game, "Play Immigrant City")
    pick(game, "Place the City on C3")

    assert production(game, 0)["megacredits"] == -5
    at_the_limit = player(megacredits=13, hand=["immigrant_city"], production={"energy": 1, "megacredits": -5})
    assert not offered(scenario(at_the_limit, player()), "Play Immigrant City")


def test_with_immigrant_city_any_players_city_raises_its_players_megacredit_production_1_step():
    game = scenario(player(megacredits=50), player(played_cards=["immigrant_city"]))

    pick(game, "City (25 MegaCredits)")
    pick(game, "Place the City on C3")
    pick(game, "City (25 MegaCredits)")
    pick(game, "Place the City on J1")

    assert production(game, 1)["megacredits"] == 2
    assert production(game, 0)["megacredits"] == 2  # the City Standard Project's own


def test_robotic_workforce_copies_only_immigrant_citys_production_box():
    holding = player(
        megacredits=9,
        hand=["robotic_workforce"],
        played_cards=["immigrant_city"],
        production={"energy": 1, "megacredits": 2},
    )
    game = scenario(holding, player(), tiles=[city("C3", owner=0)])

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 0


def test_immigrant_city_is_worth_no_victory_points():
    game = scenario(player(played_cards=["immigrant_city"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

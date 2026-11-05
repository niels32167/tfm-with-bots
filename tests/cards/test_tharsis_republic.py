"""Tharsis Republic (building Tag): Effect: when any City Tile is placed ON MARS, increase your
MegaCredit Production 1 step. When you place a City Tile, gain 3 MegaCredits. You start with 40
MegaCredits. As your first action in the game, place a City Tile."""

from tests.helpers import (
    LAND_AREAS,
    areas_offered,
    greenery,
    hand,
    labels,
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_tharsis_republic_starts_with_40_megacredits_a_building_tag_and_no_tile_yet():
    game, first = start_as("tharsis_republic")

    assert resources(game, first) == {
        "megacredits": 40,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert set(production(game, first).values()) == {0}
    assert player_board(game, first)["tags"]["building"] == 1
    assert hand(game, first) == []


def test_its_first_action_places_a_city_which_sets_off_both_its_effects():
    game, first = start_as("tharsis_republic")

    assert labels(game) == ["First action of Tharsis Republic: place a City", "Pass"]
    pick(game, "First action")
    assert game.decision["kind"] == "area"
    assert "C3" in areas_offered(game)
    pick(game, type="area", area="C3")

    assert resources(game, first)["megacredits"] == 43
    assert production(game, first)["megacredits"] == 1
    assert game.full_view()["actions_this_turn"] == 1
    assert player_board(game, first)["first_action_due"] is False


def test_a_city_it_places_itself_gains_3_megacredits_and_1_step():
    game = scenario(player(corporation="tharsis_republic", megacredits=25), player())

    pick(game, "City (25 MegaCredits)")
    pick(game, type="area", area="C3")

    assert resources(game, 0)["megacredits"] == 3
    assert (
        production(game, 0)["megacredits"] == 2
    )  # 1 from the Standard Project, 1 from Tharsis Republic


def test_another_players_city_on_mars_raises_production_but_gains_no_megacredits():
    game = scenario(player(), player(corporation="tharsis_republic"))

    pick(game, "City (25 MegaCredits)")
    pick(game, type="area", area="C3")

    assert production(game, 1)["megacredits"] == 1
    assert resources(game, 1)["megacredits"] == 42


def test_its_own_city_off_mars_gains_3_megacredits_and_raises_no_production():
    game = scenario(
        player(
            corporation="tharsis_republic",
            megacredits=0,
            titanium=9,
            hand=["phobos_space_haven"],
        ),
        player(),
    )

    pick(game, "Play Phobos Space Haven")
    pick(game, type="area", area="phobos_space_haven")

    assert resources(game, 0)["megacredits"] == 3
    assert production(game, 0)["megacredits"] == 0


def test_another_players_city_off_mars_changes_nothing():
    game = scenario(
        player(megacredits=25, hand=["phobos_space_haven"]),
        player(corporation="tharsis_republic"),
    )

    pick(game, "Play Phobos Space Haven")
    pick(game, type="area", area="phobos_space_haven")

    assert production(game, 1)["megacredits"] == 0
    assert resources(game, 1)["megacredits"] == 42


def test_a_greenery_changes_nothing():
    game = scenario(player(corporation="tharsis_republic", megacredits=23), player())

    pick(game, "Greenery (23 MegaCredits)")
    pick(game, type="area", area="C3")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["megacredits"] == 0


def test_immigrant_city_may_be_played_at_minus_5_as_tharsis_republic_raises_production_for_its_city_too():
    at_the_limit = player(corporation="tharsis_republic", hand=["immigrant_city"], production={"megacredits": -5, "energy": 1})
    game = scenario(at_the_limit, player())

    pick(game, "Play Immigrant City")
    pick(game, type="area", area="C3")

    assert production(game, 0)["megacredits"] == -5
    assert production(game, 0)["energy"] == 0


def test_robotic_workforce_may_not_copy_production_from_its_effect():
    game = scenario(
        player(corporation="tharsis_republic", hand=["robotic_workforce"]), player()
    )

    assert not offered(game, "Play Robotic Workforce")


def test_without_an_area_for_its_city_the_first_action_is_not_offered_and_nothing_else_waits_on_it():
    every_land = [greenery(area, owner=1) for area in LAND_AREAS]
    game = scenario(
        player(corporation="tharsis_republic", first_action_due=True),
        player(),
        tiles=every_land,
    )

    assert not offered(game, "First action")
    assert offered(game, "Pass")

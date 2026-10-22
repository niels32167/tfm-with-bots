"""Ocean Tiles: the Aquifer Standard Project, the Areas reserved for Oceans, and the limit of 9."""

from tests.helpers import OCEAN_AREAS, area, areas_offered, ocean, options, pick, player, player_board, scenario


def test_aquifer_costs_18_megacredits_and_places_an_ocean_for_one_terraform_rating():
    game = scenario(player(megacredits=20, terraform_rating=20), player())

    pick(game, project="aquifer")
    pick(game, area="A5")  # no placement bonus, and no Ocean next to it

    assert area(game, "A5")["tile"] == {"type": "ocean", "owner": None}
    assert game.player_view(0)["oceans"] == 1
    assert player_board(game, 0)["megacredits"] == 2
    assert player_board(game, 0)["terraform_rating"] == 21


def test_the_player_chooses_among_the_areas_reserved_for_oceans():
    game = scenario(player(megacredits=20), player())

    pick(game, project="aquifer")

    decision = game.decision
    assert decision["kind"] == "area"
    assert decision["player"] == 0
    assert areas_offered(game) == OCEAN_AREAS
    assert options(game)[0] == {
        "index": 0,
        "label": "Place the Ocean on A2",
        "details": {"type": "area", "area": "A2", "tile": "ocean"},
    }


def test_an_ocean_goes_only_on_an_empty_area_reserved_for_oceans():
    game = scenario(player(megacredits=20), player(), tiles=[ocean("A2"), ocean("E5")])

    pick(game, project="aquifer")

    assert areas_offered(game) == ["A4", "A5", "B6", "D8", "E4", "E6", "F6", "F7", "F8", "J5"]


def test_once_9_oceans_are_placed_aquifer_costs_18_megacredits_and_does_nothing_else():
    # Rulebook: you may still take Actions that raise a maxed Global Parameter,
    # ignoring that part of the effect (docs/rules-notes.md).
    nine_oceans = [ocean(name) for name in OCEAN_AREAS[:9]]
    game = scenario(player(megacredits=20, terraform_rating=30), player(), tiles=nine_oceans)

    pick(game, project="aquifer")

    assert game.player_view(0)["oceans"] == 9
    assert player_board(game, 0)["megacredits"] == 2
    assert player_board(game, 0)["terraform_rating"] == 30
    assert game.decision["kind"] == "action"
    assert game.log[-1] == "All 9 Oceans are already placed, so no Ocean is placed."


def test_placing_the_9th_ocean_leaves_no_ocean_for_the_next_aquifer():
    eight_oceans = [ocean(name) for name in OCEAN_AREAS[:8]]
    game = scenario(player(megacredits=36, terraform_rating=20), player(), tiles=eight_oceans)

    pick(game, project="aquifer")
    pick(game, area="F8")
    pick(game, project="aquifer")

    assert game.player_view(0)["oceans"] == 9
    assert area(game, "J5")["tile"] is None
    assert player_board(game, 0)["terraform_rating"] == 21
    assert game.log[-1] == "All 9 Oceans are already placed, so no Ocean is placed."


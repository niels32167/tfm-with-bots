"""#P14 Great Aquifer (Prelude Card): place 2 Ocean Tiles."""

from tests.helpers import OCEAN_AREAS, area, ocean, pick, player, player_board, scenario


def test_great_aquifer_places_2_oceans():
    game = scenario(player(prelude_cards=["great_aquifer"]), player(), prelude=True)

    pick(game, area="F6")
    pick(game, area="F7")

    assert area(game, "F6")["tile"]["type"] == area(game, "F7")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 22
    assert game.decision["kind"] == "action"


def test_with_9_oceans_placed_it_is_played_and_places_none():
    tiles = [ocean(name) for name in OCEAN_AREAS[:9]]
    game = scenario(player(prelude_cards=["great_aquifer"]), player(), prelude=True, tiles=tiles)

    assert player_board(game, 0)["played_prelude_cards"] == ["great_aquifer"]
    assert player_board(game, 0)["terraform_rating"] == 20
    assert game.decision["kind"] == "action"

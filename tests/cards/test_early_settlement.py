"""#P09 Early Settlement (Prelude Card, building and city Tags): increase your plant Production 1 step.
Place a City Tile."""

from tests.helpers import (
    area,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
)


def test_early_settlement_raises_plant_production_and_places_a_city():
    game = scenario(player(prelude_cards=["early_settlement"]), player(), prelude=True)

    assert production(game, 0)["plants"] == 1
    assert game.decision["kind"] == "area"
    pick(game, area="C3")

    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert player_board(game, 0)["tags"]["city"] == 1
    assert game.decision["kind"] == "action"


def test_its_city_sets_off_the_corporations_triggers():
    game = scenario(player(prelude_cards=["early_settlement"], corporation="tharsis_republic"), player(), prelude=True)

    pick(game, area="C3")

    assert production(game, 0)["megacredits"] == 1
    assert resources(game, 0)["megacredits"] == 45

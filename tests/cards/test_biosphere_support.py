"""#P05 Biosphere Support (Prelude Card, plant Tag): increase your plant Production 2 steps. Decrease
your MegaCredit Production 1 step."""

from tests.helpers import player, player_board, production, resources, scenario


def test_biosphere_support_raises_plant_production_by_2_and_lowers_megacredit_production_by_1():
    game = scenario(player(prelude_cards=["biosphere_support"]), player(), prelude=True)

    assert (production(game, 0)["plants"], production(game, 0)["megacredits"]) == (2, -1)
    assert player_board(game, 0)["tags"]["plant"] == 1


def test_with_megacredit_production_at_minus_5_it_cant_be_played_and_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["biosphere_support"], production={"megacredits": -5}), player(), prelude=True)

    assert production(game, 0) == {**production(game, 0), "plants": 0, "megacredits": -5}
    assert resources(game, 0)["megacredits"] == 57
    assert player_board(game, 0)["played_prelude_cards"] == []

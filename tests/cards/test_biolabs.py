"""#P04 Biolabs (Prelude Card, science Tag): increase your plant Production 1 step. Draw 3 cards."""

from tests.helpers import hand, player, player_board, production, scenario


def test_biolabs_raises_plant_production_and_draws_3_cards():
    game = scenario(player(prelude_cards=["biolabs"]), player(), prelude=True, deck=["mine", "trees", "comet", "ants"])

    assert production(game, 0)["plants"] == 1
    assert hand(game, 0) == ["comet", "mine", "trees"]
    assert player_board(game, 0)["tags"]["science"] == 1
    assert "Player 1 draws 3 cards." in game.log

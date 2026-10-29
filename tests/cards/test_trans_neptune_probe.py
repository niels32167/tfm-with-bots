"""#084 Trans-Neptune Probe (Corporate Era, 6 MegaCredits, space and science Tags, 1 Victory
Point): no effect."""

from tests.helpers import final_scores, pick, played_cards, player, player_board, resources, scenario, terraformed_mars


def test_trans_neptune_probe_is_played_for_its_tags_and_does_nothing_else():
    game = scenario(player(megacredits=6, hand=["trans_neptune_probe"]), player())

    pick(game, "Play Trans-Neptune Probe (6 MegaCredits)")

    assert played_cards(game, 0) == ["trans_neptune_probe"]
    assert resources(game, 0)["megacredits"] == 0
    tags = player_board(game, 0)["tags"]
    assert (tags["space"], tags["science"]) == (1, 1)
    assert game.decision["kind"] == "action"


def test_trans_neptune_probe_is_worth_1_victory_point():
    game = scenario(player(played_cards=["trans_neptune_probe"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]

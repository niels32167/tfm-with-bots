"""#063 Mining Expedition (12 MegaCredits, Event Tag): raise Oxygen 1 step. Remove 2 plants from
any Player. Gain 2 steel."""

from tests.helpers import final_scores, labels, pick, player, player_board, resources, scenario, terraformed_mars


def test_mining_expedition_raises_oxygen_gains_2_steel_and_removes_2_plants():
    game = scenario(player(megacredits=12, hand=["mining_expedition"]), player(plants=3))

    pick(game, "Play Mining Expedition (12 MegaCredits)")
    pick(game, "Remove 2 plants from Player 2")

    assert game.player_view(0)["oxygen"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["steel"] == 2
    assert resources(game, 1)["plants"] == 1


def test_mining_expeditions_removal_is_up_to_2_plants_and_may_be_left_undone_as_any_red_bordered_one():
    game = scenario(player(megacredits=12, hand=["mining_expedition"]), player(plants=1))

    pick(game, "Play Mining Expedition")

    assert labels(game) == ["Remove 1 plant from Player 2", "Remove nothing"]


def test_mining_expedition_has_no_victory_points():
    game = scenario(player(played_cards=["mining_expedition"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

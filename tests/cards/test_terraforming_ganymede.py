"""#197 Terraforming Ganymede (Corporate Era, 33 MegaCredits, space and jovian Tags, 2 Victory
Points): raise your Terraform Rating 1 step for each jovian Tag you have, including this."""

from tests.helpers import final_scores, pick, player, player_board, resources, scenario, terraformed_mars


def test_terraforming_ganymede_raises_terraform_rating_by_1_for_each_jovian_tag_including_its_own():
    # Methane From Titan and Colonizer Training Camp have a jovian Tag each.
    played = ["methane_from_titan", "colonizer_training_camp"]
    game = scenario(player(megacredits=33, hand=["terraforming_ganymede"], played_cards=played), player())

    pick(game, "Play Terraforming Ganymede (33 MegaCredits)")

    assert player_board(game, 0)["terraform_rating"] == 23
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their Terraform Rating by 3." in game.log
    assert game.decision["kind"] == "action"


def test_terraforming_ganymede_with_only_its_own_jovian_tag_raises_terraform_rating_by_1():
    game = scenario(player(hand=["terraforming_ganymede"]), player())

    pick(game, "Play Terraforming Ganymede")

    assert player_board(game, 0)["terraform_rating"] == 21


def test_terraforming_ganymede_is_worth_2_victory_points():
    game = scenario(player(played_cards=["terraforming_ganymede"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]

"""#036 Release of Inert Gases (14 MegaCredits, Event Tag): raise your Terraform Rating 2 steps."""

from tests.helpers import final_scores, pick, played_cards, player, player_board, resources, scenario, terraformed_mars


def test_release_of_inert_gases_raises_terraform_rating_by_2():
    game = scenario(player(megacredits=14, hand=["release_of_inert_gases"]), player())

    pick(game, "Play Release of Inert Gases (14 MegaCredits)")

    assert player_board(game, 0)["terraform_rating"] == 22
    assert resources(game, 0)["megacredits"] == 0
    assert played_cards(game, 0) == ["release_of_inert_gases"]
    assert "Player 1 raises their Terraform Rating by 2." in game.log
    assert game.decision["kind"] == "action"


def test_release_of_inert_gases_has_no_requirements_and_no_victory_points():
    game = scenario(player(played_cards=["release_of_inert_gases"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]

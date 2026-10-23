"""Final scoring: Terraform Rating, 5 Victory Points per Milestone, the Awards, 1 per
Greenery, 1 per Greenery next to each City whoever owns it, and the Victory Points on
played cards. The most Victory Points wins; MegaCredits break a tie."""

from tests.helpers import (
    city,
    claimed,
    end_the_generation,
    final_scores,
    funded,
    greenery,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_the_final_score_breakdown_adds_up_to_the_total():
    game = scenario(
        player(terraform_rating=30),
        player(terraform_rating=25),
        milestones=[claimed("mayor", by=0)],
        awards=[funded("landlord", by=0)],
        **terraformed_mars(
            tiles=[city("C3", 0), greenery("C4", 0), greenery("D3", 1), city("J1", 1), greenery("J2", 1)]
        ),
    )

    end_the_generation(game)

    assert game.scores == [
        {
            "player": 0,
            "terraform_rating": 30,
            "milestones": 5,
            "awards": 0,
            "greeneries": 1,
            "cities": 2,  # C3 is next to the Greeneries on C4 and D3
            "cards": 0,
            "total": 38,
            "megacredits": 72,
            "rank": 1,
        },
        {
            "player": 1,
            "terraform_rating": 25,
            "milestones": 0,
            "awards": 5,  # Landlord: 3 Tiles against 2
            "greeneries": 2,
            "cities": 1,  # J1 is next to the Greenery on J2
            "cards": 0,
            "total": 33,
            "megacredits": 67,
            "rank": 2,
        },
    ]


def test_each_claimed_milestone_is_worth_5_victory_points():
    game = scenario(
        player(), player(), milestones=[claimed("terraformer", by=0), claimed("mayor", by=0)], **terraformed_mars()
    )

    assert [score["milestones"] for score in final_scores(game)] == [10, 0]


def test_a_city_scores_1_for_each_adjacent_greenery_whoever_owns_it():
    # C3's neighbours are B2, B3, C2, C4, D3 and D4; A1 is not one of them.
    tiles = [city("C3", 1), greenery("B2", 0), greenery("B3", 1), greenery("D4", 0), greenery("A1", 0)]
    game = scenario(player(), player(), **terraformed_mars(tiles=tiles))

    scores = final_scores(game)

    assert [score["cities"] for score in scores] == [0, 3]
    assert [score["greeneries"] for score in scores] == [3, 1]


def test_greeneries_from_the_final_conversion_score_and_count_for_landlord():
    game = scenario(player(plants=8), player(), awards=[funded("landlord", by=1)], **terraformed_mars())
    end_the_generation(game)

    pick(game, "Convert")
    pick(game, area="C3")  # with no plants left, Player 1 is done

    assert game.is_over
    assert game.scores[0]["greeneries"] == 1
    assert game.scores[0]["awards"] == 5


def test_the_player_with_the_most_victory_points_wins():
    game = scenario(
        player(terraform_rating=28), player(terraform_rating=31), player(terraform_rating=25), **terraformed_mars()
    )

    scores = final_scores(game)

    assert [score["rank"] for score in scores] == [2, 1, 3]
    assert game.log[-1] == "Player 2 wins."


def test_on_equal_victory_points_the_player_with_more_megacredits_ranks_higher():
    game = scenario(
        player(terraform_rating=30, megacredits=0), player(terraform_rating=30, megacredits=5), **terraformed_mars()
    )

    scores = final_scores(game)

    assert [score["megacredits"] for score in scores] == [30, 35]  # after the final Production phase
    assert [score["rank"] for score in scores] == [2, 1]
    assert game.log[-1] == "Player 2 wins: tied on Victory Points, but with the most MegaCredits."


def test_players_tied_on_victory_points_and_megacredits_share_a_rank():
    game = scenario(player(terraform_rating=30), player(terraform_rating=30), player(), **terraformed_mars())

    scores = final_scores(game)

    assert [score["rank"] for score in scores] == [1, 1, 3]
    assert game.log[-2:] == [
        "Player 1 shares the win, tied on both Victory Points and MegaCredits.",
        "Player 2 shares the win, tied on both Victory Points and MegaCredits.",
    ]

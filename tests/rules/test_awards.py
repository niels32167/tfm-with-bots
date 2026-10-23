"""Awards: any Player may fund one as an Action, for 8 MegaCredits for the first Award
funded, 14 for the second and 20 for the third. Each is funded once, and only three per Game."""

from tests.helpers import (
    award,
    city,
    end_the_generation,
    funded,
    greenery,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_a_player_may_fund_an_award_for_8_megacredits_without_meeting_anything():
    game = scenario(player(megacredits=10), player())

    pick(game, "Fund the Landlord Award")

    assert resources(game, 0)["megacredits"] == 2
    assert award(game, "landlord")["funded_by"] == 0
    assert "Player 1 funds the Landlord Award for 8 MegaCredits." in game.log
    assert player_board(game, 0)["terraform_rating"] == 20


def test_the_second_award_funded_costs_14_megacredits_and_the_third_20():
    game = scenario(player(megacredits=50), player(megacredits=50), awards=[funded("miner", by=1)])
    assert game.player_view(0)["award_cost"] == 14

    pick(game, "Fund the Banker Award (14 MegaCredits)")
    assert resources(game, 0)["megacredits"] == 36
    assert game.player_view(0)["award_cost"] == 20

    pick(game, "Fund the Thermalist Award (20 MegaCredits)")
    assert resources(game, 0)["megacredits"] == 16
    assert "Player 1 funds the Thermalist Award for 20 MegaCredits." in game.log


def test_each_award_can_be_funded_only_once():
    game = scenario(player(), player(), awards=[funded("landlord", by=1)])

    assert not offered(game, "Fund the Landlord Award")
    assert offered(game, "Fund the Banker Award")
    assert award(game, "landlord")["funded_by"] == 1


def test_only_three_awards_can_be_funded_per_game():
    three_funded = [funded("landlord", by=0), funded("banker", by=1), funded("miner", by=0)]
    game = scenario(player(megacredits=100), player(), awards=three_funded)

    assert not offered(game, "Fund the")
    assert game.player_view(0)["award_cost"] is None


def test_an_award_is_not_offered_without_its_price():
    game = scenario(player(megacredits=13), player(), awards=[funded("miner", by=1)])

    assert not offered(game, "Fund the")


def test_funding_an_award_is_one_of_the_two_actions_of_a_turn():
    game = scenario(player(), player())

    pick(game, "Fund the Miner Award")

    assert game.decision["player"] == 0
    assert offered(game, "End Turn")


def test_a_fund_option_names_the_award_and_its_price():
    game = scenario(player(), player(), awards=[funded("miner", by=1)])

    found = [option for option in game.decision["options"] if option["details"]["type"] == "fund_award"]

    assert [(option["label"], option["details"]) for option in found] == [
        ("Fund the Landlord Award (14 MegaCredits)", {"type": "fund_award", "award": "landlord", "cost": 14}),
        ("Fund the Banker Award (14 MegaCredits)", {"type": "fund_award", "award": "banker", "cost": 14}),
        ("Fund the Scientist Award (14 MegaCredits)", {"type": "fund_award", "award": "scientist", "cost": 14}),
        ("Fund the Thermalist Award (14 MegaCredits)", {"type": "fund_award", "award": "thermalist", "cost": 14}),
    ]


def test_everyone_sees_each_award_with_its_condition_and_what_each_player_has_of_it():
    game = scenario(
        player(heat=5, steel=2, titanium=1, production={"megacredits": -2}),
        player(heat=9, production={"megacredits": 3}),
        tiles=[city("C3", owner=1), greenery("J1", owner=1)],
    )

    awards = game.player_view(1)["awards"]

    assert [(entry["name"], entry["condition"], entry["counts"]) for entry in awards] == [
        ("Landlord", "Owning the most Tiles in play", [0, 2]),
        ("Banker", "Having the highest MegaCredit Production", [-2, 3]),
        ("Scientist", "Having the most science Tags in play", [0, 0]),
        ("Thermalist", "Having the most heat", [5, 9]),
        ("Miner", "Having the most steel and titanium", [3, 0]),
    ]
    assert all(entry["funded_by"] is None for entry in awards)
    assert game.player_view(1)["award_cost"] == 8


# Scoring. A funded Award gives 5 Victory Points to whoever has the most of what it measures
# and 2 to the runner-up, whoever funded it.


def award_points(game):
    """Each Player's Victory Points from Awards, after the last Generation ends."""
    end_the_generation(game)
    return [score["awards"] for score in game.scores]


def test_an_award_nobody_funded_scores_nothing():
    game = scenario(player(heat=9), player(), **terraformed_mars())

    assert award_points(game) == [0, 0]


def test_landlord_goes_to_whoever_owns_the_most_tiles_and_oceans_belong_to_nobody():
    tiles = [city("C3", 0), greenery("C4", 0), greenery("J1", 1)]
    game = scenario(player(), player(), player(), awards=[funded("landlord", by=2)], **terraformed_mars(tiles=tiles))

    assert award_points(game) == [5, 2, 0]


def test_banker_goes_to_the_highest_megacredit_production_even_below_zero():
    game = scenario(
        player(production={"megacredits": -2}),
        player(production={"megacredits": -5}),
        player(production={"megacredits": -3}),
        awards=[funded("banker", by=1)],
        **terraformed_mars(),
    )

    assert award_points(game) == [5, 0, 2]


def test_thermalist_counts_heat_after_the_final_production_phase():
    game = scenario(
        player(heat=3),
        player(energy=4),  # turns into 4 heat
        player(heat=1, production={"heat": 1}),
        awards=[funded("thermalist", by=0)],
        **terraformed_mars(),
    )

    assert award_points(game) == [2, 5, 0]


def test_miner_counts_steel_and_titanium_together():
    game = scenario(
        player(steel=3),
        player(steel=2, titanium=2),
        player(titanium=3),
        awards=[funded("miner", by=0)],
        **terraformed_mars(),
    )

    assert award_points(game) == [2, 5, 2]  # Players 1 and 3 tie for second place


def test_players_tied_for_first_place_all_get_5_and_nobody_gets_second_place():
    game = scenario(
        player(steel=4), player(titanium=4), player(steel=1), awards=[funded("miner", by=2)], **terraformed_mars()
    )

    assert award_points(game) == [5, 5, 0]


def test_in_a_2_player_game_the_runner_up_gets_nothing():
    game = scenario(player(heat=5), player(heat=2), awards=[funded("thermalist", by=1)], **terraformed_mars())

    assert award_points(game) == [5, 0]


def test_a_count_of_0_can_win_an_award_or_take_second_place():
    nobody_has_heat = scenario(player(), player(), player(), awards=[funded("thermalist", by=0)], **terraformed_mars())
    assert award_points(nobody_has_heat) == [5, 5, 5]

    one_has_heat = scenario(
        player(heat=3), player(), player(), awards=[funded("thermalist", by=1)], **terraformed_mars()
    )
    assert award_points(one_has_heat) == [5, 2, 2]


def test_scientist_counts_science_tags_in_play_and_none_on_played_events():
    # Development Center (Active) and Search for Life (Active) have a science Tag each,
    # Inventors' Guild (Active) one, and the Events Technology Demonstration and Special Design
    # one each, which no longer count once played.
    game = scenario(
        player(played_cards=["development_center", "search_for_life"]),
        player(played_cards=["inventors_guild", "technology_demonstration", "special_design"]),
        player(),
        awards=[funded("scientist", by=0)],
        **terraformed_mars(),
    )

    assert award(game, "scientist")["counts"] == [2, 1, 0]
    assert award_points(game) == [5, 2, 0]


def test_the_log_says_who_takes_each_place():
    tiles = [city("C3", 0), greenery("C4", 0), greenery("J1", 1)]
    game = scenario(
        player(steel=4),
        player(titanium=4),
        player(),
        awards=[funded("miner", by=2), funded("landlord", by=2)],
        **terraformed_mars(tiles=tiles),
    )

    end_the_generation(game)

    game_over = game.log.index("The Game is over.")
    assert game.log[game_over + 1 : game_over + 5] == [
        "Player 1 takes first place in the Landlord Award (2 Tiles) and gains 5 Victory Points.",
        "Player 2 takes second place in the Landlord Award (1 Tile) and gains 2 Victory Points.",
        "Player 1 shares first place in the Miner Award (4 steel and titanium) and gains 5 Victory Points.",
        "Player 2 shares first place in the Miner Award (4 steel and titanium) and gains 5 Victory Points.",
    ]

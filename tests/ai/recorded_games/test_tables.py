"""Tables computed from the dataset, to compare with the spec's counts and with tfmstats.com's tables."""

from ai.recorded_games.importer import import_game
from ai.recorded_games.tables import claims_table, corporation_table, keep_rates, prelude_table, spec_counts
from tests.ai.recorded_games.logs import ADA, BO, SALT, prelude_log


def two_games():
    first = import_game(prelude_log(), SALT)
    log = prelude_log()
    log["table_id"] = "9"
    log["winner"] = "Bo"
    log["players"][ADA]["elo_data"]["position"], log["players"][BO]["elo_data"]["position"] = 2, 1
    log["conceded"] = True
    log["players"][BO]["elo_data"]["game_rank"] = 300
    return [first, import_game(log, SALT)]


def test_starting_hand_keep_rates_count_each_card_offered_at_setup_and_kept():
    rates = keep_rates(two_games())

    assert rates["business_contacts"] == (2, 2)  # Ada keeps it in both Games
    assert rates["hackers"] == (2, 0)
    assert rates["methane_from_titan"] == (2, 2)
    assert "teractor" not in rates and "excentric_sponsor" not in rates


def test_corporations_and_prelude_cards_count_times_chosen_and_won():
    games = two_games()

    assert corporation_table(games)["teractor"] == {"offered": 2, "chosen": 2, "won": 1}
    assert corporation_table(games)["mining_guild"] == {"offered": 2, "chosen": 0, "won": 0}
    assert prelude_table(games)["galilean_mining"] == {"offered": 2, "chosen": 2, "won": 1}


def test_milestones_and_awards_count_claims_and_their_mean_generation():
    table = claims_table(two_games(), "milestones", "milestone")

    assert table == {"planner": {"claimed": 2, "mean_generation": 2.0, "won": 1}}


def test_spec_counts_split_games_by_prelude_concession_and_rating():
    counts = spec_counts(two_games())["Prelude"]

    assert (counts["games"], counts["not_conceded"]) == (2, 1)
    assert counts["not_conceded_both_500"] == 1  # 612 and 540
    assert counts["not_conceded_both_600"] == 0
    assert counts["mean_generations"] == 2.0
    assert counts["mean_points"] == (61.0, 48.0)  # winner, loser
    assert counts["mean_winner_card_points"] == 3.0
    assert counts["mean_higher_card_points"] == 3.0  # the higher of the two, as the spec counts it

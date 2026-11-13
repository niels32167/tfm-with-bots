"""The known traits of Recorded Games' logs (the spec's "Recorded Games"), each on a hand-written log."""

import pytest

from ai.recorded_games.importer import Skipped, choose_perspective, import_game
from tests.ai.recorded_games.logs import ADA, BO, SALT, decisions, keeps, move, prelude_log


def moves_by_number(log):
    return {entry["move_number"]: entry for entry in log["moves"]}


def test_a_player_who_cancels_and_keeps_again_bought_what_they_kept_last():
    log = prelude_log()
    state = log["moves"][-1]["game_state"]
    at = next(i for i, entry in enumerate(log["moves"]) if entry["move_number"] == 20) + 1
    log["moves"][at:at] = [
        move(20, BO, "other", "Bo cancels their move", state),
        move(20, BO, "buy_card", keeps("Bo", ["Olympus Conference"]), state, cards_kept={BO: ["Olympus Conference"]}),
    ]

    [bo_buy] = decisions(import_game(log, SALT), "buy", 1)
    assert bo_buy["picked"] == ["olympus_conference"]


def test_a_draft_pick_credited_to_the_wrong_player_is_given_to_who_held_the_card():
    log = prelude_log()
    moves_by_number(log)[12]["player_id"] = ADA  # "Bo drafts Industrial Microbes", credited to Ada

    game = import_game(log, SALT)
    assert [d["picked"] for d in decisions(game, "draft", 1)] == [
        "industrial_microbes", "olympus_conference", "big_asteroid",
    ]  # fmt: skip
    assert len(decisions(game, "draft", 0)) == 3


def test_a_played_card_credited_to_the_wrong_player_is_given_to_who_the_description_names():
    log = prelude_log()
    moves_by_number(log)[5]["player_id"] = ADA  # "Bo plays card Galilean Mining", credited to Ada

    game = import_game(log, SALT)
    [ada_buy] = decisions(game, "buy", 0)
    ada, bo = game["positions"][ada_buy["position"]]["players"]
    assert (ada["prelude_cards"], bo["prelude_cards"]) == (["excentric_sponsor"], ["galilean_mining"])


def test_untranslated_and_differently_spelled_names_are_mapped():
    log = prelude_log()
    dealt = log["players"][ADA]["starting_hand"]
    dealt["preludes"][0] = "card_prelude_P34"
    dealt["project_cards"][2] = "Allied Bank"

    [ada_setup] = decisions(import_game(log, SALT), "setup", 0)
    assert ada_setup["offer"]["prelude_cards"][0] == "unmi_contractor"


def test_a_game_naming_cards_outside_the_catalog_is_skipped_and_the_names_listed():
    log = prelude_log()
    log["players"][BO]["starting_hand"]["project_cards"][0] = "Venus Governor"
    log["moves"][-1]["game_state"]["awards"] = {"Podróżnik": {"funded_by": "Bo", "player_id": BO, "move_number": 22}}
    log["moves"][-2]["game_state"]["awards"] = log["moves"][-1]["game_state"]["awards"]

    with pytest.raises(Skipped) as skipped:
        import_game(log, SALT)
    assert skipped.value.reason == "unknown names"
    assert "Venus Governor" in skipped.value.names


@pytest.mark.parametrize("date", ["0001-01-01", "1-01-01", None, "2025-13-01"])
def test_invalid_dates_are_unknown(date):
    log = prelude_log()
    log["game_date"] = date

    assert import_game(log, SALT)["date"] is None


def test_an_old_log_without_dealt_cards_or_offers_keeps_its_settings_and_results_only():
    log = prelude_log()
    for player in log["players"].values():
        player["starting_hand"] = None
    for entry in log["moves"]:
        entry["card_options"] = None
        entry["cards_kept"] = None
        if entry["action_type"] == "draft":
            entry["action_type"] = "draft_card"
            entry["card_drafted"] = None
            entry["reason"] = None
    log["metadata"]["scraper_version"] = "2025july30"

    game = import_game(log, SALT)
    assert game["decisions"] == []
    assert [player["victory_points"] for player in game["players"]] == [61, 48]


def bare(log):
    """The same Game as an older scraper saw it: no dealt cards, offers or keeps."""
    for player in log["players"].values():
        player["starting_hand"] = None
    for entry in log["moves"]:
        entry["card_options"] = None
        entry["cards_kept"] = None
    log["metadata"]["scraper_version"] = None
    return log


def test_of_several_perspectives_of_one_game_the_most_complete_is_kept():
    complete = prelude_log()
    complete["player_perspective"] = BO
    one_hand = prelude_log()
    one_hand["players"][BO]["starting_hand"] = None

    assert choose_perspective([bare(prelude_log()), complete, one_hand]) is complete
    assert choose_perspective([one_hand, bare(prelude_log())]) is one_hand


def test_of_equally_complete_perspectives_the_choice_does_not_depend_on_their_order():
    ada_s, bo_s = prelude_log(), prelude_log()
    bo_s["player_perspective"] = BO

    assert choose_perspective([ada_s, bo_s]) is choose_perspective([bo_s, ada_s])


def test_the_last_card_of_a_draft_comes_by_itself_without_a_move_of_its_own():
    log = prelude_log()
    log["moves"] = [entry for entry in log["moves"] if entry["move_number"] not in (17, 18)]

    game = import_game(log, SALT)
    [ada_buy] = decisions(game, "buy", 0)
    assert ada_buy["offer"] == ["kelp_farming", "deimos_down", "standard_technology", "tundra_farming"]
    assert len(decisions(game, "draft", 0)) == 3


def test_eccentric_sponsor_is_excentric_sponsor():
    log = prelude_log()
    dealt = log["players"][ADA]["starting_hand"]["preludes"]
    dealt[dealt.index("Excentric Sponsor")] = "Eccentric Sponsor"

    [ada_setup] = decisions(import_game(log, SALT), "setup", 0)
    assert ada_setup["offer"]["prelude_cards"][1] == "excentric_sponsor"


def test_a_corporation_recorded_as_unknown_is_the_one_kept_at_setup():
    log = prelude_log()
    log["players"][BO]["corporation"] = "Unknown"

    game = import_game(log, SALT)
    assert game["players"][1]["corporation"] == "tharsis_republic"
    [bo_buy] = decisions(game, "buy", 1)
    assert game["positions"][bo_buy["position"]]["players"][1]["corporation"] == "tharsis_republic"


def replace_buys(log, *new_moves):
    """The log with its buy moves (19 and 20) replaced."""
    at = next(i for i, entry in enumerate(log["moves"]) if entry["move_number"] == 19)
    log["moves"][at : at + 2] = list(new_moves)
    return log


def test_cards_kept_one_at_a_time_add_up_with_or_without_a_summary():
    log = prelude_log()
    state = log["moves"][-2]["game_state"]
    replace_buys(
        log,
        move(19, BO, "other", "Bo keeps Big Asteroid | Bo pays 3 MC", state, cards_kept={BO: ["Big Asteroid"]}),
        move(19, BO, "other", "Bo keeps Olympus Conference | Bo pays 3 MC", state, cards_kept={BO: ["Olympus Conference"]}),
        move(20, ADA, "other", "Ada keeps Deimos Down | Ada pays 3 MC", state, cards_kept={ADA: ["Deimos Down"]}),
        move(20, ADA, "other", "Ada keeps Kelp Farming | Ada pays 3 MC", state, cards_kept={ADA: ["Kelp Farming"]}),
        move(
            20, ADA, "other", "Ada keeps 2 cards: Deimos Down, Kelp Farming | Bo keeps Olympus Conference", state,
            cards_kept={ADA: ["Deimos Down", "Kelp Farming"], BO: ["Olympus Conference"]},
        ),
    )  # fmt: skip

    game = import_game(log, SALT)
    assert [d["picked"] for d in decisions(game, "buy", 0)] == [["kelp_farming", "deimos_down"]]
    assert [d["picked"] for d in decisions(game, "buy", 1)] == [["olympus_conference", "big_asteroid"]]


def test_a_player_without_a_keep_while_the_other_s_keep_is_logged_bought_nothing():
    log = prelude_log()
    state = log["moves"][-2]["game_state"]
    replace_buys(
        log, move(19, BO, "other", "Bo keeps Big Asteroid | Bo pays 3 MC", state, cards_kept={BO: ["Big Asteroid"]})
    )

    game = import_game(log, SALT)
    assert [d["picked"] for d in decisions(game, "buy", 0)] == [[]]
    assert [d["picked"] for d in decisions(game, "buy", 1)] == [["big_asteroid"]]


def test_a_buy_is_not_guessed_when_neither_keep_is_logged():
    log = replace_buys(prelude_log())

    assert decisions(import_game(log, SALT), "buy", 0) == []


def test_in_a_conceded_game_a_missing_keep_in_the_last_generation_is_not_taken_as_buying_nothing():
    log = prelude_log()
    log["conceded"] = True
    state = log["moves"][-2]["game_state"]
    replace_buys(
        log, move(19, BO, "other", "Bo keeps Big Asteroid | Bo pays 3 MC", state, cards_kept={BO: ["Big Asteroid"]})
    )

    assert decisions(import_game(log, SALT), "buy", 0) == []


ADA_PICKS = ["kelp_farming", "deimos_down", "standard_technology"]


def test_a_pick_missing_from_the_log_is_read_from_the_hand_passed_on():
    log = prelude_log()
    pick = moves_by_number(log)[14]  # "You draft Deimos Down", which also shows the next hands
    pick.update(description="Ada other", card_drafted=None, reason=None, action_type="other")

    game = import_game(log, SALT)
    assert [d["picked"] for d in decisions(game, "draft", 0)] == ADA_PICKS
    [ada_buy] = decisions(game, "buy", 0)
    assert ada_buy["picked"] == ["kelp_farming", "deimos_down"]


def test_a_pick_the_log_names_wrongly_is_read_from_the_hand_passed_on():
    log = prelude_log()
    moves_by_number(log)[14].update(description="You draft Big Asteroid", card_drafted="Big Asteroid")

    game = import_game(log, SALT)
    assert [d["picked"] for d in decisions(game, "draft", 0)] == ADA_PICKS
    assert [d["picked"] for d in decisions(game, "draft", 1)] == [
        "industrial_microbes",
        "olympus_conference",
        "big_asteroid",
    ]


def test_a_pick_without_next_hands_is_taken_from_the_log():
    log = prelude_log()
    for entry in log["moves"]:
        if entry["move_number"] == 16:
            entry["card_options"] = None  # Ada's third pick, Standard Technology: no next hands
    log["moves"] = [entry for entry in log["moves"] if entry["move_number"] not in (17, 18, 19, 20, 21, 22)]

    game = import_game(log, SALT)
    assert [d["picked"] for d in decisions(game, "draft", 0)] == ADA_PICKS


def test_the_setup_position_is_the_start_even_if_the_first_state_in_the_log_is_later():
    log = prelude_log()
    first = log["moves"][0]["game_state"]["player_trackers"][BO]
    first.update({"M€": 40, "M€ Production": 2, "Steel": 4, "Hand Counter": 2})  # Bo's secret setup, seen early

    game = import_game(log, SALT)
    [ada_setup] = decisions(game, "setup", 0)
    bo = game["positions"][ada_setup["position"]]["players"][1]
    assert set(bo["resources"].values()) == {0}
    assert set(bo["production"].values()) == {0}
    assert (bo["hand_counter"], bo["terraform_rating"]) == (None, 20)


def test_without_one_card_hands_the_last_card_is_what_the_other_player_passed_last():
    log = prelude_log()
    moves_by_number(log)[16]["card_options"] = None
    log["moves"] = [entry for entry in log["moves"] if entry["move_number"] not in (17, 18)]

    game = import_game(log, SALT)
    [ada_buy] = decisions(game, "buy", 0)
    assert ada_buy["offer"] == ["kelp_farming", "deimos_down", "standard_technology", "tundra_farming"]
    [bo_buy] = decisions(game, "buy", 1)
    assert bo_buy["offer"] == ["industrial_microbes", "olympus_conference", "big_asteroid", "terraforming_ganymede"]


@pytest.mark.parametrize("winner", ["Unknown", "Ada_before_renaming"])
def test_the_winner_is_who_came_first_when_the_named_winner_is_unknown_or_renamed(winner):
    log = prelude_log()
    log["winner"] = winner

    assert [player["winner"] for player in import_game(log, SALT)["players"]] == [True, False]


def test_players_who_share_first_place_are_neither_the_winner():
    log = prelude_log()
    log["winner"] = "Unknown"
    for player in log["players"].values():
        player["elo_data"]["position"] = 1

    assert [player["winner"] for player in import_game(log, SALT)["players"]] == [False, False]

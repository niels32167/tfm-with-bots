"""The slim copy of a kept Game's moves, for tickets 09 and 10 once the archive is gone: without names,
Board Game Arena ids or timestamps, and with each game state stored as what changed."""

import copy
import json

from ai.recorded_games.moves import expand_moves, slim_moves
from tests.ai.recorded_games.logs import ADA, BO, SALT, prelude_log


def test_no_name_id_or_timestamp_is_kept():
    slim = slim_moves(prelude_log(), SALT)

    text = json.dumps(slim, ensure_ascii=False)
    for leak in ("Ada", "Bo ", ADA, BO, "624518601", "7:20:55", "7:36:01"):
        assert leak not in text


def test_players_are_named_by_their_place_in_descriptions_and_fields():
    moves = expand_moves(slim_moves(prelude_log(), SALT))

    by_number = {entry["move_number"]: entry for entry in moves}
    assert by_number[4]["description"] == "Player 1 plays card Excentric Sponsor"
    assert by_number[4]["player"] == 0
    assert by_number[12]["description"] == "Player 2 drafts Industrial Microbes"
    assert by_number[12]["card_options"] == {"0": ["Big Asteroid", "Deimos Down", "Tundra Farming"], "1": [
        "Standard Technology", "Terraforming Ganymede", "Olympus Conference",
    ]}  # fmt: skip


def test_each_move_s_game_state_comes_back_whole():
    log = prelude_log()
    moves = expand_moves(slim_moves(copy.deepcopy(log), SALT))

    assert len(moves) == len(log["moves"])
    for original, expanded in zip(log["moves"], moves):
        state = expanded["game_state"]
        assert state["generation"] == original["game_state"]["generation"]
        assert state["player_trackers"]["0"] == original["game_state"]["player_trackers"][ADA]
        assert state["player_trackers"]["1"] == original["game_state"]["player_trackers"][BO]
        assert state["player_vp"]["1"] == original["game_state"]["player_vp"][BO]
    final = moves[-1]["game_state"]
    assert final["milestones"] == {"Planner": {"player": 0, "move_number": 21}}
    assert final["awards"] == {"Thermalist": {"player": 1, "move_number": 22}}


def test_unchanged_game_states_take_no_room():
    slim = slim_moves(prelude_log(), SALT)

    # Moves 12 to 19 change nothing in the game state.
    assert [entry.get("game_state") for entry in slim["moves"][11:19]] == [None] * 8


def test_a_player_named_like_a_card_leaves_card_names_alone():
    log = prelude_log()
    log["players"][BO]["player_name"] = "Moss"
    for entry in log["moves"]:
        entry["description"] = entry["description"].replace("Bo ", "Moss ")

    moves = expand_moves(slim_moves(log, SALT))
    assert moves[0]["card_options"]["1"][-1] == "Moss"
    assert (
        moves[4]["description"] == "Player 2 plays card Galilean Mining | Player 2 increases Titanium Production by 1"
    )

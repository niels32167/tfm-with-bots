"""Recorded Games replayed through the engine (ticket 10 of phase 2), on hand-written Games in the dataset's
shape (tests/ai/recorded_games/recorded.py). No archive is needed."""

import json
import re

import pytest
import tm_engine

from ai.recorded_games.replay import Differs, RecordedGameReplay, action_decisions, area_at, replay_game
from tests.ai.recorded_games.recorded import FIRST_BUYS, FIRST_CARDS, SECOND_CARDS, RecordedGame


def replayed(recorded: RecordedGame) -> tuple[object, tm_engine.Game]:
    outcome = replay_game(recorded.game(), recorded.slim())
    return outcome, tm_engine.Game.from_replay(outcome.replay)


def board(game: tm_engine.Game, player: int) -> dict:
    return game.full_view()["players"][player]


def test_a_replay_starts_from_the_deal_the_log_gives_in_player_order_from_the_first_player():
    outcome, _ = replayed(RecordedGame().setup_moves())

    deal = outcome.replay["start"]["settings"]["deal"]
    assert deal["first_player"] == 0
    assert deal["corporations"] == ["mining_guild", "ecoline", "teractor", "credicor"]
    assert deal["prelude_cards"][:4] == ["donation", "supplier", "loan", "biofuels"]
    assert deal["project_cards"] == FIRST_CARDS + SECOND_CARDS


def test_setup_and_the_prelude_cards_replay_and_a_conceded_game_ends_with_its_log():
    outcome, game = replayed(RecordedGame().setup_moves())

    assert outcome.complete
    assert outcome.difference is None
    first = board(game, 0)
    assert first["corporation"] == "mining_guild"
    assert first["played_prelude_cards"] == ["donation", "supplier"]
    assert sorted(first["hand"]) == sorted(FIRST_BUYS)
    assert first["resources"]["megacredits"] == 30 - 9 + 21
    assert board(game, 1)["played_prelude_cards"] == ["business_empire", "galilean_mining"]


def test_an_action_is_paid_and_placed_as_its_lines_say():
    recorded = (
        RecordedGame()
        .setup_moves()
        .play(0, "Mine", "increases Steel Production by 1", paid=("pays 2 Steel",))
        .move(0, "Player 1 skips second action")
        .move(1, "Player 2 plays standard project City | Player 2 pays 25 M€", action_type="standard_project")
        .move(1, "Player 2 places City on Tharsis Hex 3,4 (3,4)", action_type="place_tile")
    )

    outcome, game = replayed(recorded)

    assert outcome.complete
    assert board(game, 0)["resources"]["steel"] == 5 + 4 - 2
    tiles = [(area["area"], area["tile"]) for area in game.full_view()["board"] if area["tile"]]
    assert tiles == [("D2", {"type": "city", "owner": 1})]


def test_a_play_of_a_card_the_hand_lacks_is_a_difference_and_the_replay_stops_before_it():
    recorded = (
        RecordedGame().setup_moves().move(1, "Player 2 plays card Comet", action_type="play_card", card_played="Comet")
    )

    outcome, game = replayed(recorded)

    assert not outcome.complete
    assert outcome.difference.cause == "card not in hand"
    assert outcome.difference.detail == "comet"
    assert outcome.difference.move_number == len(recorded.moves)
    # The Replay goes up to the Decision the log disagrees with. Player 1, whose Turn came first, is taken to
    # have passed unlogged, as the log goes on with Player 2.
    assert game.decision == {**game.decision, "player": 1, "kind": "action"}
    assert outcome.unlogged["pass"] == 1
    # The pass the log left out is marked as inferred, for training to leave out.
    record = {"replay": outcome.replay, "inferred": outcome.inferred}
    inferred = [
        (d["player"], d["options"][d["picked"]]["details"]["type"]) for d in action_decisions(record) if d["inferred"]
    ]
    assert inferred == [(0, "pass")]
    assert outcome.moves_reached == len(recorded.moves) - 1


def test_trackers_are_compared_after_each_action_and_a_difference_that_lasts_stops_the_game():
    recorded = (
        RecordedGame()
        .setup_moves()
        .play(0, "Power Plant", paid=("pays 4 M€",), trackers={0: {"m": 40}})
        .play(0, "Mine", paid=("pays 2 Steel",), trackers={0: {"m": 39}})
        .move(1, "Player 2 passes", action_type="pass")
    )

    outcome, _ = replayed(recorded)

    assert outcome.difference.cause == "trackers differ: M€"
    assert outcome.difference.move_number == 8
    assert "engine 38, log 40" in outcome.difference.detail
    # The Replay ends where the trackers first disagreed, before the play that confirmed it.
    picked = [d["options"][d["picked"]]["details"].get("card") for d in action_decisions({"replay": outcome.replay})]
    assert "power_plant" in picked
    assert "mine" not in picked


def test_a_tracker_that_disagrees_once_is_taken_as_lag():
    recorded = (
        RecordedGame()
        .setup_moves()
        .play(0, "Power Plant", paid=("pays 4 M€",), trackers={0: {"m": 41}})
        .play(0, "Mine", paid=("pays 2 Steel",), trackers={0: {"m": 38}})
        .move(1, "Player 2 passes", action_type="pass")
    )

    outcome, _ = replayed(recorded)

    assert outcome.complete


def test_cards_sold_without_their_names_are_ones_their_player_never_plays_later():
    recorded = (
        RecordedGame()
        .setup_moves()
        .move(0, "Player 1 plays standard project Sell patents", action_type="standard_project")
        .move(0, "Player 1 discards 1 card/s | Player 1 gains 1 M€")
        .move(0, "Player 1 pays 2 Steel | Player 1 plays card Mine", action_type="play_card", card_played="Mine")
        .move(1, "Player 2 passes", action_type="pass")
        .move(0, "Player 1 pays 6 M€ | Player 1 plays card Sponsors", action_type="play_card", card_played="Sponsors")
    )

    outcome, game = replayed(recorded)

    assert outcome.complete
    assert board(game, 0)["hand"] == []
    assert "power_plant" not in board(game, 0)["played_cards"]


def a_second_generation(*, buy_lines: list[str]) -> RecordedGame:
    """Both Players pass; Generation 2's Draft deals Player 2, now first, Deep Well Heating, Trees, Grass and
    Heather, and Player 1 Moss, Algae, Kelp Farming and Farming."""
    recorded = RecordedGame().setup_moves().move(0, "Player 1 passes", action_type="pass")
    recorded.move(
        1,
        "Player 1 drafts 4 cards: Moss, Algae, Kelp Farming, Farming | "
        "Player 2 drafts 4 cards: Deep Well Heating, Trees, Grass, Heather",
        action_type="pass",
        generation=2,
    )
    # Each pack goes back and forth, so each Player's third pick is from the pack the other first picked from.
    for player, picks in ((1, ["deep_well_heating", "algae", "grass"]), (0, ["moss", "trees", "kelp_farming"])):
        for number, card in enumerate(picks, start=1):
            recorded.decisions.append(
                {"kind": "draft", "player": player, "generation": 2, "pick": number, "picked": card}
            )
    recorded.decisions.append({"kind": "buy", "player": 1, "generation": 2, "picked": ["deep_well_heating", "algae"]})
    recorded.decisions.append({"kind": "buy", "player": 0, "generation": 2, "picked": ["moss"]})
    for line in buy_lines:
        recorded.move(int(line[7]) - 1, line, action_type="buy_card")
    return recorded


def test_the_drafts_deal_is_drawn_in_player_order_from_the_generations_first_player():
    recorded = a_second_generation(buy_lines=[])

    deal = RecordedGameReplay(recorded.game(), recorded.slim()).deal()

    assert deal["project_cards"][-8:] == [
        "deep_well_heating", "trees", "grass", "heather", "moss", "algae", "kelp_farming", "farming",
    ]  # fmt: skip


def test_a_research_buy_follows_its_keep_lines_where_a_card_is_taken_back():
    recorded = a_second_generation(
        buy_lines=[
            "Player 2 keeps 2 cards: Deep Well Heating, Algae | Player 2 pays 6 M€",
            "Player 2 drafts Algae",
            "Player 2 keeps Deep Well Heating | Player 2 pays 3 M€",
            "Player 1 keeps Moss | Player 1 pays 3 M€",
        ]
    ).move(
        1,
        "Player 2 pays 13 M€ | Player 2 plays card Deep Well Heating",
        action_type="play_card",
        card_played="Deep Well Heating",
    )

    outcome, game = replayed(recorded)

    assert outcome.complete
    assert "algae" not in board(game, 1)["hand"]
    assert "deep_well_heating" in board(game, 1)["played_cards"]
    assert outcome.unlogged["buy differing from its record"] == 1


def test_board_game_arenas_coordinates_name_the_engines_areas():
    assert area_at(4, 2) == "B2"  # Tharsis Tholus
    assert area_at(2, 4) == "D1"  # Pavonis Mons
    assert area_at(9, 4) == "D8"  # An Ocean Area
    assert area_at(1, 5) == "E1"  # Arsia Mons
    assert area_at(7, 9) == "J5"
    assert area_at(0, 2) == "phobos_space_haven"
    assert area_at(0, 3) == "ganymede_colony"


def test_the_action_phase_decisions_of_a_replay_are_rebuilt_as_their_player_saw_them():
    recorded = (
        RecordedGame()
        .setup_moves()
        .move(0, "Player 1 pays 2 Steel | Player 1 plays card Mine", action_type="play_card", card_played="Mine")
        .move(0, "Player 1 skips second action")
        .move(1, "Player 2 plays card Comet", action_type="play_card", card_played="Comet")
    )
    outcome = replay_game(recorded.game(), recorded.slim())
    record = {"replay": outcome.replay}

    decisions = list(action_decisions(record))

    kinds = [(decision["player"], decision["kind"]) for decision in decisions]
    assert kinds == [(0, "play_prelude_card"), (1, "play_prelude_card"), (0, "action"), (0, "payment"), (0, "action")]
    mine = decisions[2]
    assert mine["options"][mine["picked"]]["details"] == {"type": "play_card", "card": "mine", "cost": 4}
    assert all("sequence" not in decision for decision in decisions)
    # Up to the first difference only, and each as its Player saw it: Player 1 never sees Player 2's hand.
    second_hand = {"satellites", "media_group", "great_dam"}
    for decision in decisions:
        if decision["player"] == 0:
            assert decision["view"]["players"][1]["hand"] is None
            assert not second_hand & set(re.findall(r'"([a-z_]+)"', json.dumps(decision)))


def test_experimental_forests_placement_bonus_is_dealt_before_the_cards_it_reveals():
    # Board Game Arena names the revealed cards before the Greenery's placement bonus; the engine draws the
    # bonus first, as the rulebook has it, so the deal puts that card first (docs/rules-notes.md).
    recorded = (
        RecordedGame()
        .move(0, "Player 1 plays card Experimental Forest", action_type="play_card", card_played="Experimental Forest")
        .move(0, "Player 1 keeps 2 cards: Trees, Grass | Player 1 increases Oxygen Level by 1 step/s to a value of 1")
        .move(0, "Player 1 draws Moss")
        .move(1, "Player 2 plays card Business Empire", action_type="play_card", card_played="Business Empire")
    )

    deal = RecordedGameReplay(recorded.game(), recorded.slim()).deal()

    assert deal["project_cards"][-3:] == ["moss", "trees", "grass"]


class FinishedGame:
    """Stands in for a finished engine Game: only its scores are read."""

    def __init__(self, totals: list[int]) -> None:
        self.scores = [{"total": total} for total in totals]


def test_a_game_not_conceded_ends_with_the_totals_its_scoring_lines_give_over_the_datasets():
    # The dataset's Victory Points come from the last game state, which can miss the final Greenery conversion.
    recorded = RecordedGame(conceded=False).move(0, "Player 1 scores 116 TOTAL VP | Player 2 scores 81 TOTAL VP")
    recorded.victory_points = [114, 81]
    replay = RecordedGameReplay(recorded.game(), recorded.slim())

    replay.check_scores(FinishedGame([116, 81]))
    with pytest.raises(Differs, match="final scores differ"):
        replay.check_scores(FinishedGame([114, 81]))


def test_a_game_that_stopped_before_the_engine_could_start_it_gives_no_decisions():
    outcome = replay_game(RecordedGame().game(), {"game": "replay-test", "moves": []})

    assert outcome.difference.cause == "log names no plays"
    assert list(action_decisions({"replay": outcome.replay, "inferred": outcome.inferred})) == []

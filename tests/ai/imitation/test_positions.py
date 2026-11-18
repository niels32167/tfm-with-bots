"""The training Decisions of a Recorded Game (ticket 13 of phase 2): setup, Draft and buy Decisions as their
Player saw them, from the replay through the engine where it reaches them (the full Player View: hand, Tiles and
Prices known, as in play), and from the records elsewhere."""

import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

import tm_engine

from ai.encoding import CARD_FIELDS, GLOBAL_FIELDS, OPTION_FIELDS
from ai.imitation.encoded import Position
from ai.imitation.positions import PositionSettings, batches, positions, training_decisions
from ai.recorded_games.records import recorded_decisions
from tests.ai.recorded_games.test_records import GAME, MAX_PICKS, RECORDED_KINDS


def replay_of_the_example(*, picks: int | None = None) -> dict:
    """Seed 7 played with GAME's recorded picks up to Generation 2's Action phase, as replays.jsonl.gz holds
    it: the whole way, or only its first `picks` picks, as when the replay stopped at a difference."""
    game = tm_engine.Game(seed=7, players=2, prelude=True)
    recorded = iter(recorded_decisions(GAME))
    for _ in range(MAX_PICKS):
        decision = game.decision
        if game.player_view(decision["player"])["generation"] == 2 and game.player_view(0)["phase"] == "action":
            break
        if decision["kind"] in RECORDED_KINDS:
            game.pick(next(recorded)["picked"])
            continue
        types = [option["details"]["type"] for option in decision["options"]]
        game.pick(types.index("pass") if "pass" in types else 0)
    replay = game.replay
    if picks is not None:
        replay["picks"] = replay["picks"][:picks]
    return {"game": GAME["game"], "complete": picks is None, "replay": replay, "inferred": []}


def picks_of(decisions: list[dict]) -> list[tuple]:
    """Who picked what, when, in no particular order."""
    return sorted(
        (d["player"], d["generation"], d["kind"], d["options"][d["picked"]]["details"].get("card") or "done")
        for d in decisions
    )


def test_without_a_replay_the_decisions_are_the_records():
    decisions = list(training_decisions(GAME, None))

    assert picks_of(decisions) == picks_of(list(recorded_decisions(GAME)))
    assert {d["source"] for d in decisions} == {"records"}


def test_where_the_replay_reaches_the_decisions_come_from_it_with_the_hand_known():
    decisions = list(training_decisions(GAME, replay_of_the_example()))

    assert picks_of(decisions) == picks_of(list(recorded_decisions(GAME)))
    assert {d["source"] for d in decisions} == {"replay"}
    buys = [d for d in decisions if d["kind"] == "buy_cards" and d["generation"] == 2]
    assert all(board["hand"] is not None for d in buys for board in [d["view"]["players"][d["player"]]])


def test_past_where_the_replay_stopped_the_decisions_come_from_the_records():
    # 12 setup picks, then 1 Prelude Card played each and a pass each; stop inside Generation 2's Draft.
    whole = replay_of_the_example()["replay"]["picks"]
    stopped = len(whole) - 6
    decisions = list(training_decisions(GAME, replay_of_the_example(picks=stopped)))

    assert picks_of(decisions) == picks_of(list(recorded_decisions(GAME)))
    sources = {(d["generation"], d["kind"], d["source"]) for d in decisions}
    assert (1, "corporation", "replay") in sources
    assert (2, "buy_cards", "records") in sources
    assert (2, "buy_cards", "replay") not in sources


# The example has 22 setup, Draft and buy Decisions, each with more than one Option: per Player a Corporation,
# 2 Prelude Cards, 2 cards bought and done at setup, 3 Draft picks and a card bought and done in Generation 2.
EXAMPLE_DECISIONS = 22


def write_dataset(folder: Path, games: list[dict], replays: list[dict]) -> Path:
    """A dataset folder as ai.recorded_games writes it: here, one shard per Game."""
    for number, game in enumerate(games):
        shard = folder / "shards" / f"{number:03}"
        shard.mkdir(parents=True)
        for name, lines in [
            ("games.jsonl.gz", [game]),
            ("replays.jsonl.gz", [r for r in replays if r["game"] == game["game"]]),
        ]:
            with gzip.open(shard / name, "wt", encoding="utf-8") as file:
                file.writelines(json.dumps(line) + "\n" for line in lines)
        (shard / "shard.done").touch()
    return folder


def example(game_id: str, *, date: str, ratings: tuple[int | None, int | None] = (500, 500), prelude: bool = True):
    players = [{**board, "rating": rating} for board, rating in zip(GAME["players"], ratings, strict=True)]
    return {**GAME, "game": game_id, "date": date, "players": players, "prelude": prelude}


def kept(folder: Path, split: str, **settings) -> list[Position]:
    return list(positions(folder, split, PositionSettings(**settings), workers=0))


def test_positions_stream_the_games_of_one_split_encoded(tmp_path):
    folder = write_dataset(tmp_path, [example("early", date="2024-01-01"), example("late", date="2026-01-01")], [])

    trained = kept(folder, "train")
    tested = kept(folder, "test")

    assert len(trained) == len(tested) == EXAMPLE_DECISIONS
    assert {position.game for position in trained} == {"early"}
    first = trained[0]
    assert first.globals.shape == (len(GLOBAL_FIELDS),)
    assert first.cards.shape[1] == len(CARD_FIELDS)
    assert first.options.shape == (len(first.options), len(OPTION_FIELDS))
    assert 0 <= first.picked < len(first.options)


def test_the_rating_filter_keeps_the_decisions_of_players_rated_that_high(tmp_path):
    folder = write_dataset(tmp_path, [example("a", date="2024-01-01", ratings=(620, 410))], [])

    assert {p.player for p in kept(folder, "train", min_rating=600)} == {0}
    assert len(kept(folder, "train", min_rating=400)) == EXAMPLE_DECISIONS
    assert kept(folder, "train", min_rating=700) == []


def test_games_without_prelude_can_be_left_out(tmp_path):
    folder = write_dataset(tmp_path, [example("a", date="2024-01-01", prelude=False)], [])

    assert kept(folder, "train", prelude_games_only=True) == []


def test_worker_processes_give_the_same_positions(tmp_path):
    games = [example(f"g{n}", date="2024-01-01") for n in range(3)]
    folder = write_dataset(tmp_path, games, [{**replay_of_the_example(), "game": "g1"}])

    def summary(found: list[Position]) -> list[tuple]:
        return sorted((p.game, p.player, p.kind, p.source, p.picked, p.cards.tobytes()) for p in found)

    in_process = kept(folder, "train")
    in_workers = list(positions(folder, "train", PositionSettings(), workers=2))

    assert summary(in_workers) == summary(in_process)
    assert {p.source for p in in_process} == {"records", "replay"}


def test_training_batches_hold_each_position_once_padded_with_few_card_rows_wasted(tmp_path):
    games = [example(f"g{n}", date="2024-01-01") for n in range(3)]
    folder = write_dataset(tmp_path, games, [{**replay_of_the_example(), "game": "g1"}])
    expected = sorted(int(p.picked) for p in kept(folder, "train"))

    for workers in (0, 2):
        made = list(batches(folder, "train", PositionSettings(), workers=workers, seed=1, size=8, buffer=16))
        assert all(len(made_batch["picked"]) <= 8 for made_batch in made)
        assert sorted(int(pick) for made_batch in made for pick in made_batch["picked"]) == expected
        for made_batch in made:
            real_rows = made_batch["card_mask"].sum(axis=1)
            assert made_batch["cards"].shape[1] == real_rows.max()
            assert made_batch["options"][~made_batch["option_mask"]].sum() == 0


def test_worker_processes_load_only_what_reading_the_dataset_needs_not_the_callers_main_module(tmp_path):
    # Python starts worker processes by importing the caller's main module, which for the training command loads
    # PyTorch: 12 workers holding it once ran the laptop out of memory.
    folder = write_dataset(tmp_path / "dataset", [example("g", date="2024-01-01")], [])
    script = tmp_path / "caller.py"
    script.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "from ai.imitation.positions import PositionSettings, positions\n"
        "MARK = Path(sys.argv[2])\n"
        "MARK.write_text(MARK.read_text() + 'imported ') if MARK.exists() else MARK.write_text('imported ')\n"
        "if __name__ == '__main__':\n"
        "    found = list(positions(Path(sys.argv[1]), 'train', PositionSettings(), workers=2))\n"
        "    print(len(found))\n"
    )
    mark = tmp_path / "mark.txt"
    ran = subprocess.run(
        [sys.executable, str(script), str(folder), str(mark)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env={**os.environ, "PYTHONPATH": str(Path.cwd())},
    )

    assert ran.stdout.strip() == str(EXAMPLE_DECISIONS), ran.stderr
    assert mark.read_text() == "imported "

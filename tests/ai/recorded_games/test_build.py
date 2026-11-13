"""The importer command (`uv run python -m ai.recorded_games`): reads an archive of logs on all cores,
writes the dataset in shards it can resume, and reports coverage. Run here on tiny archives of
hand-written logs; the real archive is never needed."""

import json

import pytest

from ai.recorded_games.build import main
from ai.recorded_games.dataset import read_games, read_moves
from tests.ai.recorded_games.logs import ADA, BO, prelude_log


def write_log(archive, log, perspective, name=None):
    folder = archive / perspective
    folder.mkdir(parents=True, exist_ok=True)
    log["player_perspective"] = perspective
    path = folder / (name or f"game_{log['table_id']}_{perspective}.json")
    path.write_text(json.dumps(log))
    return path


def another_game(table, **changes):
    log = prelude_log()
    log["table_id"] = log["replay_id"] = table
    log.update(changes)
    return log


@pytest.fixture
def archive(tmp_path):
    """Four Games: one from both perspectives (one perspective without dealt cards), one on Hellas,
    one without Prelude, one naming a card outside the catalog; and an empty download file."""
    archive = tmp_path / "tm_statistics"
    write_log(archive, prelude_log(), ADA)
    bare = prelude_log()
    for player in bare["players"].values():
        player["starting_hand"] = None
    write_log(archive, bare, BO)
    write_log(archive, another_game("700", map="Hellas"), ADA)
    write_log(archive, another_game("701", prelude_on=False), ADA)
    unknown = another_game("702")
    unknown["players"][BO]["starting_hand"]["project_cards"][0] = "Venus Governor"
    write_log(archive, unknown, BO)
    (archive / ADA / ".azDownload-58c9-game_703_1001.json").write_text("")
    return archive


def build(archive, out, *extra):
    return main(["--archive", str(archive), "--out", str(out), "--processes", "2", *extra])


def test_the_dataset_holds_each_kept_game_once(archive, tmp_path, capsys):
    out = tmp_path / "dataset"

    assert build(archive, out) == 0

    games = list(read_games(out))
    assert sorted((len(game["decisions"]), game["prelude"]) for game in games) == [(10, False), (10, True)]
    assert len(list(read_moves(out))) == 2
    assert {game["game"] for game in games} == {moves["game"] for moves in read_moves(out)}


def test_the_report_counts_games_read_and_skipped_and_why(archive, tmp_path, capsys):
    out = tmp_path / "dataset"
    build(archive, out)

    coverage = json.loads((out / "coverage.json").read_text())
    assert coverage["files"] == 6
    assert coverage["games"] == 5
    assert coverage["kept"] == 2
    assert coverage["skipped"] == {"map Hellas": 1, "unknown names": 1, "unreadable file": 1}
    assert coverage["extra_perspectives"] == 1
    assert coverage["unknown_names"] == {"Venus Governor": 1}
    assert coverage["decisions"] == {"setup": 4, "draft": 12, "buy": 4}
    # Each Player's Research phase in Generation 2 of both kept Games: 3 picks and a buy.
    assert coverage["research_phases"] == {"complete": 4}
    printed = capsys.readouterr().out
    assert "Venus Governor" in printed
    assert "map Hellas" in printed
    assert "v2025.10.07.1844" in printed  # kept Games by scraper version
    assert "Dataset size" in printed


def test_a_finished_build_is_not_redone_and_an_interrupted_one_resumes(archive, tmp_path, capsys):
    out = tmp_path / "dataset"
    build(archive, out)
    salt = (out / "salt").read_bytes()
    finished = sorted(out.glob("shards/*/*.done"))
    ids = {game["game"] for game in read_games(out)}

    # As if interrupted: one shard's work lost, and a half-written file left behind.
    finished[0].unlink()
    (finished[0].parent / "games.jsonl.gz.partial").write_bytes(b"half")
    capsys.readouterr()
    assert build(archive, out) == 0

    assert "already done" in capsys.readouterr().out
    assert (out / "salt").read_bytes() == salt
    assert {game["game"] for game in read_games(out)} == ids
    assert not list(out.glob("shards/*/*.partial"))


def test_a_game_that_breaks_the_importer_is_reported_and_sets_the_exit_status(archive, tmp_path, capsys):
    broken = another_game("704")
    broken["moves"] = 5
    write_log(archive, broken, ADA)

    assert build(archive, tmp_path / "dataset") == 3

    printed = capsys.readouterr().out
    assert "failed: 1" in printed


def test_the_tables_command_reports_from_the_dataset(archive, tmp_path, capsys):
    from ai.recorded_games import tables

    out = tmp_path / "dataset"
    build(archive, out)
    capsys.readouterr()

    assert tables.main(["--out", str(out), "--least-offered", "1"]) == 0
    printed = capsys.readouterr().out
    assert "Starting hand" in printed
    assert "teractor" in printed
    assert "planner" in printed

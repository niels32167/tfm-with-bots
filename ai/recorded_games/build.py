"""The importer command: reads the archive of Recorded Games and writes the dataset (ADR 0012).

    uv run python -m ai.recorded_games
    uv run python -m ai.recorded_games --archive tm_statistics --out .cache/recorded-games --processes 8

The archive is a folder per perspective holding one log per Game, game_<table>_<player>.json. Logs of
one Game from several perspectives count as one Game: the most complete is kept. Games are split
into shards by table, and the shards are read in worker processes on all cores. A shard is written
under partial names and marked done last, so an interrupted build resumes with the shards not yet
done. A shard done is not read again even if the archive has changed since: after changing the
archive or the importer, delete the dataset's shards/ folder to build afresh, and its salt too for new
anonymous ids.

The logs are only ever parsed as JSON: nothing in the archive is run, and it is never on the import
path.

It reports coverage: files and Games read, Games skipped and why, names it couldn't map, and kept and
skipped Games by setting, rating and scraper version, as coverage.json and report.txt in the dataset
folder. The exit status is 0, 2 for wrong arguments, and 3 if a Game broke the importer.
"""

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai.recorded_games.dataset import DATASET_FOLDER
from ai.recorded_games.importer import DRAFTED, Skipped, choose_perspective, import_game, scraper_version
from ai.recorded_games.moves import slim_moves

ARCHIVE_FOLDER = Path(__file__).parents[2] / "tm_statistics"
SHARDS = 128
LOG_NAME = re.compile(r"game_(\d+)_(\d+)\.json$")
A_GAME_FAILED = 3
RATING_BANDS = [(600, "600+"), (500, "500–599"), (400, "400–499"), (300, "300–399"), (0, "below 300")]


@dataclass(frozen=True)
class ShardTask:
    folder: Path
    games: tuple[tuple[str, tuple[Path, ...]], ...]
    salt: bytes


def find_logs(archive: Path) -> dict[str, list[Path]]:
    """Each Game's log files, by table id. A leftover of a broken download, named like
    ".azDownload-<id>-game_<table>_<player>.json", counts with its Game; a file named like no log is
    a Game of its own."""
    games: dict[str, list[Path]] = {}
    for folder in sorted(path for path in archive.iterdir() if path.is_dir()):
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            named = LOG_NAME.search(path.name)
            games.setdefault(named.group(1) if named else str(path), []).append(path)
    return games


def shard_of(table: str) -> int:
    return int(hashlib.sha256(table.encode()).hexdigest(), 16) % SHARDS


def read_log(path: Path) -> dict[str, Any] | None:
    """A log parsed as JSON, or None for an empty or broken file."""
    try:
        log = json.loads(path.read_bytes())
    except OSError, ValueError:
        return None
    return log if isinstance(log, dict) and isinstance(log.get("players"), dict) else None


def rating_band(log: dict[str, Any]) -> str:
    """The band of the lower of the Players' ratings, as the spec counts them."""
    ratings = [(player.get("elo_data") or {}).get("game_rank") for player in log["players"].values()]
    if not ratings or any(not isinstance(rating, int) for rating in ratings):
        return "unknown"
    return next(label for floor, label in RATING_BANDS if min(ratings) >= floor)


def count(report: dict[str, Any], *keys: str) -> None:
    for key in keys[:-1]:
        report = report.setdefault(key, {})
    report[keys[-1]] = report.get(keys[-1], 0) + 1


def tally(report: dict[str, Any], log: dict[str, Any] | None, outcome: str) -> None:
    """Counts a Game read, kept or skipped, by its setting, rating band and scraper version."""
    if log is None:
        setting = band = version = "unknown"
    else:
        setting = "Prelude" if log.get("prelude_on") else "no Prelude"
        band = rating_band(log)
        version = str(scraper_version(log))
    count(report, "by_setting", setting, outcome)
    count(report, "by_rating", band, outcome)
    count(report, "by_version", version, outcome)


def research_phases(game: dict[str, Any]) -> list[str]:
    """For a Game with Draft Decisions, how complete each Player's Research phases are: 3 picks (the
    fourth card comes by itself) and a buy."""
    if not any(decision["kind"] == "draft" for decision in game["decisions"]):
        return []
    found: dict[tuple[str, int, int], int] = {}
    for decision in game["decisions"]:
        key = (decision["kind"], decision["player"], decision["generation"])
        found[key] = found.get(key, 0) + 1
    phases = []
    for generation in sorted({position["generation"] for position in game["positions"] if position["generation"] >= 2}):
        for player in range(len(game["players"])):
            picks, bought = found.get(("draft", player, generation), 0), found.get(("buy", player, generation), 0)
            if picks == DRAFTED - 1 and bought:
                phases.append("complete")
            elif picks == DRAFTED - 1:
                phases.append("buy not found")
            else:
                phases.append(f"{picks} picks found" + ("" if bought else ", buy not found"))
    return phases


def build_shard(task: ShardTask) -> dict[str, Any]:
    """Reads one shard's Games and writes its part of the dataset; returns its coverage report."""
    task.folder.mkdir(parents=True, exist_ok=True)
    for partial in task.folder.glob("*.partial"):
        partial.unlink()
    report: dict[str, Any] = {"files": 0, "games": 0, "kept": 0, "extra_perspectives": 0, "failed": 0}
    failures: list[str] = []
    games_file, moves_file = task.folder / "games.jsonl.gz.partial", task.folder / "moves.jsonl.gz.partial"
    with gzip.open(games_file, "wt", encoding="utf-8") as games, gzip.open(moves_file, "wt", encoding="utf-8") as moves:
        for _, paths in task.games:
            report["files"] += len(paths)
            report["games"] += 1
            logs = [log for log in map(read_log, paths) if log is not None]
            if not logs:
                count(report, "skipped", "unreadable file")
                tally(report, None, "skipped")
                continue
            report["extra_perspectives"] += len(logs) - 1
            log = logs[0]
            try:
                log = choose_perspective(logs)
                game = import_game(log, task.salt)
                slim = slim_moves(log, task.salt)
            except Skipped as skipped:
                count(report, "skipped", skipped.reason)
                for name in skipped.names:
                    count(report, "unknown_names", name)
                tally(report, log, "skipped")
                continue
            except Exception as error:  # noqa: BLE001 - a broken Game is reported, not fatal to the build
                report["failed"] += 1
                failures.append(f"{paths[0]}: {type(error).__name__}: {error}")
                tally(report, log, "failed")
                continue
            games.write(json.dumps(game, separators=(",", ":")) + "\n")
            moves.write(json.dumps(slim, separators=(",", ":"), ensure_ascii=False) + "\n")
            report["kept"] += 1
            tally(report, log, "kept")
            count(report, "kept_with_decisions" if game["decisions"] else "kept_without_decisions", "all")
            for decision in game["decisions"]:
                count(report, "decisions", decision["kind"])
            for phase in research_phases(game):
                count(report, "research_phases", phase)
    report["failures"] = failures
    (task.folder / "report.json").write_text(json.dumps(report))
    games_file.rename(task.folder / "games.jsonl.gz")
    moves_file.rename(task.folder / "moves.jsonl.gz")
    (task.folder / "shard.done").touch()
    return report


def merge(total: dict[str, Any], part: dict[str, Any]) -> dict[str, Any]:
    for key, value in part.items():
        if isinstance(value, dict):
            merge(total.setdefault(key, {}), value)
        elif isinstance(value, list):
            total[key] = total.get(key, []) + value
        else:
            total[key] = total.get(key, 0) + value
    return total


def salt_of(out: Path) -> bytes:
    """The dataset's secret salt for anonymous ids, made once and kept beside it."""
    path = out / "salt"
    if not path.exists():
        out.mkdir(parents=True, exist_ok=True)
        path.write_bytes(os.urandom(32).hex().encode())
    return path.read_bytes()


def folder_size(folder: Path) -> int:
    return sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())


def report_text(coverage: dict[str, Any], size: int) -> str:
    def table(title: str, rows: dict[str, dict[str, int]]) -> list[str]:
        lines = [f"{title}:", f"  {'':24}{'kept':>10}{'skipped':>10}{'failed':>10}"]
        for label, counts in sorted(rows.items(), key=lambda item: -sum(item[1].values())):
            lines.append(
                f"  {label:24}" + "".join(f"{counts.get(key, 0):>10,}" for key in ("kept", "skipped", "failed"))
            )
        return lines + [""]

    decisions = coverage.get("decisions", {})
    lines = [
        (
            f"Files read: {coverage['files']:,}, Games: {coverage['games']:,} "
            f"({coverage['extra_perspectives']:,} further perspective files of the same Games)."
        ),
        (
            f"Kept: {coverage['kept']:,} ({coverage.get('kept_with_decisions', {}).get('all', 0):,} with "
            f"Decisions), failed: {coverage['failed']:,}."
        ),
        "Decisions: " + ", ".join(f"{kind} {decisions.get(kind, 0):,}" for kind in ("setup", "draft", "buy")) + ".",
        "Research phases of Games with Draft Decisions, per Player: "
        + ", ".join(
            f"{label} {number:,}"
            for label, number in sorted(coverage.get("research_phases", {}).items(), key=lambda item: -item[1])
        )
        + ".",
        "",
        "Skipped, and why:",
        *(
            f"  {reason:40}{number:>10,}"
            for reason, number in sorted(coverage.get("skipped", {}).items(), key=lambda item: -item[1])
        ),
        "",
    ]
    unknown = coverage.get("unknown_names", {})
    if unknown:
        lines.append(f"Names not mapped ({len(unknown):,}; Games naming each):")
        lines += [
            f"  {name:40}{number:>10,}" for name, number in sorted(unknown.items(), key=lambda item: -item[1])[:60]
        ]
        lines.append("")
    lines += table("By setting", coverage.get("by_setting", {}))
    lines += table("By the lower Player's rating", coverage.get("by_rating", {}))
    lines += table("By scraper version", coverage.get("by_version", {}))
    if coverage.get("failures"):
        lines.append("Games that broke the importer:")
        lines += [f"  {failure}" for failure in coverage["failures"][:20]]
        lines.append("")
    lines.append(f"Dataset size: {size / 1e9:.2f} GB ({size:,} bytes).")
    return "\n".join(lines)


def build(archive: Path, out: Path, processes: int | None = None) -> dict[str, Any]:
    """Builds the dataset in `out` from `archive`, resuming shards already done; returns the coverage."""
    salt = salt_of(out)
    by_shard: dict[int, list[tuple[str, tuple[Path, ...]]]] = {}
    for table, paths in find_logs(archive).items():
        by_shard.setdefault(shard_of(table), []).append((table, tuple(paths)))
    tasks = [
        ShardTask(out / "shards" / f"{number:03}", tuple(games), salt) for number, games in sorted(by_shard.items())
    ]
    done = [task for task in tasks if (task.folder / "shard.done").exists()]
    to_do = [task for task in tasks if task not in done]
    print(f"{len(done)} of {len(tasks)} shards already done; reading {len(to_do)}.", flush=True)
    coverage: dict[str, Any] = {}
    for task in done:
        merge(coverage, json.loads((task.folder / "report.json").read_text()))
    processes = processes or os.cpu_count() or 1
    with ProcessPoolExecutor(processes) as pool:
        futures = [pool.submit(build_shard, task) for task in to_do]
        for finished, future in enumerate(as_completed(futures), start=1):
            merge(coverage, future.result())
            print(f"  {finished} of {len(to_do)} shards read", file=sys.stderr, flush=True)
    for key in ("files", "games", "kept", "extra_perspectives", "failed"):
        coverage.setdefault(key, 0)
    (out / "coverage.json").write_text(json.dumps(coverage, indent=1, ensure_ascii=False))
    return coverage


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ai.recorded_games", description=__doc__.splitlines()[0])
    parser.add_argument("--archive", type=Path, default=ARCHIVE_FOLDER, help="(default tm_statistics/)")
    parser.add_argument("--out", type=Path, default=DATASET_FOLDER, help="(default .cache/recorded-games/)")
    parser.add_argument("--processes", type=int, help="worker processes (default: 1 per core)")
    parsed = parser.parse_args(arguments)
    if not parsed.archive.is_dir():
        parser.error(f"no archive at {parsed.archive}")
    coverage = build(parsed.archive, parsed.out, parsed.processes)
    text = report_text(coverage, folder_size(parsed.out))
    (parsed.out / "report.txt").write_text(text + "\n")
    print(text)
    return A_GAME_FAILED if coverage["failed"] else 0

"""The self-play loop (ticket 15 of phase 2): it starts the Value Model from the Imitation Model and Recorded Games'
results, then improves it by self-play, one round at a time.

    uv run python -u -m ai.value.loop --minutes 50
    uv run python -u -m ai.value.loop --rounds 12 --minutes 120
    uv run python -u -m ai.value.loop --register

A run lives in its own folder (`--run`, by default .cache/models/value-runs/main) and goes through named steps:
1. **warm start**: the Value Model, warm-started from the Imitation Model's weights (`--policy`), learns from
   `--warm-positions` positions of Recorded Games with Prelude, not conceded, in the training split, with each
   Game's result. It is version v000, and is measured on the validation split. Only a share of each Game's
   positions is kept (`--warm-keep`, and `--keep` for the loop's own Games): every position of a Game has the same
   result, and with all of them in a few batches the model learns which Game it is in (it overfit so on
   2026-11-20: training loss 0.33, validation loss 0.98). With `--start-from`, v000 is instead a copy of a saved
   Value Model, such as an earlier run's best version.
2. **panel**: the fixed old Controllers (`--panel`) play each other, and their ratings are fitted from that.
3. **rate v000**, and then each round:
4. **play**: `--games` Games, half the best version against itself and half against a pool of every earlier
   accepted version and the `--pool-bots`, taken in turn. Every Game is saved, as a Replay with its results, for
   training: the last `--buffer-rounds` rounds are kept and older ones deleted.
5. **train**: a candidate, from the best version's weights, makes `--train-passes` passes over the positions kept
   from the kept rounds' Games. (The first run trained a fixed 100,000 positions a round, about five passes over
   round 1's, and learned them by heart: training loss 0.18 against 0.46 at the warm start.)
6. **gate**: the candidate plays the best version (`--gate-games`); it joins the pool as the new best only if it
   scores at least `--gate-score`.
7. **rate**: the candidate plays each Controller of the panel (`--rating-games` each), on the same seeds for every
   version, and gets an Elo rating with the Imitation Bot at 0 (the first Controller of the panel without it).
   Ratings are logged in ratings.tsv, by round and minutes of training, and printed.

state.json lists the steps done. Each step's output is written whole or not at all, so a run stopped at any moment
(Ctrl-C, `systemctl --user stop`, a reboot) resumes with the step it was in when the same command is given again.
`--rounds` (the rounds in all), `--minutes` (for this invocation; no step starts after it), `--processes` and
`--register` may change between invocations; every other setting is fixed when the run starts, saved in run.json
and with every model, beside the seed, the commit, the engine's version and a hash of the Imitation Model's file, so
that a run can be repeated. Other settings for the same run are refused.

Every Game is played by ai.match, so each Controller answers through its handle. `--register` copies the run's best
version to .cache/models/value.pt, where the registered Value Bot reads it.

Exit status: 0, or 2 for wrong arguments or settings that differ from the run's.
"""

import argparse
import functools
import gzip
import hashlib
import importlib.metadata
import json
import platform
import random
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import torch

import ai.imitation
import ai.value
from ai.controllers import make_controller
from ai.encoding import format_stamp
from ai.imitation.model import load_model, save_model
from ai.match import Maker, MatchResult, MatchSettings, run_match
from ai.recorded_games.dataset import DATASET_FOLDER, shards
from ai.value.bot import SAMPLES, SHARE, TRIED, ValueBot
from ai.value.model import ValueModel, warm_started
from ai.value.samples import ValueSample, results_of, sample_batches
from ai.value.train import fit, measured

WRONG_ARGUMENTS = 2
REPOSITORY = Path(__file__).parents[2]

# Positions each worker process holds to shuffle.
SHUFFLE_BUFFER = 4_096
# Validation positions measured after the warm start: enough for a loss to two decimals.
VALIDATION_POSITIONS = 100_000
# The anchor of the ratings: the Imitation Bot is rated 0.
ANCHOR = "imitation"
# Settings that may change between invocations of one run: none changes what the run learns.
CHANGEABLE = ("rounds", "minutes", "register", "processes")
# Match seeds, apart for each use; the rating seeds are the same for every version.
SEEDS_PER_RUN = 1_000_000
GATE_SEEDS = 500_000
RATING_SEEDS = 900_000


def arguments(given: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m ai.value.loop", description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, default=ai.value.RUNS_FOLDER / "main", help="the run's folder")
    parser.add_argument("--rounds", type=int, default=1_000, help="rounds in all, then stop (default 1,000)")
    parser.add_argument("--minutes", type=float, help="start no step after this many minutes")
    parser.add_argument("--register", action="store_true", help="copy the best version to .cache/models/value.pt")
    parser.add_argument("--policy", type=Path, default=ai.imitation.MODEL, help="the Imitation Model")
    parser.add_argument("--dataset", type=Path, default=DATASET_FOLDER)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--warm-positions", type=int, default=1_500_000)
    parser.add_argument("--start-from", type=Path, help="a saved Value Model to start from instead of a warm start")
    parser.add_argument("--warm-learning-rate", type=float, default=1e-3)
    parser.add_argument("--warm-keep", type=float, default=0.1, help="share of each Recorded Game's positions kept")
    parser.add_argument("--validation-share", type=int, default=16, help="validate on every n-th shard")
    parser.add_argument("--games", type=int, default=120, help="Games played each round")
    parser.add_argument("--pool-bots", default="imitation,card_economy", help="registered Controllers in the pool")
    parser.add_argument("--buffer-rounds", type=int, default=3, help="rounds of Games learned from")
    parser.add_argument("--train-passes", type=int, default=1, help="passes over the kept rounds' Games each round")
    parser.add_argument("--keep", type=float, default=0.5, help="share of each of the loop's Games' positions kept")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="in each round")
    parser.add_argument("--gate-games", type=int, default=60)
    parser.add_argument("--gate-score", type=float, default=0.55)
    parser.add_argument("--panel", default="card_economy,imitation_draft_buy,imitation", help="the rating panel")
    parser.add_argument("--rating-games", type=int, default=20, help="against each Controller of the panel")
    parser.add_argument("--tried", type=int, default=TRIED, help="Options the Value Bot tries")
    parser.add_argument("--samples", type=int, default=SAMPLES, help="Sampled Positions it tries each on")
    parser.add_argument("--share", type=float, default=SHARE, help="of the likeliest Option's chance, to be tried")
    parser.add_argument("--batch", type=int, default=256)
    parser.add_argument("--workers", type=int, default=8, help="processes making training batches (0: this one)")
    parser.add_argument("--processes", type=int, default=10, help="processes playing Games")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args(given)


def settings_of(given: argparse.Namespace) -> dict[str, Any]:
    """The run's fixed settings, as saved in run.json and with each model."""
    settings = {name: value for name, value in vars(given).items() if name not in CHANGEABLE}
    return {name: str(value) if isinstance(value, Path) else value for name, value in settings.items()}


def provenance(policy: Path) -> dict[str, Any]:
    """What else a repeat of the run needs: the engine's version, the commit of the code, the encoding, and a hash of
    the Imitation Model's file (`policy`), which the settings name only by its path."""

    def git(*command: str) -> str:
        ran = subprocess.run(["git", *command], capture_output=True, text=True, cwd=REPOSITORY, check=False)
        return ran.stdout.strip()

    return {
        "engine": importlib.metadata.version("tm_engine"),
        "commit": git("rev-parse", "HEAD") or "unknown",
        "uncommitted_changes": bool(git("status", "--porcelain")),
        "format": format_stamp(),
        "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "torch": str(torch.__version__),
    }


def expected_score(rating: float, other: float) -> float:
    return 1 / (1 + 10 ** ((other - rating) / 400))


def rating_against(results: list[tuple[float, float, int]]) -> float:
    """The Elo rating that best explains a score of `points` in `games` against opponents rated `other`, for each
    (other, points, games); with one drawn Game against a Controller rated 0 added, so that a clean sweep stays
    finite."""
    results = [*results, (0.0, 0.5, 1)]
    low, high = -3_000.0, 3_000.0
    for _ in range(60):
        middle = (low + high) / 2
        surplus = sum(points - games * expected_score(middle, other) for other, points, games in results)
        low, high = (middle, high) if surplus > 0 else (low, middle)
    return (low + high) / 2


def panel_ratings(names: list[str], matches: list[dict[str, Any]]) -> dict[str, float]:
    """Ratings of the panel's Controllers from their Matches against each other, with the anchor at 0."""
    anchor = ANCHOR if ANCHOR in names else names[0]
    ratings = dict.fromkeys(names, 0.0)
    for _ in range(50):
        for name in names:
            if name == anchor:
                continue
            found = [(ratings[m["b"]], m["points"], m["games"]) for m in matches if m["a"] == name]
            found += [(ratings[m["a"]], m["games"] - m["points"], m["games"]) for m in matches if m["b"] == name]
            ratings[name] = rating_against(found)
    return ratings


def budgeted(
    make: Callable[[int], Iterator[list[ValueSample]]], positions: int | None = None, passes: int = 1_000_000
) -> Iterator[list[ValueSample]]:
    """Batches from `make(pass_number)`, pass after pass, until `positions` (if given) have been given or `passes`
    made."""
    given = 0
    for number in range(passes):
        made = make(number)
        found = False
        try:
            for batch in made:
                found = True
                yield batch
                given += len(batch)
                if positions is not None and given >= positions:
                    return
        finally:
            made.close()  # type: ignore[attr-defined]
        if not found:
            return


class Loop:
    """One run of the loop, in its folder."""

    def __init__(self, given: argparse.Namespace) -> None:
        self.given = given
        self.folder: Path = given.run
        self.settings = settings_of(given)
        self.state: dict[str, Any] = {"done": [], "best": "v000", "pool": [], "rounds": [], "ratings": [], "minutes": 0}
        if (self.folder / "state.json").exists():
            self.state = json.loads((self.folder / "state.json").read_text())

    # Where things are.

    def model_path(self, version: str) -> Path:
        return self.folder / "versions" / f"{version}.pt"

    def games_path(self, number: int) -> Path:
        return self.folder / "games" / f"round-{number:03}.jsonl.gz"

    def maker(self, name: str) -> Maker:
        """A Controller by name: a version of this run, or a registered Controller."""
        if self.model_path(name).exists():
            given = self.given
            return functools.partial(ValueBot, self.model_path(name), given.tried, given.samples, given.share)
        return functools.partial(make_controller, name)

    def first_seed(self, offset: int) -> int:
        return SEEDS_PER_RUN * (self.given.seed + 1) + offset

    # Saving.

    def write_json(self, name: str, data: Any) -> None:
        path = self.folder / name
        partial = path.with_name(path.name + ".partial")
        partial.write_text(json.dumps(data, indent=1))
        partial.replace(path)

    def save_state(self) -> None:
        self.write_json("state.json", self.state)
        lines = ["round\tversion\taccepted\tminutes\trating\t" + "\t".join(self.panel())]
        for row in self.state["ratings"]:
            shown = [str(row["round"]), row["version"], str(row["accepted"])]
            shown += [f"{row['minutes']:.1f}", f"{row['rating']:.0f}"]
            shown += [f"{row['scores'][name]:.3f}" for name in self.panel()]
            lines.append("\t".join(shown))
        partial = self.folder / "ratings.tsv.partial"
        partial.write_text("\n".join(lines) + "\n")
        partial.replace(self.folder / "ratings.tsv")

    def save_version(self, path: Path, model: ValueModel, **saved: Any) -> None:
        save_model(path, model, {"settings": self.settings, "provenance": provenance(self.given.policy), **saved})

    # The steps.

    def steps(self) -> Iterator[tuple[str, Callable[[], None]]]:
        yield "warm start", self.warm_start
        yield "panel", self.rate_panel
        yield "rate v000", lambda: self.rate(0, "v000", accepted=True)
        for number in range(1, self.given.rounds + 1):
            yield f"play {number}", functools.partial(self.play, number)
            yield f"train {number}", functools.partial(self.train, number)
            yield f"gate {number}", functools.partial(self.gate, number)
            yield f"rate {number}", functools.partial(self.rate_candidate, number)

    def warm_start(self) -> None:
        given = self.given
        if given.start_from is not None:
            model = load_model(given.start_from, given.device, kind=ValueModel)[0]
            self.save_version(self.model_path("v000"), model, version="v000", started_from=str(given.start_from))
            print(f"warm start: v000 is {given.start_from}", flush=True)
            return
        torch.manual_seed(given.seed)
        model = warm_started(given.policy).to(given.device)
        found = shards(given.dataset)

        def made(number: int) -> Iterator[list[ValueSample]]:
            seed = random.Random(f"{given.seed}:warm:{number}").randrange(2**32)
            return sample_batches(
                found,
                "train",
                workers=given.workers,
                seed=seed,
                size=given.batch,
                buffer=SHUFFLE_BUFFER,
                keep=given.warm_keep,
            )

        trained = fit(
            model,
            budgeted(made, given.warm_positions),
            learning_rate=given.warm_learning_rate,
            device=given.device,
            budget=given.warm_positions,
        )
        validation = measured(
            model,
            budgeted(
                lambda _: sample_batches(
                    found[:: given.validation_share],
                    "validation",
                    workers=min(given.workers, 4),
                    seed=0,
                    size=given.batch,
                    buffer=given.batch,
                    keep=given.warm_keep,
                ),
                VALIDATION_POSITIONS,
                passes=1,
            ),
            given.device,
        )
        print(
            f"warm start: {trained['positions']:,} positions of Recorded Games, train loss {trained['loss']:.4f}; "
            f"validation loss {validation['loss']:.4f}, the winner rated likelier at {validation['accuracy']:.1%} of "
            f"{validation['positions']:,} positions",
            flush=True,
        )
        self.save_version(self.model_path("v000"), model, version="v000", trained=trained, validation=validation)

    def panel(self) -> list[str]:
        return self.given.panel.split(",")

    def match(self, a: str, b: str, games: int, first_seed: int) -> MatchResult:
        return run_match(
            a,
            b,
            games,
            first_seed,
            processes=self.given.processes,
            settings=MatchSettings(failures_folder=self.folder / "match-failures"),
            makers=(self.maker(a), self.maker(b)),
        )

    def rate_panel(self) -> None:
        names, matches = self.panel(), []
        for first, a in enumerate(names):
            for b in names[first + 1 :]:
                played = self.match(a, b, self.given.rating_games, self.first_seed(RATING_SEEDS))
                side = played.sides[0]
                matches.append({"a": a, "b": b, "points": side.score * side.finished, "games": side.finished})
        self.state["panel"] = panel_ratings(names, matches)
        self.state["panel_matches"] = matches
        print(
            "panel: " + ", ".join(f"{name} {rating:+.0f}" for name, rating in self.state["panel"].items()), flush=True
        )

    def rate(self, number: int, version: str, *, accepted: bool) -> None:
        """Rates `version` against the panel, on the same seeds for every version."""
        scores, results = {}, []
        for name in self.panel():
            side = self.match(version, name, self.given.rating_games, self.first_seed(RATING_SEEDS)).sides[0]
            scores[name] = side.score
            results.append((self.state["panel"][name], side.score * side.finished, side.finished))
        row = {
            "round": number,
            "version": version,
            "accepted": accepted,
            "minutes": self.state["minutes"],
            "rating": rating_against(results),
            "scores": scores,
        }
        self.state["ratings"].append(row)
        shown = ", ".join(f"{name} {score:.0%}" for name, score in scores.items())
        print(f"rating of {version} (round {number}): {row['rating']:+.0f}; against {shown}", flush=True)

    def play(self, number: int) -> None:
        best, given = self.state["best"], self.given
        opponents = [version for version in self.state["pool"] if version != best]
        opponents += given.pool_bots.split(",")
        against_itself = given.games // 4 * 2
        counts = dict.fromkeys(opponents, 0)
        turn, left = number % len(opponents), given.games - against_itself
        while left >= 2:
            counts[opponents[turn]] += 2
            left -= 2
            turn = (turn + 1) % len(opponents)
        lines, scores = [], {}
        for offset, (opponent, games) in enumerate([(best, against_itself), *counts.items()]):
            if not games:
                continue
            played = self.match(best, opponent, games, self.first_seed(number * 1_000 + offset * 100))
            scores[opponent] = played.sides[0].score
            for game in played.finished:
                results, margins = results_of(game.scores)
                lines.append(json.dumps({"replay": game.replay, "results": results, "margins": margins}))
        path = self.games_path(number)
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(path.name + ".partial")
        with gzip.open(partial, "wt", encoding="utf-8") as file:
            file.writelines(line + "\n" for line in lines)
        partial.replace(path)
        self.state["rounds"].append({"round": number, "best": best, "games": len(lines), "scores": scores})
        shown = ", ".join(f"{name} {score:.0%}" for name, score in scores.items())
        print(f"round {number}: {best} played {len(lines)} Games; it scored against {shown}", flush=True)

    def train(self, number: int) -> None:
        given = self.given
        torch.manual_seed(given.seed * 1_000 + number)
        model = load_model(self.model_path(self.state["best"]), given.device, kind=ValueModel)[0]
        kept = [self.games_path(n) for n in range(max(1, number - given.buffer_rounds + 1), number + 1)]
        kept = [path for path in kept if path.exists()]

        def made(pass_number: int) -> Iterator[list[ValueSample]]:
            seed = random.Random(f"{given.seed}:{number}:{pass_number}").randrange(2**32)
            return sample_batches(
                kept,
                "train",
                workers=given.workers,
                seed=seed,
                size=given.batch,
                buffer=SHUFFLE_BUFFER,
                keep=given.keep,
            )

        trained = fit(
            model, budgeted(made, passes=given.train_passes), learning_rate=given.learning_rate, device=given.device
        )
        version = f"candidate-{number:03}"
        self.save_version(self.model_path(version), model, version=version, round=number, trained=trained)
        self.round(number)["trained"] = trained
        for old in self.folder.glob("games/round-*.jsonl.gz"):
            if int(old.name[6:9]) <= number - given.buffer_rounds:
                old.unlink()
        print(f"round {number}: trained on {trained['positions']:,} positions, loss {trained['loss']:.4f}", flush=True)

    def round(self, number: int) -> dict[str, Any]:
        return next(found for found in self.state["rounds"] if found["round"] == number)

    def gate(self, number: int) -> None:
        candidate, best = f"candidate-{number:03}", self.state["best"]
        side = self.match(candidate, best, self.given.gate_games, self.first_seed(GATE_SEEDS + number * 1_000)).sides[0]
        accepted = side.finished > 0 and side.score >= self.given.gate_score
        if accepted:
            version = f"v{number:03}"
            shutil.copyfile(self.model_path(candidate), self.model_path(version))
            self.state["pool"].append(best)
            self.state["best"] = version
        self.round(number)["gate"] = {"score": side.score, "games": side.finished, "accepted": accepted}
        verdict = f"accepted as {self.state['best']}" if accepted else f"rejected; {best} stays the best"
        print(f"round {number}: {candidate} scored {side.score:.1%} against {best}: {verdict}", flush=True)

    def rate_candidate(self, number: int) -> None:
        self.rate(number, f"candidate-{number:03}", accepted=self.round(number)["gate"]["accepted"])


def main(given_arguments: Sequence[str] | None = None) -> int:
    given = arguments(given_arguments)
    loop = Loop(given)
    loop.folder.mkdir(parents=True, exist_ok=True)
    run_file = loop.folder / "run.json"
    if run_file.exists():
        saved = json.loads(run_file.read_text())["settings"]
        differing = [
            name for name in sorted(set(saved) | set(loop.settings)) if saved.get(name) != loop.settings.get(name)
        ]
        if differing:
            print(
                f"{loop.folder} was started with other settings ({', '.join(differing)}): give the same ones, or "
                "another --run",
                file=sys.stderr,
            )
            return WRONG_ARGUMENTS
    else:
        loop.write_json("run.json", {"settings": loop.settings, "provenance": provenance(given.policy)})
    if given.register:
        best = loop.model_path(loop.state["best"])
        ai.value.MODEL.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(best, ai.value.MODEL)
        print(f"registered {best} as {ai.value.MODEL}")
        return 0
    started = time.time()
    for name, step in loop.steps():
        if name in loop.state["done"]:
            continue
        if given.minutes is not None and time.time() - started >= given.minutes * 60:
            print(f"stopped after {given.minutes:g} minutes, before {name}: give the same command to go on", flush=True)
            return 0
        print(f"{name}…", flush=True)
        step_started = time.time()
        step()
        loop.state["minutes"] += (time.time() - step_started) / 60
        loop.state["done"].append(name)
        loop.save_state()
    print(f"done: {given.rounds} rounds; the best version is {loop.state['best']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

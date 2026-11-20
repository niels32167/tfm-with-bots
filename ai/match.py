"""The Match tool: two Controllers play a Match, and it reports how they did.

    uv run python -m ai.match random_bot random_bot --games 1000
    uv run python -m ai.match my_bot random_bot --games 400 --threshold 0.5
    uv run python -m ai.match ai.random_bot:RandomBot random_bot --games 20 --no-prelude

A Controller is named as registered in ai.controllers, or as "module:attribute" to try one out. N Games
are played on N/2 seeds from --first-seed, and each seed is played both ways, so that each Controller
takes each Player. Games are 2-player, with Corporations, and with the Draft and Prelude (ADR 0011)
unless told otherwise. They run in worker processes on all cores.

It reports each Controller's win rate with a 95% interval, its mean Victory Points, card Victory
Points and Terraform Rating, the mean Generations, and how often Player 1 and the first player won.
A draw counts as half a win. A Game still going after the pick limit is stalled, and counts towards
neither win rate. Stalled Games and Games that went wrong are saved as Replay files in
match-failures/. The GUI's Load Replay… opens those between registered Controllers; it refuses
"module:attribute" names, as loading a file must never import code it names.

The exit status is 0, 1 if --threshold is given and the low end of the first Controller's interval
is not above it, so that a step up the ladder can be checked by a command (ADR 0013), 2 for wrong
arguments, and 3 if a Game went wrong.

The same seeds and Controllers give the same results, for Controllers that draw random numbers only
from the random source their handle gives them.
"""

import argparse
import json
import math
import os
import random
import re
import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from itertools import repeat
from pathlib import Path
from typing import Any, Literal

import tm_engine

from ai.controller import Controller, handle_for, offered
from ai.controllers import make_controller

PLAYERS = 2
FAILURES_FOLDER = Path(__file__).parents[1] / "match-failures"

# A guard, not a rule: 2-player Random Bot Games with Prelude take about 530 picks, and few take
# more than 1,500. A Controller that stops the Game from ending is caught here.
PICK_LIMIT = 5_000

# For the 95% interval.
Z = 1.959964

# The exit statuses.
THRESHOLD_MISSED = 1
A_GAME_FAILED = 3

type Outcome = Literal["over", "stalled", "failed"]

# Makes a new Controller for one Player in one Game.
type Maker = Callable[[], Controller]


@dataclass(frozen=True)
class MatchSettings:
    """How each Game of a Match is set up, and the guard and folder for Games that don't end well."""

    draft: bool = True
    prelude: bool = True
    pick_limit: int = PICK_LIMIT
    failures_folder: Path = FAILURES_FOLDER

    def description(self) -> str:
        parts = [f"{PLAYERS} Players", "Corporations"]
        parts += [name for name, on in [("Draft", self.draft), ("Prelude", self.prelude)] if on]
        return f"{', '.join(parts)}; pick limit {self.pick_limit:,}"


@dataclass(frozen=True)
class GameResult:
    """One Game of a Match. `controllers` names each Player's Controller, and `sides` says which side
    of the Match each Player is: 0 for the first Controller named, 1 for the second. `scores` are the
    engine's, once the Game is over. `problem` says what went wrong in a failed Game; its Replay
    stops just before the pick that did."""

    seed: int
    controllers: tuple[str, str]
    sides: tuple[int, int]
    outcome: Outcome
    replay: dict[str, Any]
    generations: int
    first_player: int
    scores: list[dict[str, Any]] | None = None
    problem: str | None = None

    def player_of(self, side: int) -> int:
        return self.sides.index(side)

    def winners(self) -> list[int]:
        """The Players ranked first: one, or two in a draw; none while the Game isn't over."""
        return [score["player"] for score in self.scores or [] if score["rank"] == 1]


@dataclass(frozen=True)
class Side:
    """How one Controller did over the finished Games of a Match."""

    name: str
    wins: int
    draws: int
    losses: int
    mean_points: float
    mean_card_points: float
    mean_terraform_rating: float

    @property
    def finished(self) -> int:
        return self.wins + self.draws + self.losses

    @property
    def score(self) -> float:
        """The win rate, a draw counting as half a win."""
        return (self.wins + self.draws / 2) / self.finished if self.finished else 0.0

    @property
    def interval(self) -> tuple[float, float]:
        """The 95% (Wilson) interval on the win rate."""
        return wilson_interval(self.score, self.finished)

    def above(self, threshold: float) -> bool:
        """Whether the low end of the interval is above `threshold`: the test of a step up the ladder."""
        return self.interval[0] > threshold


@dataclass(frozen=True)
class MatchResult:
    controllers: tuple[str, str]
    settings: MatchSettings
    games: tuple[GameResult, ...]
    sides: tuple[Side, Side] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "sides", tuple(side_of(self.controllers[side], side, self.finished) for side in (0, 1))
        )

    @property
    def finished(self) -> list[GameResult]:
        return [game for game in self.games if game.outcome == "over"]

    @property
    def stalled(self) -> int:
        return sum(game.outcome == "stalled" for game in self.games)

    @property
    def failed(self) -> int:
        return sum(game.outcome == "failed" for game in self.games)


def wilson_interval(rate: float, games: int) -> tuple[float, float]:
    if games == 0:
        return (0.0, 1.0)
    denominator = 1 + Z**2 / games
    centre = (rate + Z**2 / (2 * games)) / denominator
    half = Z * math.sqrt(rate * (1 - rate) / games + Z**2 / (4 * games**2)) / denominator
    return (max(0.0, centre - half), min(1.0, centre + half))


def side_of(name: str, side: int, finished: list[GameResult]) -> Side:
    wins = draws = losses = 0
    points = card_points = terraform_rating = 0
    for game in finished:
        player = game.player_of(side)
        winners = game.winners()
        if player not in winners:
            losses += 1
        elif len(winners) == 1:
            wins += 1
        else:
            draws += 1
        score = game.scores[player]
        points += score["total"]
        card_points += score["cards"]
        terraform_rating += score["terraform_rating"]
    count = max(len(finished), 1)
    return Side(name, wins, draws, losses, points / count, card_points / count, terraform_rating / count)


@dataclass(frozen=True)
class Claim:
    """A Milestone claimed or an Award funded: which, by which Player (from 0), in which Generation, and for an
    Award, whether its funder lost it: another Player had more at the end (a tie for first is no loss)."""

    name: str
    player: int
    generation: int
    lost: bool | None = None


@dataclass(frozen=True)
class GameSummary:
    """What box 4 of ticket 14 compares between the Imitation Bot's Games against itself and Players' Games."""

    generations: int
    scores: list[dict[str, Any]]
    milestones: list[Claim]
    awards: list[Claim]


def game_summary(replay: dict[str, Any]) -> GameSummary:
    """A Replay (its start and picks) played through the engine: its Generations, the engine's scores, and each
    Milestone claimed and Award funded with its Generation, from the pick that claims or funds it."""
    game = tm_engine.Game.from_replay({"start": replay["start"], "picks": []})
    milestones: list[Claim] = []
    funded: list[tuple[str, int, int]] = []
    for picked in replay["picks"]:
        decision = game.decision
        details = decision["options"][picked]["details"]
        if details["type"] in ("claim_milestone", "fund_award"):
            generation = game.player_view(decision["player"])["generation"]
            if details["type"] == "claim_milestone":
                milestones.append(Claim(details["milestone"], decision["player"], generation))
            else:
                funded.append((details["award"], decision["player"], generation))
        game.pick(picked)
    view = game.full_view()
    counts = {award["award"]: award["counts"] for award in view["awards"]}
    awards = [
        Claim(award, player, generation, lost=counts[award][player] < max(counts[award]))
        for award, player, generation in funded
    ]
    return GameSummary(view["generation"], game.scores, milestones, awards)


def views_along(
    replay: dict[str, Any], viewer: Callable[[dict[str, Any]], int | None]
) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    """At each Decision of a Replay, before its pick, the Decision and the Player View of the Player that
    `viewer(decision)` names, or nothing if it names none: what the Value Model learns from (ai.value), one Player's
    view of positions of a past Game."""
    game = tm_engine.Game.from_replay({"start": replay["start"], "picks": []})
    for picked in replay["picks"]:
        decision = game.decision
        player = viewer(decision)
        if player is not None:
            yield decision, game.player_view(player)
        game.pick(picked)


def play_game(
    seed: int,
    controllers: tuple[str, str],
    sides: tuple[int, int],
    settings: MatchSettings,
    makers: tuple[Maker, Maker] | None = None,
) -> GameResult:
    """Plays one Game of a Match, Player 1 answered by `controllers[0]` and Player 2 by `controllers[1]`,
    made by name, or by `makers` for each Player if given. Each Controller's random source is seeded by
    the seed, its side and its Player, so that a Controller playing itself doesn't play the same Game
    twice on a seed."""
    game = tm_engine.Game(seed=seed, players=PLAYERS, draft=settings.draft, prelude=settings.prelude)
    start = game.replay["start"]
    first_player = game.player_view(0)["first_player"]
    answering = [make() for make in makers] if makers else [make_controller(name) for name in controllers]
    random_sources = [random.Random(f"{seed}/{side}/{player}") for player, side in enumerate(sides)]
    picks: list[int] = []
    outcome: Outcome = "stalled"
    problem = None
    while len(picks) < settings.pick_limit:
        decision = game.decision
        if decision is None:
            outcome = "over"
            break
        player = decision["player"]
        problem = answer(game, answering[player], controllers[player], random_sources[player], picks)
        if problem is not None:
            outcome = "failed"
            break
    else:
        if game.decision is None:
            outcome = "over"
    if outcome == "stalled":
        problem = f"the Game was still going after {settings.pick_limit:,} picks"
    result = GameResult(
        seed=seed,
        controllers=controllers,
        sides=sides,
        outcome=outcome,
        replay={"start": start, "picks": picks},
        generations=game.player_view(0)["generation"],
        first_player=first_player,
        scores=game.scores,
        problem=problem,
    )
    if outcome != "over":
        save_replay_file(result, settings.failures_folder)
    return result


def answer(
    game: tm_engine.Game, controller: Controller, name: str, random_source: random.Random, picks: list[int]
) -> str | None:
    """Has `controller` answer the Decision `game` is waiting on and picks its Option. Returns what
    went wrong, if anything; then the pick is not made."""
    decision = game.decision
    try:
        index = controller.pick(handle_for(game, random_source))
    except Exception as error:  # noqa: BLE001 - whatever a Controller raises fails its Game, not the Match.
        return f"{name} raised {type(error).__name__} answering a {decision['kind']} Decision: {error}"
    options = decision["options"]
    if not offered(decision, index):
        return f"{name} picked Option {index!r} of a {decision['kind']} Decision with {len(options)} Options"
    try:
        game.pick(index, decision["sequence"])
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as error:  # noqa: BLE001 - a panic in the engine arrives as a BaseException.
        label = options[index]["label"]
        return f"the engine raised {type(error).__name__} as {name} picked Option {index} ({label}): {error}"
    picks.append(index)
    return None


def save_replay_file(game: GameResult, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    names = "-vs-".join(re.sub(r"[^A-Za-z0-9_]+", "_", name) for name in game.controllers)
    first = "a" if game.sides[0] == 0 else "b"
    path = folder / f"{names}-seed-{game.seed}-{first}-first-{game.outcome}.json"
    path.write_text(json.dumps({"controllers": list(game.controllers), "replay": game.replay, "problem": game.problem}))
    return path


def run_match(
    a: str,
    b: str,
    games: int,
    first_seed: int = 0,
    processes: int | None = None,
    settings: MatchSettings | None = None,
    on_progress: Callable[[int], None] | None = None,
    makers: tuple[Maker, Maker] | None = None,
) -> MatchResult:
    """Plays a Match of `games` Games between Controllers `a` and `b`, on `processes` worker processes
    (one per core by default; 1 plays them here), set up as `settings` says (the defaults if None).
    Seeds `first_seed` on are each played twice: first with `a` as Player 1, then with `b`. `on_progress`
    is told how many Games are done as they finish. With `makers`, `a` and `b` only name the
    Controllers that its two factories make, such as Card Economy Bots with weights being fitted; on
    more than one process they must pickle. Raises ValueError for an odd number of Games or an
    unknown Controller, before any Game starts."""
    if games <= 0 or games % 2:
        raise ValueError(f"a Match needs an even number of Games, at least 2, not {games}")
    for name in (a, b) if makers is None else ():
        make_controller(name)  # Unknown names are refused before any Game starts.
    names = (a, b)
    settings = settings or MatchSettings()
    seeds = [seed for seed in range(first_seed, first_seed + games // 2) for _ in (0, 1)]
    sides = [(first, 1 - first) for _ in range(games // 2) for first in (0, 1)]
    by_player = [(names[first], names[second]) for first, second in sides]
    player_makers = [(makers[first], makers[second]) if makers else None for first, second in sides]
    processes = processes or os.cpu_count() or 1
    results: list[GameResult] = []

    def collect(played: Iterable[GameResult]) -> None:
        for result in played:
            results.append(result)
            if on_progress:
                on_progress(len(results))

    if processes == 1:
        collect(map(play_game, seeds, by_player, sides, repeat(settings), player_makers))
    else:
        with ProcessPoolExecutor(processes) as pool:
            chunks = max(1, games // (processes * 8))
            played = pool.map(
                play_game, seeds, by_player, sides, repeat(settings, games), player_makers, chunksize=chunks
            )
            collect(played)
    return MatchResult(names, settings, tuple(results))


def percent(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def report(match: MatchResult, threshold: float | None = None) -> str:
    a, b = match.sides
    finished = match.finished
    seeds = sorted({game.seed for game in match.games})

    def row(label: str, values: Sequence[str]) -> str:
        return f"  {label:28}{values[0]:>20}{values[1]:>20}"

    def share(count: int) -> str:
        return percent(count / len(finished)) if finished else "-"

    player_1_won = sum(game.winners() == [0] for game in finished)
    player_2_won = sum(game.winners() == [1] for game in finished)
    first_player_won = sum(game.winners() == [game.first_player] for game in finished)
    generations = sum(game.generations for game in finished) / len(finished) if finished else 0.0
    lines = [
        (
            f"Match: {a.name} (a) against {b.name} (b), {len(match.games):,} Games on seeds {seeds[0]} to "
            f"{seeds[-1]}, each played both ways."
        ),
        f"Settings: {match.settings.description()}.",
        "",
        row("", [f"a: {a.name}", f"b: {b.name}"]),
        row("Win rate", [percent(a.score), percent(b.score)]),
        row("  95% interval", [f"{percent(s.interval[0])}–{percent(s.interval[1])}" for s in (a, b)]),
        row("Wins / draws / losses", [f"{s.wins} / {s.draws} / {s.losses}" for s in (a, b)]),
        row("Mean Victory Points", [f"{s.mean_points:.1f}" for s in (a, b)]),
        row("Mean card Victory Points", [f"{s.mean_card_points:.1f}" for s in (a, b)]),
        row("Mean Terraform Rating", [f"{s.mean_terraform_rating:.1f}" for s in (a, b)]),
        "",
        f"Mean Generations: {generations:.2f}",
        (
            f"Player 1 won {share(player_1_won)} of finished Games, Player 2 {share(player_2_won)}; "
            f"the first player won {share(first_player_won)}."
        ),
        f"Finished: {len(finished):,}, stalled: {match.stalled:,}, failed: {match.failed:,}.",
    ]
    problems = [game for game in match.games if game.outcome != "over"]
    if problems:
        lines.append(f"Saved as Replay files in {match.settings.failures_folder}:")
        lines += [f"  seed {game.seed}, {' vs '.join(game.controllers)}: {game.problem}" for game in problems[:20]]
    if threshold is not None:
        verdict = "met" if a.above(threshold) else "NOT met"
        lines += ["", f"Threshold: the low end of a's interval must be above {percent(threshold)}: {verdict}."]
    return "\n".join(lines)


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ai.match", description=__doc__.splitlines()[0])
    parser.add_argument("a", help="the first Controller: a registered name, or module:attribute")
    parser.add_argument("b", help="the second Controller")
    parser.add_argument("--games", type=int, default=1_000, help="how many Games, an even number (default 1,000)")
    parser.add_argument("--first-seed", type=int, default=0, help="the first seed (default 0)")
    parser.add_argument("--processes", type=int, help="worker processes (default: 1 per core)")
    parser.add_argument("--threshold", type=float, help="exit with status 1 unless a's interval is above this")
    parser.add_argument("--pick-limit", type=int, default=PICK_LIMIT, help=f"(default {PICK_LIMIT:,})")
    parser.add_argument("--no-draft", action="store_true", help="play without the Draft")
    parser.add_argument("--no-prelude", action="store_true", help="play without Prelude")
    parser.add_argument("--failures-folder", type=Path, default=FAILURES_FOLDER, help="(default match-failures/)")
    parsed = parser.parse_args(arguments)
    settings = MatchSettings(
        draft=not parsed.no_draft,
        prelude=not parsed.no_prelude,
        pick_limit=parsed.pick_limit,
        failures_folder=parsed.failures_folder,
    )
    reported = 0

    def show_progress(done: int) -> None:
        nonlocal reported
        if done - reported >= max(parsed.games // 10, 1) and done < parsed.games:
            reported = done
            print(f"  {done:,} of {parsed.games:,} Games played", file=sys.stderr, flush=True)

    try:
        match = run_match(
            parsed.a, parsed.b, parsed.games, parsed.first_seed, parsed.processes, settings, on_progress=show_progress
        )
    except ValueError as error:
        parser.error(str(error))
    print(report(match, parsed.threshold))
    if match.failed:
        return A_GAME_FAILED
    if parsed.threshold is not None and not match.sides[0].above(parsed.threshold):
        return THRESHOLD_MISSED
    return 0


if __name__ == "__main__":
    sys.exit(main())

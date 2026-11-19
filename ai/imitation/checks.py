"""Checks of what the Imitation Model learned (tickets 13 and 14 of phase 2):

- Keep rates (box 5): each card's share kept at setup when dealt, by the model buying through the whole chain of
  buy Decisions itself (with the Corporation and Prelude Cards the Player chose), beside Players' share. The
  Players' shares are the dataset's, which ticket 08 checked against tfmstats.com's Starting Hand page.
- Synergies (box 6): for a Corporation and a Prelude Card, the model's chance of choosing the Corporation with the
  Prelude Card among those dealt and without it, and its chance of keeping the Prelude Card (first or second) with
  the Corporation chosen and with another. Each setup record is a probe: the pair is put into its offer, or taken out
  and replaced by a stand-in (the first card of its kind in the catalog that the offer lacks).

- Self-play (ticket 14, box 4): a registered Controller's Games against itself beside Players' (rated at least
  --min-rating, Games with Prelude not conceded and replayed fully through the engine): Generations, Victory Points
  and card Victory Points, each Milestone claimed and Award funded and in which Generation, and the flip rate, how
  often a funder lost the Award they funded. tfmstats.com's flip rate would need the site; the dataset's comes from
  the replays' final scoring (the spec's "When tfmstats.com doesn't answer").

    uv run python -m ai.imitation.checks keep-rates --model .cache/models/imitation.pt
    uv run python -m ai.imitation.checks synergies --pairs credicor:allied_banks,helion:...
    uv run python -m ai.imitation.checks self-play --games 200 --processes 6 --most-games 4000
"""

import argparse
import copy
import itertools
import sys
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from ai.controller import card_catalog
from ai.imitation import MODEL
from ai.imitation.evaluate import Scorer
from ai.imitation.model import collate, load_model, scored
from ai.imitation.positions import encoded
from ai.imitation.split import split_of
from ai.match import Claim, GameSummary, game_summary, run_match
from ai.recorded_games.dataset import DATASET_FOLDER, read_games, read_shard, shards
from ai.recorded_games.records import recorded_decisions

# Cards dealt at setup, and so a guard on the buying chain.
CARDS_DEALT = 10
MOST_BUYS = CARDS_DEALT
# Cards dealt fewer times than this are left out of the keep-rate comparison.
FEWEST_DEALT = 100

type Counts = dict[str, tuple[int, int]]


@dataclass(frozen=True)
class MilestoneRate:
    """How often a Milestone is claimed per Game, and the mean Generation it is claimed in."""

    per_game: float = 0.0
    generation: float = float("nan")


@dataclass(frozen=True)
class AwardRate:
    """How often an Award is funded per Game, the mean Generation it is funded in, and the share its funder lost."""

    per_game: float = 0.0
    generation: float = float("nan")
    lost: float = float("nan")


@dataclass(frozen=True)
class Benchmark:
    """Means over Games: Generations, and a Player's Victory Points and card Victory Points. For each Milestone,
    claims per Game and the mean Generation; for each Award, funded per Game, the mean Generation and the share its
    funder lost; and the flip rate, the share of all Awards funded that their funder lost."""

    games: int
    generations: float
    points: float
    card_points: float
    milestones: dict[str, MilestoneRate]
    awards: dict[str, AwardRate]
    flip_rate: float


def benchmark(summaries: Iterable[GameSummary]) -> Benchmark:
    games = list(summaries)
    per_game = 1 / max(len(games), 1)
    scores = [score for game in games for score in game.scores]
    milestones: dict[str, list[Claim]] = defaultdict(list)
    awards: dict[str, list[Claim]] = defaultdict(list)
    for game in games:
        for claim in game.milestones:
            milestones[claim.name].append(claim)
        for claim in game.awards:
            awards[claim.name].append(claim)
    funded = [claim for claims in awards.values() for claim in claims]
    return Benchmark(
        games=len(games),
        generations=mean_of(game.generations for game in games),
        points=mean_of(score["total"] for score in scores),
        card_points=mean_of(score["cards"] for score in scores),
        milestones={
            name: MilestoneRate(len(claims) * per_game, mean_of(claim.generation for claim in claims))
            for name, claims in sorted(milestones.items())
        },
        awards={
            name: AwardRate(
                len(claims) * per_game,
                mean_of(claim.generation for claim in claims),
                mean_of(float(bool(claim.lost)) for claim in claims),
            )
            for name, claims in sorted(awards.items())
        },
        flip_rate=mean_of(float(bool(claim.lost)) for claim in funded),
    )


def players_games(folder: Path, min_rating: int) -> Iterator[GameSummary]:
    """Players' Games with Prelude, not conceded, replayed fully, with both Players rated at least `min_rating`."""
    for shard in shards(folder):
        replays = {record["game"]: record for record in read_shard(shard, "replays.jsonl.gz") if record["complete"]}
        for game in read_shard(shard, "games.jsonl.gz"):
            rated = all((board["rating"] or 0) >= min_rating for board in game["players"])
            if game["prelude"] and not game["conceded"] and rated and game["game"] in replays:
                yield game_summary(replays[game["game"]]["replay"])


def benchmark_table(columns: dict[str, Benchmark]) -> str:
    def row(label: str, values: Iterable[str]) -> str:
        return f"{label:<34}" + "".join(f"{value:>32}" for value in values)

    found = list(columns.values())
    lines = [row("", columns), row("Games", (f"{b.games:,}" for b in found))]
    lines.append(row("Generations", (f"{b.generations:.1f}" for b in found)))
    lines.append(row("Victory Points (a Player)", (f"{b.points:.1f}" for b in found)))
    lines.append(row("card Victory Points (a Player)", (f"{b.card_points:.1f}" for b in found)))
    lines.append(row("Awards funded, lost (flip rate)", (f"{b.flip_rate:.1%}" for b in found)))
    lines.append("Milestones: claimed per Game, mean Generation")
    for name in sorted({name for b in found for name in b.milestones}):
        cells = (b.milestones.get(name, MilestoneRate()) for b in found)
        lines.append(row(f"  {name}", (f"{c.per_game:.2f}, Generation {c.generation:.1f}" for c in cells)))
    lines.append("Awards: funded per Game, mean Generation, share lost")
    for name in sorted({name for b in found for name in b.awards}):
        cells = (b.awards.get(name, AwardRate()) for b in found)
        lines.append(
            row(f"  {name}", (f"{c.per_game:.2f}, Generation {c.generation:.1f}, {c.lost:.0%}" for c in cells))
        )
    return "\n".join(lines)


def self_play_report(given: argparse.Namespace) -> int:
    match = run_match(given.controller, given.controller, given.games, processes=given.processes)
    print(
        f"{given.controller} against itself: {len(match.finished)} finished, {match.stalled} stalled, {match.failed} failed"
    )
    columns = {
        f"{given.controller} (self-play)": benchmark(game_summary(game.replay) for game in match.finished),
        f"Players rated {given.min_rating}+": benchmark(
            itertools.islice(players_games(given.dataset, given.min_rating), given.most_games)
        ),
    }
    print(benchmark_table(columns))
    return 0


def mean_of(values: Iterable[float]) -> float:
    found = list(values)
    return sum(found) / len(found) if found else float("nan")


def setup_records(games: Iterable[dict[str, Any]]) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    """Each Game's setup records, with their Game."""
    for game in games:
        for record in game["decisions"]:
            if record["kind"] == "setup":
                yield game, record


def setup_chain(game: dict[str, Any], record: dict[str, Any]) -> list[dict[str, Any]]:
    """The Decisions of one setup record alone, from the records' own source."""
    return [{**decision, "source": "records"} for decision in recorded_decisions({**game, "decisions": [record]})]


def chances(scorer: Scorer, game: dict[str, Any], decision: dict[str, Any]) -> list[float]:
    """The scorer's chance of each Option of `decision`."""
    with torch.no_grad():
        scores = scorer(collate([encoded(game, decision)]))[0]
    return torch.softmax(scores.float(), dim=0).tolist()


def players_keep_rates(games: Iterable[dict[str, Any]]) -> Counts:
    """For each card, the times it was dealt at setup and the times its Player kept it."""
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for _, record in setup_records(games):
        for card in record["offer"]["cards"]:
            counts[card][0] += 1
            counts[card][1] += card in record["picked"]["cards"]
    return {card: (dealt, kept) for card, (dealt, kept) in counts.items()}


def model_keep_rates(scorer: Scorer, games: Iterable[dict[str, Any]]) -> Counts:
    """For each card, the times it was dealt at setup and the times the model kept it, buying card after card until
    it picks done or can't pay for another."""
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for game, record in setup_records(games):
        bought: list[str] = []
        for _ in range(MOST_BUYS + 1):
            trial = copy.deepcopy(record)
            trial["picked"]["cards"] = list(bought)
            buys = [decision for decision in setup_chain(game, trial) if decision["kind"] == "buy_cards"]
            # The last buy Decision asks for the next card; there is none if no other can be paid for.
            if not buys or len(buys) == len(bought):
                break
            asked = buys[-1]
            given = chances(scorer, game, asked)
            card = asked["options"][given.index(max(given))]["details"].get("card")
            if card is None:
                break
            bought.append(card)
        for card in record["offer"]["cards"]:
            counts[card][0] += 1
            counts[card][1] += card in bought
    return {card: (dealt, kept) for card, (dealt, kept) in counts.items()}


@dataclass(frozen=True)
class Synergy:
    """The model's mean chances over `probes` setup records, with the pair together and apart."""

    corporation: str
    prelude_card: str
    probes: int
    corporation_with: float
    corporation_without: float
    prelude_with: float
    prelude_without: float

    @property
    def learned(self) -> bool:
        """Whether the model gives each part a higher chance with the other than without."""
        return self.corporation_with > self.corporation_without and self.prelude_with > self.prelude_without


def stand_in(kind: str, offer: list[str], card: str) -> str:
    """The first card of `kind` in the catalog that `offer` lacks, other than `card`."""
    return next(
        other
        for other, printed in card_catalog().items()
        if printed["type"] == kind and other not in offer and other != card
    )


def with_card(offer: list[str], card: str, keep: Iterable[str]) -> list[str]:
    """`offer` holding `card`: in place of the first card not in `keep`, if it isn't there already."""
    if card in offer:
        return list(offer)
    kept = set(keep)
    replaced = next(index for index, other in enumerate(offer) if other not in kept)
    return [card if index == replaced else other for index, other in enumerate(offer)]


def without_card(offer: list[str], card: str, kind: str) -> list[str]:
    return [stand_in(kind, offer, card) if other == card else other for other in offer]


def chance_of(scorer: Scorer, game: dict[str, Any], record: dict[str, Any], kind: str, card: str) -> float:
    """The chance the scorer gives `card` at the first Decision of `kind` in the setup chain of `record`."""
    decision = next(decision for decision in setup_chain(game, record) if decision["kind"] == kind)
    cards = [option["details"].get("card") for option in decision["options"]]
    return chances(scorer, game, decision)[cards.index(card)]


def after_keeping(decision: dict[str, Any], card: str) -> dict[str, Any]:
    """The second Prelude Card Decision of a setup chain, once `card` is kept at the first: the same view with
    `card` kept, and the other Prelude Cards dealt to choose from."""
    kept = copy.deepcopy(decision)
    kept["view"]["players"][decision["player"]]["prelude_cards"]["kept"] = [card]
    others = [option["details"]["card"] for option in decision["options"] if option["details"]["card"] != card]
    kept["options"] = [
        {
            "index": index,
            "label": f"Keep {card_catalog()[other]['name']}",
            "details": {"type": "keep_prelude_card", "card": other},
        }
        for index, other in enumerate(others)
    ]
    kept["picked"] = 0
    return kept


def chance_kept(scorer: Scorer, game: dict[str, Any], record: dict[str, Any], card: str) -> float:
    """The chance the scorer keeps `card` among the 2 Prelude Cards kept at setup, kept first or second. Kept first
    alone would be biased: the records list kept cards in card-number order, so the model learned that order."""
    first = next(decision for decision in setup_chain(game, record) if decision["kind"] == "prelude_cards")
    cards = [option["details"]["card"] for option in first["options"]]
    seconds = [after_keeping(first, other) for other in cards if other != card]
    with torch.no_grad():
        scores = scorer(collate([encoded(game, decision) for decision in [first, *seconds]])).float()
    given = torch.softmax(scores, dim=1)
    kept_first = given[0, cards.index(card)].item()
    kept_second = 0.0
    for second, decision in enumerate(seconds, start=1):
        other = next(c for c in cards if c not in [o["details"]["card"] for o in decision["options"]])
        later = [option["details"]["card"] for option in decision["options"]]
        kept_second += given[0, cards.index(other)].item() * given[second, later.index(card)].item()
    return kept_first + kept_second


def synergy(scorer: Scorer, games: Iterable[dict[str, Any]], corporation: str, prelude_card: str) -> Synergy:
    """The model's chances for `corporation` and `prelude_card` together and apart, over the setup records of Games
    with Prelude where Prelude Cards were kept."""
    totals = dict.fromkeys(("corporation_with", "corporation_without", "prelude_with", "prelude_without"), 0.0)
    probes = 0
    for game, record in setup_records(game for game in games if game["prelude"]):
        offer, picked = record["offer"], record["picked"]
        kept = picked.get("prelude_cards") or []
        if not kept:
            continue
        # The Corporation, with the Prelude Card dealt and without it. The Player's own pick stays offered.
        corporations = with_card(offer["corporations"], corporation, (picked["corporation"],))
        for name, preludes in [
            ("corporation_with", with_card(offer["prelude_cards"], prelude_card, kept)),
            ("corporation_without", without_card(offer["prelude_cards"], prelude_card, "prelude")),
        ]:
            probe = copy.deepcopy(record)
            probe["offer"] |= {"corporations": corporations, "prelude_cards": preludes}
            probe["picked"]["prelude_cards"] = [card for card in kept if card in preludes] or preludes[:1]
            totals[name] += chance_of(scorer, game, probe, "corporation", corporation)
        # The Prelude Card, kept with the Corporation chosen and with another chosen.
        dealt = with_card(offer["prelude_cards"], prelude_card, kept)
        others = without_card(offer["corporations"], corporation, "corporation")
        for name, offered, chosen in [
            ("prelude_with", corporations, corporation),
            ("prelude_without", others, picked["corporation"] if picked["corporation"] in others else others[0]),
        ]:
            probe = copy.deepcopy(record)
            probe["offer"] |= {"corporations": offered, "prelude_cards": dealt}
            probe["picked"] |= {"corporation": chosen, "prelude_cards": [card for card in kept if card in dealt]}
            totals[name] += chance_kept(scorer, game, probe, prelude_card)
        probes += 1
    return Synergy(
        corporation, prelude_card, probes, **{name: total / max(probes, 1) for name, total in totals.items()}
    )


def held_out(folder: Path, split: str) -> Iterator[dict[str, Any]]:
    """The Games of `split` with setup records, slimmed to what the checks read."""
    for game in read_games(folder):
        if split_of(game) == split and any(record["kind"] == "setup" for record in game["decisions"]):
            yield {
                **game,
                "positions": game["positions"][:1],
                "decisions": [r for r in game["decisions"] if r["kind"] == "setup"],
            }


def keep_rate_report(model_counts: Counts, player_counts: Counts, top: int) -> str:
    rows = []
    for card, (dealt, kept) in player_counts.items():
        if dealt < FEWEST_DEALT:
            continue
        model_kept = model_counts[card][1]
        rows.append((model_kept / dealt - kept / dealt, card, dealt, kept / dealt, model_kept / dealt))
    if not rows:
        return "no card dealt often enough"
    differences = [abs(row[0]) for row in rows]
    players = [row[3] for row in rows]
    model = [row[4] for row in rows]
    correlation = torch.corrcoef(torch.tensor([players, model]))[0, 1].item()
    setups = sum(dealt for dealt, _ in player_counts.values()) / CARDS_DEALT
    lines = [
        (
            f"{len(rows)} cards dealt at least {FEWEST_DEALT} times; correlation {correlation:.3f}, "
            f"mean absolute difference {sum(differences) / len(rows):.1%}"
        ),
        (
            f"cards kept per setup: Players {sum(kept for _, kept in player_counts.values()) / setups:.2f}, "
            f"model {sum(kept for _, kept in model_counts.values()) / setups:.2f}"
        ),
        f"{'card':<36}{'dealt':>8}{'Players':>9}{'model':>8}{'difference':>12}",
    ]
    for difference, card, dealt, by_players, by_model in sorted(rows, key=lambda row: -abs(row[0]))[:top]:
        lines.append(f"{card:<36}{dealt:>8,}{by_players:>9.1%}{by_model:>8.1%}{difference:>+12.1%}")
    return "\n".join(lines)


def main(given_arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ai.imitation.checks", description=__doc__.splitlines()[0])
    parser.add_argument("check", choices=("keep-rates", "synergies", "self-play"))
    parser.add_argument("--model", type=Path, default=MODEL)
    parser.add_argument("--dataset", type=Path, default=DATASET_FOLDER)
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    parser.add_argument("--prelude-games-only", action="store_true", help="as tfmstats.com's Starting Hand page")
    parser.add_argument("--top", type=int, default=20, help="keep rates: how many of the largest differences")
    parser.add_argument("--most-games", type=int, help="only the first this many held-out Games, for a quicker look")
    parser.add_argument("--pairs", default="", help="synergies: corporation:prelude_card pairs, comma-separated")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--controller", default="imitation", help="self-play: the registered Controller")
    parser.add_argument("--games", type=int, default=200, help="self-play: Games against itself")
    parser.add_argument("--processes", type=int, help="self-play: worker processes (default: every core)")
    parser.add_argument("--min-rating", type=int, default=450, help="self-play: Players rated at least this")
    given = parser.parse_args(given_arguments)
    if given.check == "self-play":
        return self_play_report(given)
    model = load_model(given.model, given.device)[0]

    def scorer(batch: Any) -> torch.Tensor:
        return scored(model, batch.to(given.device), given.device)

    def games() -> Iterator[dict[str, Any]]:
        kept = (
            game for game in held_out(given.dataset, given.split) if game["prelude"] or not given.prelude_games_only
        )
        return itertools.islice(kept, given.most_games)

    if given.check == "keep-rates":
        print(keep_rate_report(model_keep_rates(scorer, games()), players_keep_rates(games()), given.top))
        return 0
    held = list(games())
    learned = 0
    pairs = [pair.split(":") for pair in given.pairs.split(",") if pair]
    print(
        f"{'Corporation':<32}{'Prelude Card':<28}{'probes':>7}{'corp with':>11}{'without':>9}{'prelude with':>14}{'without':>9}"
    )
    for corporation, prelude_card in pairs:
        found = synergy(scorer, held, corporation, prelude_card)
        learned += found.learned
        print(
            f"{corporation:<32}{prelude_card:<28}{found.probes:>7,}{found.corporation_with:>11.1%}"
            f"{found.corporation_without:>9.1%}{found.prelude_with:>14.1%}{found.prelude_without:>9.1%}"
            f"  {'yes' if found.learned else 'no'}",
            flush=True,
        )
    print(f"{learned} of {len(pairs)} pairs given a higher chance together than apart, for both parts")
    return 0


if __name__ == "__main__":
    sys.exit(main())

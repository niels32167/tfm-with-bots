"""How well the Imitation Model predicts Players' picks on held-out Games, beside three baselines (ticket 13 of
phase 2, box 2):
- a random pick (its expected accuracy, one over the Options);
- the most-kept card: the Option whose card was kept most often when offered at that kind of Decision, over the
  training Games (`KeepRates`; "done" is counted likewise);
- the Card Economy Bot's Prices, where the view holds the hand its Prices read: setup records and replayed
  positions, not records after setup. The model's accuracy on those same positions is given beside it.

    uv run python -m ai.imitation.evaluate --model .cache/models/imitation.pt
    uv run python -m ai.imitation.evaluate --model m.pt --min-rating 500 --prelude-games-only --split validation

Accuracy is reported overall, by Decision kind, Generation, the deciding Player's rating, and whether the
position came from the replay (full view) or the records.
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from ai.encoding import OPTION_FIELDS, OPTION_TYPES, card_numbers
from ai.imitation import MODEL, MODELS_FOLDER
from ai.imitation.encoded import Position
from ai.imitation.model import Batch, collate, load_model, scored
from ai.imitation.positions import PositionSettings, positions
from ai.imitation.split import TEST_FROM, VALIDATION_FROM, split_of
from ai.recorded_games.dataset import DATASET_FOLDER, read_games
from ai.recorded_games.records import recorded_decisions

KEEP_RATES_FILE = MODELS_FOLDER / "keep-rates.json"
RATING_BANDS = ((0, "under 300"), (300, "300-399"), (400, "400-499"), (500, "500-599"), (600, "600+"))
LAST_GENERATION_SHOWN = 10
NO_CARD = ""

type Scorer = Callable[[Batch], torch.Tensor]


class KeepRates:
    """How often each card was kept when offered, by kind of Decision and Option type, from Recorded Games' records."""

    def __init__(self, counts: dict[tuple[str, str, str], list[int]]) -> None:
        self.counts = counts
        self.kinds = {kind for kind, _, _ in counts}

    @classmethod
    def counted(cls, games: Iterable[dict[str, Any]]) -> KeepRates:
        counts: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0])
        for game in games:
            for decision in recorded_decisions(game):
                for option in decision["options"]:
                    details = option["details"]
                    offered_and_kept = counts[decision["kind"], details["type"], details.get("card") or NO_CARD]
                    offered_and_kept[0] += 1
                    offered_and_kept[1] += option["index"] == decision["picked"]
        return cls(dict(counts))

    def rate(self, kind: str, option_type: str, card: str) -> float:
        offered, kept = self.counts.get((kind, option_type, card), (0, 0))
        return kept / offered if offered else 0.0

    def pick(self, kind: str, options: Any) -> int | None:
        """The Option, among encoded Option rows, whose card was kept most often; None at a kind of Decision the
        records don't describe (the Action phase's), which has no keep rates."""
        if kind not in self.kinds:
            return None
        cards = [NO_CARD, *card_numbers()]
        rates = [self.rate(kind, OPTION_TYPES[int(row[TYPE_COLUMN])], cards[int(row[CARD_COLUMN])]) for row in options]
        return rates.index(max(rates))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [[*key, *counts] for key, counts in sorted(self.counts.items())]
        path.write_text(json.dumps({"split": [VALIDATION_FROM, TEST_FROM], "counts": rows}))

    @classmethod
    def load(cls, path: Path) -> KeepRates | None:
        """Saved keep rates, or None if there are none for this split."""
        if not path.exists():
            return None
        saved = json.loads(path.read_text())
        if saved["split"] != [VALIDATION_FROM, TEST_FROM]:
            return None
        return cls(
            {(kind, option_type, card): [offered, kept] for kind, option_type, card, offered, kept in saved["counts"]}
        )


TYPE_COLUMN = OPTION_FIELDS.index("type")
CARD_COLUMN = OPTION_FIELDS.index("card")


@dataclass
class Accuracy:
    """Counts for one row of the report; the properties are shares."""

    count: int = 0
    model_right: int = 0
    random_sum: float = 0.0
    most_kept_count: int = 0
    most_kept_right: int = 0
    card_economy_count: int = 0
    card_economy_right: int = 0
    model_right_where_priced: int = 0

    @property
    def model(self) -> float:
        return self.model_right / self.count

    @property
    def random(self) -> float:
        return self.random_sum / self.count

    @property
    def most_kept(self) -> float:
        return self.most_kept_right / self.most_kept_count if self.most_kept_count else float("nan")

    @property
    def card_economy(self) -> float:
        return self.card_economy_right / self.card_economy_count if self.card_economy_count else float("nan")

    @property
    def model_where_priced(self) -> float:
        return self.model_right_where_priced / self.card_economy_count if self.card_economy_count else float("nan")


def rating_band(rating: int) -> str:
    return [label for lowest, label in RATING_BANDS if rating >= lowest][-1]


def generation_label(generation: int) -> str:
    return str(generation) if generation < LAST_GENERATION_SHOWN else f"{LAST_GENERATION_SHOWN}+"


def accuracy_report(
    scorer: Scorer, found: Iterable[Position], keep_rates: KeepRates, *, batch: int = 512
) -> dict[str, dict[str, Accuracy]]:
    """The model's accuracy and the baselines' on `found`, overall and by kind, Generation, rating and source."""
    report: dict[str, dict[str, Accuracy]] = defaultdict(lambda: defaultdict(Accuracy))
    chunk: list[Position] = []

    def tally() -> None:
        with torch.no_grad():
            picks = scorer(collate(chunk)).argmax(dim=1).tolist()
        for position, pick in zip(chunk, picks, strict=True):
            rows = [
                report["overall"]["all"],
                report["kind"][position.kind],
                report["generation"][generation_label(position.generation)],
                report["rating"][rating_band(position.rating)],
                report["source"][position.source],
            ]
            right = pick == position.picked
            most_kept = keep_rates.pick(position.kind, position.options)
            for row in rows:
                row.count += 1
                row.model_right += right
                row.random_sum += 1 / len(position.options)
                if most_kept is not None:
                    row.most_kept_count += 1
                    row.most_kept_right += most_kept == position.picked
                if position.card_economy_pick is not None:
                    row.card_economy_count += 1
                    row.card_economy_right += position.card_economy_pick == position.picked
                    row.model_right_where_priced += right
        chunk.clear()

    for position in found:
        chunk.append(position)
        if len(chunk) == batch:
            tally()
    if chunk:
        tally()
    return {section: dict(rows) for section, rows in report.items()}


def training_keep_rates(folder: Path) -> KeepRates:
    """The keep rates of the training Games, counted once and saved."""
    saved = KeepRates.load(KEEP_RATES_FILE) if folder == DATASET_FOLDER else None
    if saved is not None:
        return saved
    rates = KeepRates.counted(game for game in read_games(folder) if split_of(game) == "train")
    if folder == DATASET_FOLDER:
        rates.save(KEEP_RATES_FILE)
    return rates


def percent(share: float) -> str:
    return "-" if math.isnan(share) else f"{share:.1%}"


def table(report: dict[str, dict[str, Accuracy]]) -> str:
    header = f"{'':<22}{'positions':>10}{'model':>8}{'random':>8}{'most-kept':>11}{'priced':>9}{'model':>8}{'Bot':>8}"
    lines = [header, f"{'':<22}{'':>10}{'':>8}{'':>8}{'':>11}{'(Bot)':>9}{'there':>8}{'Prices':>8}"]
    order = {
        "generation": lambda key: int(key.rstrip("+")),
        "rating": lambda key: [b[1] for b in RATING_BANDS].index(key),
    }
    for section, rows in report.items():
        lines.append(section)
        for key in sorted(rows, key=order.get(section, str)):
            row = rows[key]
            lines.append(
                f"  {key:<20}{row.count:>10,}{percent(row.model):>8}{percent(row.random):>8}"
                f"{percent(row.most_kept):>11}{row.card_economy_count:>9,}{percent(row.model_where_priced):>8}"
                f"{percent(row.card_economy):>8}"
            )
    return "\n".join(lines)


def main(given_arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ai.imitation.evaluate", description=__doc__.splitlines()[0])
    parser.add_argument("--model", type=Path, default=MODEL)
    parser.add_argument("--dataset", type=Path, default=DATASET_FOLDER)
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    parser.add_argument("--min-rating", type=int, help="only Decisions of Players rated at least this")
    parser.add_argument("--prelude-games-only", action="store_true")
    parser.add_argument("--shard-share", type=int, default=1, help="only every n-th shard")
    parser.add_argument("--without-bot", action="store_true", help="leave out the Card Economy Bot's baseline")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    given = parser.parse_args(given_arguments)
    model, saved = load_model(given.model, given.device)
    print(f"{given.model}: trained on {saved['positions_seen']:,} positions with {saved['settings']}")
    keep_rates = training_keep_rates(given.dataset)
    settings = PositionSettings(given.min_rating, given.prelude_games_only, card_economy_picks=not given.without_bot)
    found = positions(given.dataset, given.split, settings, workers=given.workers, shard_share=(0, given.shard_share))
    report = accuracy_report(lambda batch: scored(model, batch.to(given.device), given.device), found, keep_rates)
    print(f"{given.split} Games; {settings}")
    print(table(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())

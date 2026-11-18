"""Which Games train the Imitation Model, which choose between models and settings (validation), and which
are held out to test it: by whole Game, so that no position of a Game is learned and tested on, and by date,
so that the test Games are later than every Game trained on, as the AI meets Players after it was trained.

The two dates cut the dated Games about 80/10/10 (59,039 Games, 56,234 of them dated, 2023-11-28 to
2026-01-07). A Game whose date is invalid (None) goes by a hash of its id, in the same proportions.
"""

import hashlib
from typing import Any, Literal

type Split = Literal["train", "validation", "test"]

VALIDATION_FROM = "2025-09-09"
TEST_FROM = "2025-09-30"

# For Games without a date: the share of each part, in hundredths.
TRAIN_SHARE = 80
VALIDATION_SHARE = 10


def split_of(game: dict[str, Any]) -> Split:
    """The part `game` (a dataset Game, or anything with its "game" id and "date") belongs to."""
    date = game["date"]
    if date is not None:
        if date < VALIDATION_FROM:
            return "train"
        return "validation" if date < TEST_FROM else "test"
    hundredth = int.from_bytes(hashlib.sha256(game["game"].encode()).digest()[:8]) % 100
    if hundredth < TRAIN_SHARE:
        return "train"
    return "validation" if hundredth < TRAIN_SHARE + VALIDATION_SHARE else "test"

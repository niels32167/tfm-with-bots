"""Value and Search Bots on Value Models other than the registered one, for Matches by "module:attribute" (ticket 16's
box 3, 2026-11-23). Run from the repository with this folder on the path:

    PYTHONPATH=.:.scratch/phase-2-ai-opponent/experiments/16 uv run python -m ai.match model_files:search_w \
        model_files:value_v006 --games 200 --processes 10 --first-seed 3000000
"""

from pathlib import Path

from ai.search import SearchBot
from ai.value.bot import ValueBot

MODELS = Path(__file__).resolve().parents[4] / ".cache" / "models"
V006 = MODELS / "value-v006.pt"  # ticket 15's registered Value Model, kept as a copy
V000 = MODELS / "value-runs" / "main" / "versions" / "v000.pt"  # ticket 15's first warm start
W = MODELS / "value-runs" / "warm-all-short" / "versions" / "v000.pt"  # the warm start on every Recorded Game, 800k


def value_v006() -> ValueBot:
    return ValueBot(V006)


def value_v000() -> ValueBot:
    return ValueBot(V000)


def value_w() -> ValueBot:
    return ValueBot(W)


def search_v000() -> SearchBot:
    return SearchBot(path=V000)


def search_w() -> SearchBot:
    return SearchBot(path=W)

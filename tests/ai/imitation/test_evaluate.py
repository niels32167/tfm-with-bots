"""On held-out Games, the Imitation Model's picks are compared with Players' and with the baselines' (ticket 13 of
phase 2, box 2): a random pick, the most-kept card overall, and the Card Economy Bot's Prices, by Decision kind,
Generation and rating."""

import math

import torch

from ai.imitation.evaluate import KeepRates, accuracy_report
from ai.imitation.model import Batch
from ai.imitation.positions import PositionSettings, game_positions
from tests.ai.imitation.test_positions import EXAMPLE_DECISIONS, example, replay_of_the_example
from tests.ai.recorded_games.test_records import GAME


def picks_as_players_did(batch: Batch) -> torch.Tensor:
    """A scorer that always agrees with the Player."""
    return torch.nn.functional.one_hot(batch.picked, batch.options.shape[1]).float()


def held_out():
    settings = PositionSettings(card_economy_picks=True)
    return list(game_positions(example("late", date="2026-01-01"), None, settings))


def test_keep_rates_count_how_often_a_card_offered_was_kept_at_each_kind_of_decision():
    rates = KeepRates.counted([GAME])

    # Player 1 drafted Electro Catapult the one time it was offered; Technology Demonstration was offered three
    # times in Generation 2's Draft and never picked (the 4th card comes by itself).
    assert rates.rate("draft", "draft_card", "electro_catapult") == 1.0
    assert rates.rate("draft", "draft_card", "technology_demonstration") == 0.0
    assert rates.rate("draft", "draft_card", "never_offered") == 0.0


def test_the_report_gives_each_kind_with_the_model_and_baselines_beside_it():
    report = accuracy_report(picks_as_players_did, held_out(), KeepRates.counted([GAME]), batch=8)

    overall = report["overall"]["all"]
    assert overall.count == EXAMPLE_DECISIONS
    assert overall.model == 1.0
    # Three Draft picks each, from 4, 3 and 2 cards.
    assert abs(report["kind"]["draft"].random - (1 / 4 + 1 / 3 + 1 / 2) / 3) < 1e-9
    assert set(report["kind"]) == {"corporation", "prelude_cards", "buy_cards", "draft"}
    assert set(report["generation"]) == {"1", "2"}
    assert set(report["rating"]) == {"500-599"}


def test_the_card_economy_bot_is_scored_only_where_the_view_holds_what_its_prices_need():
    report = accuracy_report(picks_as_players_did, held_out(), KeepRates.counted([GAME]), batch=8)

    # Records after setup lack the hand, which the Bot's Prices read: only the 12 setup Decisions are priced.
    assert report["overall"]["all"].card_economy_count == 12
    assert report["kind"]["draft"].card_economy_count == 0
    assert 0.0 <= report["kind"]["corporation"].card_economy <= 1.0


def test_the_most_kept_baseline_is_left_blank_at_kinds_the_records_dont_describe():
    # Ticket 14: no keep rates exist for the Action-phase kinds, where most-kept would only pick the first Option.
    game = example("late", date="2026-01-01")
    replay = {**replay_of_the_example(), "game": game["game"]}
    found = list(game_positions(game, replay, PositionSettings()))

    report = accuracy_report(picks_as_players_did, found, KeepRates.counted([GAME]), batch=8)

    assert math.isnan(report["kind"]["action"].most_kept)
    assert report["kind"]["draft"].most_kept >= 0.0
    assert report["overall"]["all"].most_kept_count == EXAMPLE_DECISIONS

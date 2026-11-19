"""Checks of what the Imitation Model learned, on held-out Games (ticket 13 of phase 2): its keep rate for each
card at setup beside Players' (box 5), and whether it gives a Corporation and a Prelude Card a higher chance
together than apart (box 6). A scorer with a known taste stands in for the model."""

import torch

from ai.encoding import OPTION_TYPES, card_number
from ai.imitation.checks import (
    AwardRate,
    MilestoneRate,
    benchmark,
    model_keep_rates,
    players_games,
    players_keep_rates,
    synergy,
)
from ai.imitation.model import Batch
from ai.match import Claim, GameSummary
from tests.ai.imitation.test_positions import example, replay_of_the_example, write_dataset

DONE = OPTION_TYPES.index("done")
CREDICOR, EARLY_SETTLEMENT = "credicor", "early_settlement"


def never_buying(batch: Batch) -> torch.Tensor:
    return (batch.options[..., 0] == DONE).float()


def always_buying(batch: Batch) -> torch.Tensor:
    return (batch.options[..., 0] != DONE).float()


def test_players_keep_rates_are_the_cards_kept_at_setup_over_those_dealt():
    rates = players_keep_rates([example("a", date="2026-01-01")])

    assert rates["underground_city"] == (1, 1)
    assert rates["ai_central"] == (1, 0)


def test_the_models_keep_rates_come_from_its_own_picks_through_the_whole_buying_chain():
    games = [example("a", date="2026-01-01")]

    assert model_keep_rates(never_buying, games)["underground_city"] == (1, 0)
    # Both Players can pay for all 10 cards dealt: Credicor starts with 57 MegaCredits, Thorgate with 48.
    kept = model_keep_rates(always_buying, games)
    assert kept["underground_city"] == kept["ai_central"] == kept["pets"] == (1, 1)


def fond_of_credicor_with_early_settlement(batch: Batch) -> torch.Tensor:
    """Scores Credicor higher where Early Settlement is among the cards the Player sees, and nothing else."""
    sees = (batch.cards[..., 0] == card_number(EARLY_SETTLEMENT)).any(dim=1, keepdim=True)
    is_credicor = batch.options[..., 1] == card_number(CREDICOR)
    return (is_credicor & sees).float() * 2


def test_a_synergy_shows_as_a_higher_chance_for_each_part_with_the_other_than_without():
    found = synergy(
        fond_of_credicor_with_early_settlement, [example("a", date="2026-01-01")], CREDICOR, EARLY_SETTLEMENT
    )

    # Each setup record is a probe, with the pair put into its offer or taken out of it.
    assert found.probes == 2
    assert found.corporation_with > found.corporation_without
    assert found.prelude_with == found.prelude_without


def test_a_corporation_nobody_was_dealt_is_put_in_beside_the_one_the_player_chose():
    found = synergy(never_buying, [example("a", date="2026-01-01")], "helion", EARLY_SETTLEMENT)

    assert found.probes == 2


def no_preference(batch: Batch) -> torch.Tensor:
    """The same score for every Option; padding never wins, as in the model."""
    return torch.zeros(batch.options.shape[:2]).masked_fill(~batch.option_mask, float("-inf"))


def test_the_prelude_card_counts_if_kept_at_all_not_only_if_kept_first():
    # Of 4 Prelude Cards dealt, 2 are kept: with no preference, each is kept with chance 1/4 + 3/4 * 1/3 = 1/2,
    # whatever its card number. Kept first would be 1/4, and never for a card the records always list last.
    found = synergy(no_preference, [example("a", date="2026-01-01")], CREDICOR, EARLY_SETTLEMENT)

    assert abs(found.prelude_with - 0.5) < 1e-6
    assert abs(found.prelude_without - 0.5) < 1e-6


def test_the_benchmark_gives_means_per_game_and_the_share_of_funded_awards_lost():
    def score(player: int, total: int, cards: int) -> dict:
        return {"player": player, "total": total, "cards": cards}

    games = [
        GameSummary(
            12,
            [score(0, 100, 20), score(1, 80, 10)],
            [Claim("mayor", 0, 5)],
            [Claim("banker", 0, 6, lost=True), Claim("miner", 1, 10, lost=False)],
        ),
        GameSummary(
            14, [score(0, 90, 30), score(1, 110, 40)], [Claim("mayor", 1, 7)], [Claim("banker", 1, 8, lost=False)]
        ),
    ]

    found = benchmark(games)

    assert found.games == 2
    assert found.generations == 13
    assert found.points == 95
    assert found.card_points == 25
    assert found.milestones["mayor"] == MilestoneRate(per_game=1.0, generation=6.0)
    assert found.awards["banker"] == AwardRate(per_game=1.0, generation=7.0, lost=0.5)
    assert found.flip_rate == 1 / 3


def test_players_games_are_those_with_prelude_not_conceded_replayed_fully_and_both_players_rated_that_high(tmp_path):
    games = [
        {**example("strong", date="2024-01-01", ratings=(500, 460)), "conceded": False},
        {**example("weak", date="2024-01-01", ratings=(500, 300)), "conceded": False},
        {**example("conceded", date="2024-01-01"), "conceded": True},
        {**example("cut short", date="2024-01-01"), "conceded": False},
    ]
    replays = [{**replay_of_the_example(), "game": game} for game in ("strong", "weak", "conceded")]
    replays.append({**replay_of_the_example(picks=20), "game": "cut short", "complete": False})
    folder = write_dataset(tmp_path, games, replays)

    found = list(players_games(folder, min_rating=450))

    assert len(found) == 1
    assert found[0].generations == 2

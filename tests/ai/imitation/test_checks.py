"""Checks of what the Imitation Model learned, on held-out Games (ticket 13 of phase 2): its keep rate for each
card at setup beside Players' (box 5), and whether it gives a Corporation and a Prelude Card a higher chance
together than apart (box 6). A scorer with a known taste stands in for the model."""

import torch

from ai.encoding import OPTION_TYPES, card_number
from ai.imitation.checks import model_keep_rates, players_keep_rates, synergy
from ai.imitation.model import Batch
from tests.ai.imitation.test_positions import example

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

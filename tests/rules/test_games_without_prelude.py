"""The Prelude box's 47 cards are in the card catalog (ADR 0011), but a Game never holds one until
Prelude can be switched on. Scenarios can't name them either, since a card with no effect data can't be played."""

import pytest
import tm_engine

from tests.helpers import PROJECT_CARDS, play_randomly, player, scenario

PRELUDE_BOX_IDS = {card["id"] for card in tm_engine.card_catalog() if card["expansion"] == "prelude"}


def strings_in(value) -> set[str]:
    """Every string anywhere inside a view of a Game, keys aside."""
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        return {found for each in value for found in strings_in(each)}
    return set()


@pytest.mark.parametrize("players", [2, 3, 4, 5])
def test_a_game_without_prelude_never_deals_a_card_of_the_prelude_box_at_setup(players):
    for seed in range(50):
        game = tm_engine.Game(seed=seed, players=players)

        assert not strings_in(game.full_view()) & PRELUDE_BOX_IDS


def test_a_whole_game_never_holds_a_card_of_the_prelude_box():
    game = tm_engine.Game(seed=3, players=2)
    seen: set[str] = set()
    for batch in range(10_000):
        if game.is_over:
            break
        seen |= strings_in(game.full_view())
        play_randomly(game, seed=batch, picks=25)

    assert game.is_over
    assert seen & set(PROJECT_CARDS)  # the views do name cards
    assert not seen & PRELUDE_BOX_IDS


@pytest.mark.parametrize("card", ["house_printing", "donation", "vitor"])
def test_a_scenario_cannot_put_a_card_of_the_prelude_box_in_a_hand(card):
    with pytest.raises(ValueError, match=card):
        scenario(player(hand=[card]), player())


@pytest.mark.parametrize("card", ["vitor", "donation", "house_printing"])
def test_a_scenario_cannot_give_a_player_a_corporation_from_the_prelude_box(card):
    with pytest.raises(ValueError, match=card):
        scenario(player(corporation=card), player())

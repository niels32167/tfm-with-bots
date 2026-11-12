"""Sampled Positions (ticket 07): a Game made from one Player's Player View, with the cards that Player
can't see dealt at random. Search looks ahead on them instead of on copies of the real Game, which would
show it the deck and the other hands (ADR 0013)."""

import random
from collections import Counter
from typing import Any

import pytest
import tm_engine

from tests.helpers import MAX_PICKS


def test_a_sampled_positions_player_view_for_its_player_equals_the_real_one():
    game = tm_engine.Game(seed=3, players=2, draft=True, prelude=True)
    game.play_randomly(seed=3, picks=200)
    player = game.decision["player"]

    sample = game.sampler(player).sample(seed=1)

    assert sample.player_view(player) == game.player_view(player)


PROJECT_CARDS = [card["id"] for card in tm_engine.card_catalog() if card["type"] in {"automated", "active", "event"}]
PRELUDE_CARDS = [card["id"] for card in tm_engine.card_catalog() if card["type"] == "prelude"]


def readable(game: tm_engine.Game) -> list[object]:
    """Everything Python can read of a Game."""
    return [game.full_view(), game.decision, game.log, game.seed, game.replay, game.scores]


def assert_same_game(one: tm_engine.Game, other: tm_engine.Game) -> None:
    """Two Games are the same if everything Python can read of them is, now and after playing both on
    the same way to the end."""
    assert readable(one) == readable(other)
    one.play_randomly(seed=99)
    other.play_randomly(seed=99)
    assert readable(one) == readable(other)


def test_two_games_that_differ_only_in_hidden_cards_give_the_same_sampled_position_for_the_same_seed():
    # Player 1's hand, the deck's top cards, the discard pile and Player 1's Prelude Cards still to play
    # are swapped around between the two, and the seeds differ: Player 0 can't tell them apart.
    mine = PROJECT_CARDS[:3]
    swapped = PROJECT_CARDS[10:16]

    def game(seed: int, theirs: list[str], deck: list[str], discard: list[str], preludes: list[str]):
        return tm_engine.Game.from_scenario(
            {
                "seed": seed,
                "prelude": True,
                "generation": 1,
                "players": [
                    {"hand": mine, "prelude_cards": PRELUDE_CARDS[:2]},
                    {"hand": theirs, "prelude_cards": preludes},
                ],
                "deck": deck,
                "discard": discard,
            }
        )

    one = game(1, swapped[:2], swapped[2:4], swapped[4:], PRELUDE_CARDS[2:4])
    other = game(2, swapped[4:], swapped[:2], swapped[2:4], PRELUDE_CARDS[4:6])
    assert one.player_view(0) == other.player_view(0)
    assert one.full_view() != other.full_view()

    assert_same_game(one.sampler(0).sample(seed=5), other.sampler(0).sample(seed=5))


def without_sequence(decision: dict[str, Any] | None) -> dict[str, Any] | None:
    """A Decision without its sequence number, which counts every pick before it, hidden ones too."""
    return decision and {key: value for key, value in decision.items() if key != "sequence"}


def places_of_cards(game: tm_engine.Game) -> dict[str, list[str]]:
    """Every card in the Game by where it is. Cards a Player has chosen of those dealt to them (a
    Corporation, Prelude Cards kept, cards bought, cards kept in the Draft or of those looked at) count
    with those dealt, as a sample may take such choices back."""
    view = game.full_view()
    places = {"deck": view["deck"], "discard": view["discard"]}
    for index, board in enumerate(view["players"]):
        corporations = board["choosing_corporation"] or {"dealt": []}
        prelude_cards = board["prelude_cards"] or {"dealt": [], "kept": []}
        drafting = board["drafting"] or {"picking_from": [], "kept": []}
        keeping = board["keeping"] or {"looking_at": [], "kept": []}
        places |= {
            f"{index} hand": board["hand"],
            f"{index} played": board["played_cards"] + board["played_prelude_cards"],
            f"{index} corporation": [board["corporation"]] if board["corporation"] else [],
            f"{index} corporations dealt": corporations["dealt"],
            f"{index} prelude cards": sorted(set(prelude_cards["dealt"]) | set(prelude_cards["kept"])),
            f"{index} dealt": (board["buying"] or {"dealt": []})["dealt"],
            f"{index} drafting": drafting["picking_from"] + drafting["kept"],
            f"{index} looking at": keeping["looking_at"] + keeping["kept"],
        }
    return places


SETTINGS = [
    {"seed": 7, "players": 2, "draft": True, "prelude": True},
    {"seed": 8, "players": 3, "draft": True, "prelude": True},
    {"seed": 9, "players": 2, "draft": True, "prelude": True},
    {"seed": 12, "players": 2, "draft": False, "prelude": True},
    {"seed": 10, "players": 2, "draft": True, "prelude": False},
    {"seed": 11, "players": 4, "draft": True, "prelude": True},
]


def test_at_every_decision_a_sample_keeps_the_deciding_players_view_and_decision_and_every_card():
    for settings in SETTINGS:
        game = tm_engine.Game(**settings)
        random_numbers = random.Random(settings["seed"])
        for _ in range(MAX_PICKS):
            if (decision := game.decision) is None:
                break
            player = decision["player"]
            sample = game.sampler(player).sample(seed=random_numbers.randrange(1 << 40))
            where = f"{settings}, pick {decision['sequence']}, a {decision['kind']} Decision"

            assert sample.player_view(player) == game.player_view(player), where
            assert without_sequence(sample.decision) == without_sequence(decision), where
            real, sampled = places_of_cards(game), places_of_cards(sample)
            assert {place: len(cards) for place, cards in sampled.items()} == {
                place: len(cards) for place, cards in real.items()
            }, where
            assert Counter(card for cards in sampled.values() for card in cards).most_common(1)[0][1] == 1, where
            assert sample.full_view()["prelude_deck_size"] == game.full_view()["prelude_deck_size"], where
            game.pick(random_numbers.randrange(len(decision["options"])), decision["sequence"])
        assert game.is_over


def test_at_every_decision_sampling_a_sample_gives_what_sampling_the_real_game_does():
    # A sample is a Game its Player can't tell from the real one, differing in every hidden card, in
    # its seed and in its past. So both must give the same samples.
    for settings in SETTINGS:
        game = tm_engine.Game(**settings)
        random_numbers = random.Random(settings["seed"])
        for _ in range(MAX_PICKS):
            if (decision := game.decision) is None:
                break
            for player in range(game.players):
                first, second = random_numbers.randrange(1 << 40), random_numbers.randrange(1 << 40)
                resampled = game.sampler(player).sample(seed=first).sampler(player).sample(seed=second)
                where = f"{settings}, pick {decision['sequence']}, a {decision['kind']} Decision, Player {player}"

                assert readable(resampled) == readable(game.sampler(player).sample(seed=second)), where
            game.pick(random_numbers.randrange(len(decision["options"])), decision["sequence"])
        assert game.is_over


def test_a_sample_has_its_own_seed_an_empty_log_and_a_replay_that_starts_at_the_sample():
    game = tm_engine.Game(seed=3, players=2, draft=True, prelude=True)
    game.play_randomly(seed=3, picks=300)
    sample = game.sampler(0).sample(seed=12345)

    assert sample.seed == 12345
    assert sample.log == []
    assert sample.replay == {"start": "sampled", "picks": []}
    assert sample.decision["sequence"] == 0
    sample.pick(0)
    assert sample.replay["picks"] == [0]


def test_a_samples_replay_cant_be_replayed():
    game = tm_engine.Game(seed=3, players=2)
    sample = game.sampler(0).sample(seed=1)
    sample.pick(0)

    with pytest.raises(ValueError, match="dealt at random"):
        tm_engine.Game.from_replay(sample.replay)


def play_until(game: tm_engine.Game, wanted, random_numbers: random.Random) -> None:
    for _ in range(MAX_PICKS):
        if wanted(game.decision):
            return
        game.pick(random_numbers.randrange(len(game.decision["options"])))
    raise AssertionError("never got there")


def test_the_cards_another_player_bought_before_are_taken_back_and_they_buy_again_after_the_player():
    game = tm_engine.Game(seed=21, players=2, draft=False, prelude=False)
    random_numbers = random.Random(1)
    # Generation 2's Research phase, once the first player has bought a card and is done.
    play_until(game, lambda decision: game.player_view(0)["generation"] == 2, random_numbers)
    first = game.decision["player"]
    second = 1 - first
    play_until(game, lambda decision: decision["kind"] == "buy_cards", random_numbers)
    buy = next(option["index"] for option in game.decision["options"] if option["details"]["type"] == "buy_card")
    game.pick(buy)
    play_until(game, lambda decision: decision["player"] == second, random_numbers)
    assert game.full_view()["players"][first]["buying"]["bought"]

    sample = game.sampler(second).sample(seed=8)
    assert sample.full_view()["players"][first]["buying"]["bought"] == []
    play_until(sample, lambda decision: decision["player"] == first, random_numbers)

    assert sample.decision["kind"] == "buy_cards"
    assert sample.player_view(0)["phase"] == "research"


def test_the_card_another_player_kept_in_this_draft_round_is_taken_back_and_they_pick_again_after_the_player():
    game = tm_engine.Game(seed=21, players=2, draft=True, prelude=False)
    random_numbers = random.Random(1)
    play_until(game, lambda decision: decision["kind"] == "draft", random_numbers)
    first = game.decision["player"]
    game.pick(0)
    second = game.decision["player"]
    assert second != first and game.decision["kind"] == "draft"

    sample = game.sampler(second).sample(seed=8)
    drafting = sample.full_view()["players"][first]["drafting"]
    assert (len(drafting["picking_from"]), len(drafting["kept"])) == (4, 0)
    sample.pick(0)

    assert sample.decision["player"] == first
    assert sample.decision["kind"] == "draft"
    assert len(sample.decision["options"]) == 4


def known_to_be_with(view: dict[str, Any]) -> dict[int, set[str]]:
    """The cards the viewer passed in the Draft and can't see now, by whom they went to last: that is
    where the viewer knows them to be, unless since played or otherwise accounted for."""
    own = view["players"][view["viewer"]]
    seen = set(own["hand"]) | {card for board in view["players"] for card in board["played_cards"]}
    for place in ("drafting", "buying", "keeping"):
        for cards in (own[place] or {}).values():
            seen |= set(cards) if isinstance(cards, list) else set()
    holders: dict[str, int] = {}
    for draft_pass in own["passed_in_draft"]:
        holders |= dict.fromkeys(draft_pass["cards"], draft_pass["to"])
    known: dict[int, set[str]] = {}
    for card, to in holders.items():
        if card not in seen:
            known.setdefault(to, set()).add(card)
    return known


def holdings(board: dict[str, Any]) -> set[str]:
    cards = set(board["hand"])
    for place in ("drafting", "buying"):
        if board[place]:
            cards |= set(board[place]["picking_from" if place == "drafting" else "dealt"])
            cards |= set(board[place]["kept"] if place == "drafting" else [])
    return cards


def test_cards_the_player_passed_in_the_draft_stay_with_whom_they_went_to_and_the_last_ones_are_picked_from():
    draft_picks_checked = 0
    for settings in [setting for setting in SETTINGS if setting["draft"]]:
        game = tm_engine.Game(**settings)
        random_numbers = random.Random(settings["seed"])
        for _ in range(MAX_PICKS):
            if (decision := game.decision) is None:
                break
            player = decision["player"]
            view = game.player_view(player)
            sample = game.sampler(player).sample(seed=random_numbers.randrange(1 << 40)).full_view()
            where = f"{settings}, pick {decision['sequence']}, a {decision['kind']} Decision"

            for holder, cards in known_to_be_with(view).items():
                held = holdings(sample["players"][holder])
                assert len(cards & held) == min(len(cards), len(held)), where
            passes = [p for p in view["players"][player]["passed_in_draft"] if p["generation"] == view["generation"]]
            if decision["kind"] == "draft" and passes and len(passes[-1]["cards"]) >= 2:
                picking_from = sample["players"][passes[-1]["to"]]["drafting"]["picking_from"]
                assert picking_from == passes[-1]["cards"], where
                draft_picks_checked += 1
            game.pick(random_numbers.randrange(len(decision["options"])), decision["sequence"])
    assert draft_picks_checked > 100


def test_a_card_another_player_is_paying_for_is_public_and_stays_in_their_hand_in_a_sample():
    game = tm_engine.Game(seed=4, players=2, draft=True, prelude=False)
    random_numbers = random.Random(4)

    def paying_for_a_card(decision: dict[str, Any]) -> bool:
        return decision["kind"] == "payment" and "action" not in decision["options"][0]["details"]

    play_until(game, paying_for_a_card, random_numbers)
    paying, other = game.decision["player"], 1 - game.decision["player"]
    card = game.decision["options"][0]["details"]["card"]

    assert game.player_view(other)["playing_card"] == card
    sample = game.sampler(other).sample(seed=2)
    assert card in sample.full_view()["players"][paying]["hand"]
    sample.pick(0)
    boards = sample.full_view()["players"]
    assert card in boards[paying]["played_cards"] and card not in boards[paying]["hand"]


def test_a_decision_in_progress_for_another_player_stays_answerable_with_their_cards_dealt_afresh():
    # Excentric Sponsor plays a card from the hand, and can be played only with a card it can play:
    # everyone knows Player 1 holds one, though not which. Found by the fuzz run (ticket 07).
    game = tm_engine.Game.from_scenario(
        {
            "prelude": True,
            "players": [
                {"prelude_cards": ["excentric_sponsor"], "hand": ["mine"], "resources": {"megacredits": 0}},
                {},
            ],
        }
    )
    assert game.decision["kind"] == "play_card"

    for seed in range(200):
        assert game.sampler(1).sample(seed=seed).decision["options"], f"seed {seed}"


def test_a_pick_another_player_makes_in_secret_changes_no_sample_for_a_player_who_cant_tell():
    # Two real positions a pick apart that a Player can't tell apart, such as before and after another
    # Player chooses their Corporation, buys a card or keeps one of those they look at, must give that Player
    # the same samples.
    compared: Counter[str] = Counter()
    for settings in SETTINGS:
        game = tm_engine.Game(**settings)
        random_numbers = random.Random(settings["seed"])
        for _ in range(MAX_PICKS):
            if (decision := game.decision) is None:
                break
            before = game.copy()
            game.pick(random_numbers.randrange(len(decision["options"])), decision["sequence"])
            for player in range(game.players):
                if player != decision["player"] and before.player_view(player) == game.player_view(player):
                    where = f"{settings}, pick {decision['sequence']}, a {decision['kind']} Decision, Player {player}"
                    seed = random_numbers.randrange(1 << 40)
                    one, other = before.sampler(player).sample(seed=seed), game.sampler(player).sample(seed=seed)
                    assert readable(one) == readable(other), where
                    compared[decision["kind"]] += 1
        assert game.is_over
    # After a Draft pick another Player picks, which every Player sees; that take-back has a test of its own.
    assert {"buy_cards", "corporation", "keep_cards", "prelude_cards"} <= set(compared), compared

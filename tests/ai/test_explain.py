"""The explain command: why a Controller picked what it picked at a step of a saved Game, with the
Prices of its top Options."""

import json

import tm_engine

from ai.card_economy import CardEconomyBot
from ai.controller import handle_for
from ai.explain import main, server_random


def a_saved_game(tmp_path, picks: int = 400):
    """A Replay file of two Card Economy Bots, played as the server plays them, stopped at the first
    Action with more than 2 Options after `picks` picks."""
    game = tm_engine.Game(seed=21, players=2, draft=True, prelude=True)
    bot = CardEconomyBot()
    while True:
        decision = game.decision
        if len(game.replay["picks"]) >= picks and decision["kind"] == "action" and len(decision["options"]) > 2:
            break
        game.pick(bot.pick(handle_for(game, server_random(game.seed, decision["sequence"]))))
    step = len(game.replay["picks"])
    game.pick(bot.pick(handle_for(game, server_random(game.seed, step))))
    path = tmp_path / "saved.json"
    path.write_text(json.dumps({"controllers": ["card_economy", "card_economy"], "replay": game.replay}))
    return path, step


def test_it_explains_a_saved_pick_with_the_prices_of_the_top_options(tmp_path, capsys):
    path, step = a_saved_game(tmp_path, picks=150)

    assert main([str(path), "--step", str(step), "--top", "3"]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == f"Card Economy Bot, step {step}:"
    assert "Generations left, held for every Option" in lines[1]
    best = next(line for line in lines if line.startswith("1. "))
    picked = lines[-1].removeprefix("Picked in the Replay: ")
    assert best.startswith(f"1. {picked}: ")
    assert not any(line.startswith("4. ") for line in lines)

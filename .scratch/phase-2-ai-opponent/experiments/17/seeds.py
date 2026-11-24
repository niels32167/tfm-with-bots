"""Ticket 17's seeds, drawn before any Game: the user is always Player 1, first Player in the odd-numbered Games and
second in the even-numbered ones. Only who is first is read from each Game, nothing of its deal.

    uv run python .scratch/phase-2-ai-opponent/experiments/17/seeds.py
"""

import random

import tm_engine

GAMES = 30

drawn = random.Random("ticket 17")
for number in range(1, GAMES + 1):
    wanted = (number + 1) % 2
    while True:
        seed = drawn.randrange(10**9)
        game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True, ask_last_prelude_card=True)
        if game.player_view(0)["first_player"] == wanted:
            break
    print(f"| {number} | {seed} | {'me' if wanted == 0 else 'AI'} | | | | |")

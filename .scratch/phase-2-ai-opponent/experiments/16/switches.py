"""Ticket 16's paired rule: at each Decision the Search Bot searches in a Game against the Value Bot, how many Sampled
Positions fit and how often each margin would pick other than the likeliest Option."""
import random, statistics, sys
import tm_engine
from ai.controller import handle_for
from ai.search import SearchBot
from ai.value.bot import ValueBot

seconds = float(sys.argv[1]); seeds = range(int(sys.argv[2]), int(sys.argv[3]))
margins = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0)
samples, switched = [], {margin: 0 for margin in margins}
for seed in seeds:
    bots = [SearchBot(seconds=seconds), ValueBot()]
    game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True)
    rng = random.Random(seed)
    while game.decision is not None:
        handle = handle_for(game, rng)
        if handle.player == 0 and len(handle.decision["options"]) > 1:
            found = bots[0].search(handle)
            pick = found.picked(0.0)
            if found.samples:
                samples.append(found.samples)
                for margin in margins:
                    switched[margin] += found.picked(margin) != next(iter(found.options))
        else:
            pick = bots[handle.player].pick(handle)
        game.pick(pick)
n = len(samples)
print(f"{seconds}s, {len(seeds)} Games, {n} Decisions searched; Sampled Positions median {statistics.median(samples)}, "
      f"quartiles {statistics.quantiles(samples, n=4)}, share with one {sum(s == 1 for s in samples) / n:.1%}")
for margin in margins:
    print(f"  margin {margin}: picks other than the likeliest at {switched[margin] / n:.1%}")

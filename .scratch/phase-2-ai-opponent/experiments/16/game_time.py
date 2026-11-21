"""Ticket 16: what one Game of the Search Bot against the Value Bot costs: time per pick, Decisions searched, samples."""
import random, statistics, sys, time
import tm_engine
from ai.controller import handle_for
from ai.search import SearchBot
from ai.value.bot import ValueBot

seconds = float(sys.argv[1]); seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1_900_000
bots = [SearchBot(seconds=seconds), ValueBot()]
game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True)
times, samples, searched_options = [], [], []
started = time.perf_counter()
rng = random.Random(seed)
while game.decision is not None:
    handle = handle_for(game, rng)
    bot = bots[handle.player]
    t = time.perf_counter()
    if handle.player == 0 and len(handle.decision["options"]) > 1:
        found = bot.search(handle)
        pick = 0 if not found.options else (next(iter(found.options)) if len(found.options) == 1 else max(found.options, key=lambda i: found.options[i].mean))
        if found.samples:
            times.append(time.perf_counter() - t); samples.append(found.samples); searched_options.append(len(found.options))
    else:
        pick = bot.pick(handle)
    game.pick(pick)
total = time.perf_counter() - started
print(f"budget {seconds}s: Game {total:.0f}s, searched {len(times)} Decisions, pick mean {statistics.mean(times):.3f}s max {max(times):.3f}s, samples mean {statistics.mean(samples):.1f} min {min(samples)}, Options {statistics.mean(searched_options):.1f}, generation {game.player_view(0)['generation']}, scores {[s['total'] for s in game.scores]}")

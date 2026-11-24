"""How many Sampled Positions the Search Bot gets per Decision, and how long it and the Value Bot take, on every third
Decision the Search Bot searches in one Game the Imitation Bot plays against itself. At a tenth of a core, as Render's
free instance has:

    systemd-run --user --scope -p CPUQuota=10% env PYTHONPATH=. \
        .venv/bin/python .scratch/phase-2-ai-opponent/experiments/17/samples_at_a_tenth.py 5

Give the seconds of the budget; leave out the systemd-run part for a whole core.
"""

import random
import statistics
import sys
import time

import tm_engine

from ai.controller import handle_for
from ai.controllers import make_controller

search = make_controller(f"search?seconds={float(sys.argv[1])}")
value = make_controller("value")
imitation = search.policy
game = tm_engine.Game(seed=77_000_001, players=2, draft=True, prelude=True)
decisions = searchable = 0
samples, search_seconds, value_seconds = [], [], []
while game.decision is not None:
    handle = handle_for(game, random.Random(decisions))
    decisions += 1
    if len(handle.decision["options"]) > 1 and len(search.narrowed(imitation.chances(handle))) > 1:
        searchable += 1
        if searchable % 3 == 0:
            started = time.perf_counter()
            samples.append(search.search(handle).samples)
            search_seconds.append(time.perf_counter() - started)
            started = time.perf_counter()
            value.pick(handle)
            value_seconds.append(time.perf_counter() - started)
    game.pick(imitation.pick(handle))

print(f"{len(samples)} Decisions of {searchable} searched")
only_one = samples.count(1) / len(samples)
print(f"Sampled Positions: quartiles {statistics.quantiles(samples, n=4)}, only 1 in {only_one:.0%}")
for name, seconds in (("Search Bot", search_seconds), ("Value Bot", value_seconds)):
    print(f"{name}: median {statistics.median(seconds):.2f} s, most {max(seconds):.2f} s")

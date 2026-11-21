import random, collections
import tm_engine
from ai.controller import handle_for
from ai.search import SearchBot
import ai.search as S
from ai.value.bot import ValueBot

bot = SearchBot(seconds=1.0)
vb = ValueBot()
game = tm_engine.Game(seed=1_900_000, players=2, draft=True, prelude=True)
rng = random.Random(0)
counts = collections.Counter()
orig_rated = bot.rated
def rated(g, p, r):
    counts["rated"] += 1; return orig_rated(g, p, r)
bot.rated = rated
orig_walk = bot.walk
for step in range(400):
    h = handle_for(game, rng)
    if h.player == 0 and len(h.decision["options"]) > 1 and h.player_view["phase"] == "action" and h.player_view["generation"] >= 3:
        counts.clear()
        found = bot.search(h)
        print(h.player_view["generation"], h.decision["kind"], len(h.decision["options"]), "searched", len(found.options), "samples", found.samples, dict(counts),
              {i: (round(e.mean, 3), e.visits, len(e.below or {})) for i, e in found.options.items()})
        if found.samples > 50: break
    game.pick(vb.pick(h))

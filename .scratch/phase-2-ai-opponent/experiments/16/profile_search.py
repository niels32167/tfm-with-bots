import cProfile, pstats, random, collections
import tm_engine
from ai.controller import handle_for
from ai.search import SearchBot
from ai.value.bot import ValueBot

bot = SearchBot(seconds=None, samples=10)
vb = ValueBot()
game = tm_engine.Game(seed=1_900_000, players=2, draft=True, prelude=True)
rng = random.Random(0)
handles = []
while game.decision is not None and len(handles) < 30:
    h = handle_for(game, rng)
    if h.player == 0 and len(h.decision["options"]) > 1 and h.player_view["phase"] == "action" and h.player_view["generation"] >= 4:
        handles.append(h)
    game.pick(vb.pick(h))
kinds = collections.Counter()
orig = bot.answer
def answer(g, d, f, r):
    kinds[(d["kind"], "follow" if f else "other", len(d["options"]) > 1)] += 1; return orig(g, d, f, r)
bot.answer = answer
pr = cProfile.Profile(); pr.enable()
total = sum(bot.search(h).samples for h in handles)
pr.disable()
print("samples", total, kinds.most_common(12))
pstats.Stats(pr).sort_stats("cumulative").print_stats(18)

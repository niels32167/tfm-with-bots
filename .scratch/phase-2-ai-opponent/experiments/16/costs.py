"""Ticket 16: what a search step costs on one core: forward passes by batch size, Sampled Positions, copies, views."""
import random, time
import tm_engine, torch
from ai.controller import handle_for
from ai.imitation.bot import ImitationBot
from ai.imitation.encoded import Position
from ai.value.bot import loaded
from ai.value.encoded import view_position
from ai.value.model import chances_of_winning
from ai.imitation.model import collate

torch.set_num_threads(1)
value, saved = loaded(__import__("ai.value", fromlist=["MODEL"]).MODEL)
policy = ImitationBot(saved["settings"]["policy"])
game = tm_engine.Game(seed=5, players=2, draft=True, prelude=True)
game.play_randomly(seed=5, picks=250)
h = handle_for(game, random.Random(0))
print("gen", h.player_view["generation"], h.decision["kind"], len(h.decision["options"]))

def timed(f, n=30):
    f(); t = time.perf_counter()
    for _ in range(n): f()
    return (time.perf_counter() - t) / n * 1000

samples = [h.sample(seed=i) for i in range(64)]
print("sample ms", timed(lambda: h.sample(seed=3)))
print("copy ms", timed(lambda: samples[0].copy()))
print("player_view ms", timed(lambda: samples[0].player_view(h.player)))
pv = samples[0].player_view(h.player); d = samples[0].decision
print("Position.of ms", timed(lambda: Position.of(pv, d)))
for n in (1, 4, 8, 16, 32, 64):
    ps = [Position.of(s.player_view(h.player), s.decision) for s in samples[:n]]
    vs = [view_position(s.player_view(h.player)) for s in samples[:n]]
    print(n, "policy ms %.1f" % timed(lambda: policy.likeliest_picks(ps), 10),
          "value ms %.1f" % timed(lambda: chances_of_winning(value, vs), 10),
          "collate ms %.1f" % timed(lambda: collate(ps), 10))

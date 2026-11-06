"""Rough, throwaway experiment for the phase-2 design talk. Three Controllers:

- random:    uniform random Option.
- heuristic: the "cost return" idea. A card's worth in MegaCredits from its printed data and the
             Generations left, a position's worth for draft, buy, sell and Action picks.
- flat_mc:   for each Option, N random playouts on copies, picks the best mean VP margin.
             NOTE it cheats: copies hold the real deck and the opponent's hand.
"""
import argparse
import collections
import multiprocessing as mp
import random
import statistics
import time

import tm_engine

CAT = {c["id"]: c for c in tm_engine.card_catalog()}

PROD = {"megacredits": 1.0, "steel": 1.7, "titanium": 2.5, "plants": 2.2, "energy": 1.3, "heat": 0.9}
STOCK = {"megacredits": 1.0, "steel": 1.7, "titanium": 2.5, "plants": 1.5, "energy": 0.7, "heat": 0.8}
TAG_BONUS = 0.5


def gens_left(view):
    temp = (8 - view["temperature"]) / 2
    oxy = 14 - view["oxygen"]
    oceans = 9 - view["oceans"]
    return max(temp + oxy + oceans, 0) / 4.5 + 0.5


def vp_worth(g):
    # A VP costs about 8 MegaCredits by Standard Project at the end; early money compounds.
    return 8 - min(g, 8) * 0.5


def effect_worth(e, g, vp):
    tr = vp + g
    v = 0.0
    for r, n in (e.get("production") or {}).items():
        v += PROD[r] * n * g
    for r, n in (e.get("resources") or {}).items():
        v += STOCK[r] * n
    v += e.get("temperature", 0) * tr + e.get("oxygen", 0) * tr + e.get("terraform_rating", 0) * tr
    v += e.get("draw", 0) * 3.5
    for t in e.get("tiles") or []:
        kind = t if isinstance(t, str) else t.get("tile")
        v += {"ocean": tr + 2, "greenery": tr + vp + 1, "city": vp * 1.5 + 2}.get(kind, 1)
    return v


def card_worth(card_id, g, vp):
    c = CAT[card_id]
    e = c.get("effects") or {}
    v = effect_worth(e, g, vp)
    pts = c.get("victory_points")
    v += (pts if isinstance(pts, (int, float)) else (1.5 if pts else 0)) * vp
    if e.get("action"):
        v += max(effect_worth(e["action"], g, vp), 1.0) * g * 0.6
    if e.get("discount") or e.get("cube_values") or e.get("when"):
        v += 2.0 * g
    if c["type"] != "event":
        v += len(c.get("tags") or []) * TAG_BONUS
    return v - (c.get("cost") or 0)


def player_worth(view, p, g=None):
    g = gens_left(view) if g is None else g
    vp = vp_worth(g)
    b = view["players"][p]
    v = (b["terraform_rating"]) * (vp + g)
    for r, n in b["production"].items():
        v += PROD[r] * n * g
    for r, n in b["resources"].items():
        v += STOCK[r] * n * (1.0 if g > 1 else 0.5)
    for area in view["board"]:
        t = area["tile"]
        if t and t.get("owner") == p:
            v += {"greenery": vp, "city": vp * 1.5}.get(t["type"], 0)
    for cid in b["played_cards"]:
        c = CAT[cid]
        pts = c.get("victory_points")
        v += (pts if isinstance(pts, (int, float)) else 1.5 if pts else 0) * vp
        a = (c.get("effects") or {}).get("action")
        if a:
            v += max(effect_worth(a, g, vp), 1.0) * g * 0.6
        if (c.get("effects") or {}).get("discount") or (c.get("effects") or {}).get("when"):
            v += 2.0 * g
    for m in view["milestones"]:
        if m["claimed_by"] == p:
            v += 5 * vp
    for cid in b["hand"] or []:
        v += max(card_worth(cid, g, vp), 1.0) * 0.5
    return v


def position_worth(game, me):
    view = game.player_view(me)
    return player_worth(view, me) - sum(
        player_worth(view, p) for p in range(len(view["players"])) if p != me and False
    )


def heuristic_pick(game, d, rng):
    me = d["player"]
    options = d["options"]
    if len(options) == 1:
        return 0
    kind = d["kind"]
    view = game.player_view(me)
    g = gens_left(view)
    vp = vp_worth(g)
    if kind == "corporation":
        return max(range(len(options)), key=lambda i: (CAT[options[i]["details"]["card"]]["effects"] or {}).get("resources", {}).get("megacredits", 0))
    if kind == "draft":
        return max(range(len(options)), key=lambda i: card_worth(options[i]["details"]["card"], g, vp))
    if kind == "buy_cards":
        best, score = None, 3.0
        for i, o in enumerate(options):
            if o["details"]["type"] == "buy_card":
                w = card_worth(o["details"]["card"], g, vp)
                if w > score:
                    best, score = i, w
        if best is not None:
            return best
        return next(i for i, o in enumerate(options) if o["details"]["type"] == "done")
    if kind == "sell_patents":
        for i, o in enumerate(options):
            if o["details"]["type"] == "sell_card" and card_worth(o["details"]["card"], g, vp) < -6:
                return i
        return next(i for i, o in enumerate(options) if o["details"]["type"] == "done")
    # Everything else: one step on a copy, finishing the chain of this Player's follow-up Decisions.
    best, best_v = 0, -1e18
    for i, o in enumerate(options):
        kind_of_option = o["details"]["type"]
        if kind_of_option == "end_turn":
            continue  # never wait: Pass when nothing is worth doing
        if kind_of_option == "standard_project" and "Sell Patents" in o["label"]:
            continue
        c = game.copy()
        c.pick(i)
        for _ in range(8):
            n = c.decision
            if n is None or n["player"] != me or n["kind"] == "action":
                break
            c.pick(0)
        if c.is_over:
            v = next(s["total"] for s in c.scores if s["player"] == me) * 100
        else:
            v = player_worth(c.player_view(me), me, g)  # g held fixed: see the stall note
        if kind_of_option == "pass":
            v += 0.01
        if v > best_v:
            best, best_v = i, v
    return best


def mc_pick(game, d, rng, rollouts):
    me = d["player"]
    if len(d["options"]) == 1:
        return 0
    best, best_v = 0, -1e18
    for i in range(len(d["options"])):
        total = 0.0
        for _ in range(rollouts):
            c = game.copy()
            c.pick(i)
            c.play_randomly(seed=rng.randrange(1 << 40))
            s = {x["player"]: x["total"] for x in c.scores}
            total += s[me] - max(v for p, v in s.items() if p != me)
        if total > best_v:
            best, best_v = i, total
    return best


def play(args):
    seed, a, b, rollouts, swap = args
    rng = random.Random(seed * 7 + 1)
    game = tm_engine.Game(seed=seed, players=2, draft=True)
    names = {0: b, 1: a} if swap else {0: a, 1: b}
    picks = 0
    while not game.is_over:
        if picks > 3000:
            return dict(a=0, b=0, win=0.5, gens=game.player_view(0)["generation"], picks=picks, tr=0, cards=0, stalled=1)
        d = game.decision
        who = names[d["player"]]
        if who == "random":
            i = rng.randrange(len(d["options"]))
        elif who == "heuristic":
            i = heuristic_pick(game, d, rng)
        else:
            i = mc_pick(game, d, rng, rollouts)
        game.pick(i)
        picks += 1
    s = {x["player"]: x for x in game.scores}
    pa, pb = (1, 0) if swap else (0, 1)
    return dict(
        a=s[pa]["total"], b=s[pb]["total"],
        win=1.0 if s[pa]["rank"] < s[pb]["rank"] else 0.5 if s[pa]["rank"] == s[pb]["rank"] else 0.0,
        gens=game.player_view(0)["generation"], picks=picks,
        tr=s[pa]["terraform_rating"], cards=s[pa]["cards"],
        stalled=0,
    )


def matchup(a, b, n, rollouts, pool):
    t = time.time()
    jobs = [(10_000 + i // 2, a, b, rollouts, i % 2 == 1) for i in range(n)]
    rs = pool.map(play, jobs, chunksize=1)
    mean = statistics.mean
    w = mean(r["win"] for r in rs)
    se = (w * (1 - w) / n) ** 0.5
    print(
        f"{a:10} vs {b:10} n={n:4} win {w:6.1%} ±{1.96*se:4.1%}  VP {mean(r['a'] for r in rs):5.1f}-{mean(r['b'] for r in rs):5.1f}"
        f"  gens {mean(r['gens'] for r in rs):4.1f}  picks {mean(r['picks'] for r in rs):4.0f}"
        f"  TR/cardVP(a) {mean(r['tr'] for r in rs):4.1f}/{mean(r['cards'] for r in rs):4.1f}  stalled {sum(r['stalled'] for r in rs)}  {time.time()-t:5.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", type=int, default=20)
    args = ap.parse_args()
    with mp.Pool(14) as pool:
        matchup("heuristic", "random", 400, 0, pool)
        matchup("random", "random", 2000, 0, pool)
        matchup("heuristic", "heuristic", 200, 0, pool)
        matchup("flat_mc", "random", 56, 20, pool)
        matchup("flat_mc", "flat_mc", 28, 20, pool)
        matchup("flat_mc", "heuristic", 112, 5, pool)
        matchup("flat_mc", "heuristic", 112, 20, pool)
        matchup("flat_mc", "heuristic", 56, 100, pool)

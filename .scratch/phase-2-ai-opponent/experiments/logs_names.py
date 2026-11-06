"""Which cards appear in matching Recorded Games, against the catalog. Run with python -I."""
import collections, json, multiprocessing as mp, os, random, sys
ROOT, SUMMARY, CARDS = sys.argv[1:4]
def norm(n): return "".join(ch for ch in n.lower() if ch.isalnum())
def work(item):
    fname, persp = item
    p = os.path.join(ROOT, persp, fname)
    if not os.path.exists(p): return None
    g = json.load(open(p))
    c = collections.Counter(); pre = collections.Counter(); corp = collections.Counter(); pl = collections.Counter(); sell = collections.Counter(); ndealt = collections.Counter()
    for q in g["players"].values():
        s = q.get("starting_hand") or {}
        pre.update(s.get("preludes") or []); corp.update(s.get("corporations") or []); c.update(s.get("project_cards") or [])
        ndealt[len(s.get("preludes") or [])] += 1
        pl.update(q.get("cards_played") or [])
    return pre, corp, c, pl, ndealt
if __name__ == "__main__":
    rows = [json.loads(l) for l in open(SUMMARY)]
    seen = {}
    for r in rows:
        if "error" in r or r["table"] in seen: continue
        if r["n"] == 2 and r["map"] == "Tharsis" and r["corporate"] and not r["colonies"] and r["draft"] and r["prelude"] and all(p["has_start"] for p in r["players"]): seen[r["table"]] = r
    items = [(r["file"], r["perspective"]) for r in seen.values()]
    random.Random(3).shuffle(items); items = items[:6000]
    tot = [collections.Counter() for _ in range(5)]
    with mp.Pool(14) as pool:
        for res in pool.imap_unordered(work, items, chunksize=20):
            if res:
                for t, x in zip(tot, res): t.update(x)
    pre, corp, dealt, played, nd = tot
    cat = json.load(open(CARDS)); cat = cat if isinstance(cat, list) else cat["cards"]
    names = {norm(c["name"]): c["name"] for c in cat}
    exact = {c["name"] for c in cat}
    print("Games", len(items), "preludes dealt per Player", nd.most_common(4))
    print("PRELUDES", len(pre)); print(sorted(pre.items(), key=lambda kv: -kv[1]))
    print("CORPS", len(corp)); print(sorted(corp.items(), key=lambda kv: -kv[1]))
    newp = {k: v for k, v in dealt.items() if norm(k) not in names}
    print("PROJECT cards dealt", len(dealt), "not in catalog", len(newp)); print(sorted(newp.items(), key=lambda kv: -kv[1]))
    print("played but not in catalog nor preludes", sorted(((k, v) for k, v in played.items() if norm(k) not in names and k not in pre), key=lambda kv: -kv[1])[:30])
    print("name differs only by spelling", sorted(k for k in dealt if k not in exact and norm(k) in names)[:40])
    print("catalog cards never dealt", [c["name"] for c in cat if c["type"] != "corporation" and norm(c["name"]) not in {norm(k) for k in dealt}][:20])

"""Scan every log once into one summary line per file, without keeping the moves. Run with python -I."""
import collections
import json
import multiprocessing as mp
import os
import sys
import time

ROOT, OUT = sys.argv[1], sys.argv[2]


def summarise(path):
    try:
        with open(path) as f:
            g = json.load(f)
    except Exception as e:
        return {"path": path, "error": str(e)[:100]}
    moves = g.get("moves") or []
    players = g.get("players") or {}
    types = collections.Counter(m.get("action_type") for m in moves)
    states = [m.get("game_state") for m in moves]
    with_state = sum(1 for s in states if s)
    with_trackers = sum(1 for s in states if s and s.get("player_trackers"))
    with_hands = sum(1 for s in states if s and s.get("player_hands"))
    hand_players = set()
    for s in states:
        if s and s.get("player_hands"):
            hand_players.update(s["player_hands"].keys())
    return {
        "file": os.path.basename(path),
        "table": str(g.get("table_id") or g.get("replay_id")),
        "perspective": str(g.get("player_perspective")),
        "date": g.get("game_date"),
        "n": len(players),
        "map": g.get("map"),
        "prelude": g.get("prelude_on"),
        "colonies": g.get("colonies_on"),
        "corporate": g.get("corporate_era_on"),
        "draft": g.get("draft_on"),
        "beginners": g.get("beginners_corporations_on"),
        "speed": g.get("game_speed"),
        "gens": g.get("generations"),
        "conceded": g.get("conceded"),
        "version": (g.get("metadata") or {}).get("scraper_version"),
        "players": [
            {
                "vp": p.get("final_vp"),
                "tr": p.get("final_tr"),
                "corp": p.get("corporation"),
                "arena": (p.get("elo_data") or {}).get("arena_points"),
                "rank": (p.get("elo_data") or {}).get("game_rank"),
                "breakdown": p.get("vp_breakdown"),
                "has_start": bool(p.get("starting_hand")),
                "played": len(p.get("cards_played") or []),
            }
            for p in players.values()
        ],
        "moves": len(moves),
        "types": types,
        "with_state": with_state,
        "with_trackers": with_trackers,
        "with_hands": with_hands,
        "hand_players": len(hand_players),
        "with_options": sum(1 for m in moves if m.get("card_options")),
        "with_kept": sum(1 for m in moves if m.get("cards_kept")),
        "with_drafted": sum(1 for m in moves if m.get("card_drafted")),
        "with_tile": sum(1 for m in moves if m.get("tile_location")),
    }


if __name__ == "__main__":
    t = time.time()
    paths = []
    for d in os.scandir(ROOT):
        if d.is_dir():
            paths.extend(e.path for e in os.scandir(d.path) if e.name.endswith(".json"))
    print("files", len(paths), flush=True)
    with mp.Pool(14) as pool, open(OUT, "w") as out:
        for i, s in enumerate(pool.imap_unordered(summarise, paths, chunksize=50)):
            out.write(json.dumps(s) + "\n")
            if i % 10000 == 0:
                print(i, round(time.time() - t), flush=True)
    print("done", round(time.time() - t))

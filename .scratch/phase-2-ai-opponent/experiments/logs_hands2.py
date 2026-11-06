"""Second try at rebuilding hands, from the wording of each move's description. Run with python -I."""
import collections
import json
import multiprocessing as mp
import os
import random
import re
import sys

ROOT, SUMMARY = sys.argv[1], sys.argv[2]
ENDS_RESEARCH = re.compile(r"plays card|plays standard project|passes|activates|funds |claims |first action|skips second|places |pays 8 (Heat|Plant)")


def pick_files(sample=3000):
    rows = [json.loads(l) for l in open(SUMMARY)]
    seen = {}
    for r in rows:
        if "error" in r or r["table"] in seen:
            continue
        if r["n"] == 2 and r["map"] == "Tharsis" and r["corporate"] and not r["colonies"] and r["draft"] and not r["conceded"] and (r["gens"] or 0) >= 6 and all(p["has_start"] for p in r["players"]):
            seen[r["table"]] = r
    by = {True: [], False: []}
    for r in seen.values():
        by[bool(r["prelude"])].append(r)
    rng = random.Random(7)
    out = []
    for flag, rs in by.items():
        rng.shuffle(rs)
        out.extend((flag, r["file"], r["perspective"], r["version"]) for r in rs[: sample // 2])
    return out, {k: len(v) for k, v in by.items()}


def cards_of(text):
    text = re.sub(r"^\d+ cards?:\s*", "", text.strip())
    return [c.strip() for c in text.split(", ") if c.strip()]


def rebuild(g):
    ids = list(g["players"])
    names = {g["players"][i]["player_name"]: i for i in ids}
    alt = "|".join(sorted((re.escape(n) for n in names), key=len, reverse=True))
    part_re = re.compile(rf"^({alt}|You) (keeps|draws|discards|buy|plays card) (.*)$")
    not_hand = set()
    for i in ids:
        s = g["players"][i].get("starting_hand") or {}
        not_hand.update(s.get("corporations") or [])
        not_hand.update(s.get("preludes") or [])
    hand = {i: collections.Counter() for i in ids}
    pending = {i: None for i in ids}
    research = True
    gen = 1
    each_move, end_of_gen = [], []
    played = missing = 0
    last_counter = {}

    def commit():
        for pid in ids:
            if pending[pid] is not None:
                for c in pending[pid]:
                    if c not in not_hand:
                        hand[pid][c] += 1
                pending[pid] = None

    for m in g["moves"]:
        gs = m.get("game_state") or {}
        new_gen = gs.get("generation")
        if new_gen and new_gen != gen:
            for pid in ids:
                if pid in last_counter:
                    end_of_gen.append(sum(hand[pid].values()) - last_counter[pid])
            gen = new_gen
            research = True
        d = m.get("description") or ""
        looking = bool(m.get("card_options"))
        for part in d.split(" | "):
            x = part_re.match(part.strip())
            if ENDS_RESEARCH.search(part) and research:
                commit()
                research = False
            if not x:
                continue
            who, verb, rest = x.groups()
            pid = m.get("player_id") if who == "You" else names[who]
            if pid not in hand:
                continue
            if verb == "keeps":
                cards = cards_of(rest)
                if research:
                    pending[pid] = cards
                else:
                    for c in cards:
                        hand[pid][c] += 1
            elif verb == "buy" and research:
                pending[pid] = (pending[pid] or []) + cards_of(rest)
            elif verb == "draws" and not looking:
                for c in cards_of(rest):
                    hand[pid][c] += 1
            elif verb == "discards":
                for c in cards_of(rest):
                    if hand[pid][c] > 0:
                        hand[pid][c] -= 1
            elif verb == "plays card":
                c = rest.strip()
                if c in not_hand:
                    continue
                played += 1
                if hand[pid][c] > 0:
                    hand[pid][c] -= 1
                else:
                    missing += 1
        tr = gs.get("player_trackers") or {}
        for pid in ids:
            hc = (tr.get(pid) or {}).get("Hand Counter")
            if hc is not None:
                # The counter only refreshes now and then, so compare only when it changes.
                # The trace shows it is right straight after its Player plays a card, so compare there.
                if not research and m.get("action_type") == "play_card" and m.get("player_id") == pid and last_counter.get(pid) != hc:
                    each_move.append(sum(hand[pid].values()) - hc)
                last_counter[pid] = hc
    return each_move, end_of_gen, played, missing


def work(item):
    flag, fname, perspective, version = item
    path = os.path.join(ROOT, perspective, fname)
    if not os.path.exists(path):
        return None
    g = json.load(open(path))
    e, h, played, missing = rebuild(g)
    return dict(prelude=flag, version=version, n=len(e), exact=sum(1 for x in e if x == 0), near=sum(1 for x in e if abs(x) <= 1),
                gn=len(h), gexact=sum(1 for x in h if x == 0), played=played, missing=missing, signed=sum(e) / max(len(e), 1))


if __name__ == "__main__":
    files, avail = pick_files()
    print("candidates", avail)
    with mp.Pool(14) as pool:
        rs = [r for r in pool.imap_unordered(work, files, chunksize=20) if r]
    for flag in (True, False):
        s = [r for r in rs if r["prelude"] == flag]
        tot = sum(r["n"] for r in s)
        print("Prelude" if flag else "No Prelude", "Games", len(s), "| each move exact", round(sum(r["exact"] for r in s) / tot, 3), "within 1", round(sum(r["near"] for r in s) / tot, 3),
              "| end of Generation exact", round(sum(r["gexact"] for r in s) / max(sum(r["gn"] for r in s), 1), 3),
              "| played card was in rebuilt hand", round(1 - sum(r["missing"] for r in s) / max(sum(r["played"] for r in s), 1), 3),
              "| Games with every played card known", round(sum(1 for r in s if r["missing"] == 0) / len(s), 3),
              "| Games >=95% exact", round(sum(1 for r in s if r["n"] and r["exact"] / r["n"] >= 0.95) / len(s), 3),
              "| signed", round(sum(r["signed"] for r in s) / len(s), 2))
    by = collections.defaultdict(list)
    for r in rs:
        by[r["version"]].append(r)
    for v, s in sorted(by.items(), key=lambda kv: -len(kv[1]))[:8]:
        print(v, len(s), "exact", round(sum(r["exact"] for r in s) / max(sum(r["n"] for r in s), 1), 3), "played known", round(1 - sum(r["missing"] for r in s) / max(sum(r["played"] for r in s), 1), 3))

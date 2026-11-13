"""Ticket 09: rebuild every Player's hand in the dataset's Recorded Games and measure it.

Run from the repo root: PYTHONPATH=. uv run python .scratch/phase-2-ai-opponent/experiments/hands_rebuild.py [shards]
It reads .cache/recorded-games/ (the slim moves, never the archive), on all cores, and writes one line per Game to
.cache/ticket-09/hands.jsonl, then prints the summary (see summarise()). `shards` limits the run to the first N.
"""

import gzip
import json
import multiprocessing
import sys
from collections import Counter, defaultdict
from pathlib import Path

from ai.recorded_games.dataset import DATASET_FOLDER
from ai.recorded_games.hands import PLAYERS, HandReader
from ai.recorded_games.moves import expand_moves

OUT = Path(".cache/ticket-09/hands.jsonl")


def measure(game: dict, slim: dict) -> dict:
    moves = expand_moves(slim)
    plain = HandReader(prelude=game["prelude"])
    for move in moves:
        plain.read(move)
    # With resync, at each of a Player's own Action-phase moves (a stand-in for their Decisions): how their
    # hand stands. "exact": known card by card; "sold": every card entered named, but some left unnamed
    # (Sell Patents, Mars University), so a few named cards may be gone; "unnamed": some cards entered
    # without a name (the opponent in old logs).
    reader = HandReader(prelude=game["prelude"], resync=True)
    states = [Counter() for _ in range(PLAYERS)]
    unnamed_ever = [False] * PLAYERS
    for move in moves:
        player = move.get("player")
        if player in range(PLAYERS) and not reader.buying:
            hand = reader.hands[player]
            states[player]["exact" if hand.exact else "unnamed" if hand.unnamed else "sold"] += 1
        reader.read(move)
        for place, hand in enumerate(reader.hands):
            unnamed_ever[place] |= hand.unnamed > 0
    ratings = [p.get("rating") for p in game["players"]]
    return {
        "game": game["game"],
        "version": game["scraper_version"],
        "prelude": game["prelude"],
        "conceded": game["conceded"],
        "generations": game["generations"],
        "decisions": bool(game["decisions"]),
        "rating": min((r for r in ratings if r is not None), default=None) if None not in ratings else None,
        "checks": len(plain.checks),
        "exact": sum(c.rebuilt == c.counter for c in plain.checks),
        "first_wrong": next(
            ([c.move_number, c.player, c.rebuilt, c.counter] for c in plain.checks if c.rebuilt != c.counter), None
        ),
        "errors": dict(Counter(c.rebuilt - c.counter for c in plain.checks if c.rebuilt != c.counter)),
        "resynced": reader.resynced,
        "plays": [dict(p) for p in plain.plays],
        "unnamed_ever": unnamed_ever,
        "gone": [hand.gone for hand in reader.hands],
        # Sold cards can be told in hindsight only if enough named cards are never played: those still
        # named in the hand at the end.
        "sold_assignable": [hand.cards.total() >= hand.gone for hand in reader.hands],
        "states": [dict(c) for c in states],
        "unread": plain.unread,
    }


def work(shard: Path) -> list[dict]:
    if not (shard / "shard.done").exists():
        return []
    results = []
    with gzip.open(shard / "games.jsonl.gz", "rt") as games, gzip.open(shard / "moves.jsonl.gz", "rt") as moves:
        for game_line, moves_line in zip(games, moves):
            game, slim = json.loads(game_line), json.loads(moves_line)
            assert game["game"] == slim["game"]
            results.append(measure(game, slim))
    return results


def share(part: float, whole: float) -> str:
    return f"{part / whole:.4f}" if whole else "-"


def summarise(rows: list[dict]) -> None:
    def line(label: str, group: list[dict]) -> None:
        checks = sum(r["checks"] for r in group)
        with_checks = [r for r in group if r["checks"]]
        plays = Counter()
        for r in group:
            for p in r["plays"]:
                plays.update(p)
        played = sum(plays.values())
        print(
            f"{label:30} Games {len(group):6} | checks {checks:8} exact {share(sum(r['exact'] for r in group), checks)}"
            f" (resync {share(checks - sum(r['resynced'] for r in group), checks)})"
            f" | Games all exact {share(sum(r['exact'] == r['checks'] for r in with_checks), len(with_checks))}"
            f", no checks {len(group) - len(with_checks)}"
            f" | plays: by name {share(plays['named'], played)}, unnamed {share(plays['unnamed'], played)},"
            f" missing {share(plays['missing'], played)}"
        )

    print("By setting:")
    line("all", rows)
    for prelude in (True, False):
        for conceded in (False, True):
            line(
                f"{'Prelude' if prelude else 'no Prelude'}, {'conceded' if conceded else 'not conceded'}",
                [r for r in rows if r["prelude"] == prelude and r["conceded"] == conceded],
            )
    print("\nBy scraper version:")
    by_version = defaultdict(list)
    for r in rows:
        by_version[r["version"]].append(r)
    for version, group in sorted(by_version.items(), key=lambda kv: -len(kv[1])):
        line(str(version), group)
    print(
        "\nErrors at checks (rebuilt minus counter):",
        sorted(sum((Counter(r["errors"]) for r in rows), Counter()).items()),
    )
    print("Games with unread card lines:", sum(r["unread"] > 0 for r in rows))
    states = Counter()
    for r in rows:
        for c in r["states"]:
            states.update(c)
    total = sum(states.values())
    print(
        f"\nOwn Action-phase moves {total}: hand exact {share(states['exact'], total)}, every card named but some"
        f" sold {share(states['sold'], total)}, some cards unnamed {share(states['unnamed'], total)}"
    )
    named_plays = Counter()
    for r in rows:
        for plays, unnamed in zip(r["plays"], r["unnamed_ever"]):
            if not unnamed:
                named_plays.update(plays)
    print(
        f"Plays by Players whose every card entered named: {sum(named_plays.values())}, found by name"
        f" {share(named_plays['named'], sum(named_plays.values()))}, missing"
        f" {share(named_plays['missing'], sum(named_plays.values()))}"
    )
    sellers = [(g, a) for r in rows for g, a in zip(r["gone"], r["sold_assignable"]) if g]
    print(
        f"Players with cards gone unnamed: {len(sellers)} of {PLAYERS * len(rows)};"
        f" assignable in hindsight {share(sum(a for _, a in sellers), len(sellers))}"
    )


def trust(rows: list[dict]) -> None:
    """How many Games each kind of trust leaves: "counted" (every fresh check exact, no unread line, at
    least one check); "named" (counted, and every card entering either hand named: newer versions);
    "exact" (named, and no card ever left a hand unnamed, so both hands are known card by card throughout)."""

    def counted(r: dict) -> bool:
        return r["checks"] > 0 and r["exact"] == r["checks"] and r["unread"] == 0

    def named(r: dict) -> bool:
        return counted(r) and not any(r["unnamed_ever"])

    def exact(r: dict) -> bool:
        return named(r) and not any(r["gone"])

    def strong(r: dict) -> bool:  # The spec's bands: both Players rated 500+ (450+ without Prelude).
        return r["rating"] is not None and r["rating"] >= (500 if r["prelude"] else 450)

    print(f"\n{'':34}{'all':>8}{'counted':>9}{'named':>8}{'exact':>8}")
    for prelude in (True, False):
        for label, chosen in (
            ("all", lambda r: True),
            ("not conceded", lambda r: not r["conceded"]),
            ("with Decisions", lambda r: r["decisions"]),
            ("strong, not conceded", lambda r: strong(r) and not r["conceded"]),
        ):
            group = [r for r in rows if r["prelude"] == prelude and chosen(r)]
            print(
                f"{('Prelude' if prelude else 'no Prelude') + ', ' + label:34}{len(group):8}"
                f"{sum(map(counted, group)):9}{sum(map(named, group)):8}{sum(map(exact, group)):8}"
            )


if __name__ == "__main__":
    shards = sorted((DATASET_FOLDER / "shards").glob("*"))
    if sys.argv[1:] == ["--trust"]:  # Only the trust table, from the last run's lines.
        trust([json.loads(line) for line in OUT.open()])
        sys.exit()
    if len(sys.argv) > 1:
        shards = shards[: int(sys.argv[1])]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with multiprocessing.Pool() as pool, OUT.open("w") as out:
        for results in pool.imap_unordered(work, shards):
            for row in results:
                out.write(json.dumps(row) + "\n")
            rows.extend(results)
    summarise(rows)
    trust(rows)

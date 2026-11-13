"""Ticket 09: where does Board Game Arena's Hand Counter change, and how often does the rebuilt hand agree there?

Run from the repo root: PYTHONPATH=. uv run python .scratch/phase-2-ai-opponent/experiments/hand_counter_freshness.py
For every change of a Player's counter from one move to the next (Research phases left out), it records the kind
of move: the Player's own move with a "plays card" line, their own play logged only in card_played, any other own
move, or the other Player's move; and whether the rebuilt hand's size (HandReader, no resync) equals the counter.
Also, for contrast, agreement at moves where the counter did not change, by the same kinds.
"""

import gzip
import json
import multiprocessing
import re
from collections import Counter
from pathlib import Path

from ai.recorded_games.dataset import DATASET_FOLDER
from ai.recorded_games.hands import PLAYERS, HandReader
from ai.recorded_games.moves import expand_moves


def kind(move: dict, player: int) -> str:
    if re.search(rf"(?:^|\| )Player {player + 1} plays card ", move.get("description") or ""):
        return "own 'plays card' line"
    if move.get("player") != player:
        return "the other Player's move"
    if move.get("card_played"):
        return "own play, card_played only"
    return f"own {move.get('action_type')}"


def work(shard: Path) -> Counter:
    tally = Counter()
    with gzip.open(shard / "games.jsonl.gz", "rt") as games, gzip.open(shard / "moves.jsonl.gz", "rt") as moves:
        for game_line, moves_line in zip(games, moves):
            reader = HandReader(prelude=json.loads(game_line)["prelude"])
            previous = [None] * PLAYERS
            for move in expand_moves(json.loads(moves_line)):
                reader.read(move)
                trackers = move["game_state"].get("player_trackers") or {}
                for player in range(PLAYERS):
                    counter = (trackers.get(str(player)) or {}).get("Hand Counter")
                    changed = None not in (counter, previous[player]) and counter != previous[player]
                    previous[player] = counter
                    if counter is None or reader.buying:
                        continue
                    key = ("changed" if changed else "unchanged", kind(move, player))
                    tally[key + ("all",)] += 1
                    tally[key + ("agrees",)] += reader.hands[player].size == counter
    return tally


if __name__ == "__main__":
    tally = Counter()
    with multiprocessing.Pool() as pool:
        for part in pool.imap_unordered(work, sorted((DATASET_FOLDER / "shards").glob("*"))):
            tally.update(part)
    for state in ("changed", "unchanged"):
        rows = sorted(((k[1], v) for k, v in tally.items() if k[0] == state and k[2] == "all"), key=lambda kv: -kv[1])
        total = sum(v for _, v in rows)
        print(f"Counter {state}: {total} Player-moves")
        for name, count in rows[:8]:
            print(
                f"  {name:32} {count:9} ({count / total:.4f})"
                f"  rebuild agrees {tally[(state, name, 'agrees')] / count:.4f}"
            )

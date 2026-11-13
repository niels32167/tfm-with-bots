"""Recorded Games: the Board Game Arena archive turned into a compact, private dataset (ADR 0012).

Build it with `uv run python -m ai.recorded_games` (see build.py), read it with dataset.read_games() and
read_moves(), and compare it with the spec and tfmstats.com with `uv run python -m ai.recorded_games.tables`.

The dataset is .cache/recorded-games/, out of git: never publish it or anything trained from it.
- shards/NNN/games.jsonl.gz: one Game per line, in the format below.
- shards/NNN/moves.jsonl.gz: the same Games' slim moves (ai.recorded_games.moves), for tickets 09 and 10.
  They name both Players' cards, as the logs do: raw material, never training data as they stand.
- salt: the secret behind the anonymous ids. Keep it to follow Players across rebuilds.
- coverage.json and report.txt: what the build read, kept and skipped, and why.

A Game (format 1):
- "game": an anonymous id; "date" (None if the log's is invalid); "scraper_version";
  "prelude", "conceded" and "generations". Every Game is 2 Players on Tharsis with Corporate Era and the
  Draft, without Colonies or the Beginner Corporation.
- "players": for each Player, in the log's order, which Decisions and positions index from 0: an
  anonymous "id", Board Game Arena's "rating" (game_rank) and "rating_change", "corporation",
  "victory_points", "points" (by source: tr, awards, milestones, cities, greeneries, cards), "winner".
  No names.
- "milestones" and "awards": each claimed or funded, by "player", in which "generation".
- "positions": the public positions Decisions point to. Positions[0] is the start, as the rules set it
  up; then one per Research phase, after its Production phase: "generation", "temperature", "oxygen", "oceans", "milestones" and
  "awards" (id -> player), and per Player "corporation", "terraform_rating", "resources" and
  "production" (megacredits, steel, titanium, plants, energy, heat), "tags", "events" played,
  "hand_counter" (Board Game Arena's, often stale), and the Project Cards ("played") and Prelude Cards
  ("prelude_cards") played so far. Research-phase Resources are worked out from the previous
  Generation's last trackers, which lag the play.
- "decisions": in the order made, each one Player's, holding only what that Player could see:
  - "setup": "offer" {"corporations", "prelude_cards", "cards"} dealt, "picked" {"corporation",
    "prelude_cards", "cards"} kept.
  - "draft": "pick" (1 to 3; the 4th card comes by itself), "offer" (the hand), "picked", "drafted"
    (this Generation's picks so far), "passed" (every card passed on this Game, [{"generation",
    "cards"}], as in the Player View).
  - "buy": "offer" (the 4 cards drafted), "picked" (those kept, maybe none), "passed".
  Each has "kind", "player", "generation" and "position" (an index into "positions"). Cards are catalog ids.
  Not in these records, because Recorded Games don't give them reliably: the Player's hand (rebuilt from
  the moves by ai.recorded_games.hands, ticket 09) and the board's Tiles (ticket 10, from the moves).
  Action-phase Decisions will be further kinds.
"""

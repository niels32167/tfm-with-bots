"""Terraforming Mars rules engine (Rust, built with PyO3).

Everything returned is plain, JSON-serializable data: dicts, lists, strings, numbers
and None. Players are indexed from 0; their names ("Player 1", ...) count from 1.
"""

from typing import Any

MAX_SEED: int
"""The largest seed, 2**53 - 1: Replays travel as JSON, and some JSON readers (the
browser's among them) keep whole numbers exact only up to there."""

class Game:
    """A Game of Terraforming Mars, always either over or waiting on one Decision."""

    def __init__(self, *, seed: int, players: int = 2) -> None:
        """A new Game from its settings; the first player is drawn from the seed.

        Raises ValueError for an unsupported Player count or a seed above MAX_SEED.
        """

    @staticmethod
    def from_scenario(scenario: dict[str, Any]) -> Game:
        """A Game started from a Scenario. Anything left out takes the normal defaults.

        Fields: seed, generation, first_player (default 0, who also takes the first Turn),
        temperature, oxygen, tiles, milestones, awards, and players: a list of
        {"resources": {...}, "production": {...}, "terraform_rating": int}.
        Resources and Production name any of the six Resources (megacredits, steel,
        titanium, plants, energy, heat); the rest keep their defaults: 42 MegaCredits and
        nothing else to start with, and no Production.
        Each Tile is {"area": "C3", "tile": "ocean" | "greenery" | "city", "owner": 0};
        Oceans have no owner, and the number of Oceans is the number of Ocean Tiles.
        Milestones claimed are {"milestone": "mayor", "claimed_by": 1} and Awards funded
        {"award": "landlord", "funded_by": 0}: at most three of each, each at most once.
        Raises ValueError for unknown fields or impossible values, such as a negative
        Resource, MegaCredit Production below -5 or any other Production below 0, a City on
        an Area reserved for Oceans, or more than 9 Oceans.
        """

    @staticmethod
    def from_replay(replay: dict[str, Any], step: int | None = None) -> Game:
        """The Game a Replay describes, rebuilt by replaying its picks from the start.

        With `step`, only the first `step` picks are replayed (step 0 is the Game before
        any pick). Raises ValueError for a Replay that isn't one, a pick the Game doesn't
        offer, or a step beyond the end.
        """

    def copy(self) -> Game:
        """An independent copy: changing either Game never changes the other."""

    @property
    def players(self) -> int:
        """How many Players the Game has."""

    @property
    def seed(self) -> int:
        """The seed this Game was created with."""

    @property
    def decision(self) -> dict[str, Any] | None:
        """The Decision the Game is waiting on, or None once it is over.

        {"player": int, "kind": str, "sequence": int,
         "options": [{"index": int, "label": str, "details": {"type": str, ...}}]}

        Kinds: "action" (an Action, End Turn or Pass), "area" (where to place a Tile,
        with details {"type": "area", "area": "C3", "tile": "city"}) and "final_greenery"
        (convert 8 plants into a Greenery once more, or be done, after the final Production
        phase). Claiming a Milestone and funding an Award are Actions, with details
        {"type": "claim_milestone", "milestone": "mayor", "cost": 8} and
        {"type": "fund_award", "award": "landlord", "cost": 14}.
        """

    def pick(self, index: int, sequence: int | None = None) -> None:
        """Answers the current Decision with its Option at `index`.

        Pass the Decision's `sequence` to have a stale pick rejected. Raises ValueError
        for a stale pick, an index that isn't offered, or a Game that is over.
        """

    @property
    def replay(self) -> dict[str, Any]:
        """The Replay so far: where this Game started and the index of every Option picked.

        {"start": {"settings": {"players": int, "seed": int}} or {"scenario": {...}},
         "picks": [int, ...]}
        """

    def player_view(self, player: int) -> dict[str, Any]:
        """Everything `player` is allowed to know. Its "viewer" is `player`.

        It has the Generation, the phase ("action", "final_greenery" or "over"), the Global
        Parameters (temperature, oxygen, oceans) and each Player's board:
        {"name": "Player 1", "resources": {...}, "production": {...}, "terraform_rating": int,
         "passed": bool}, where Resources and Production each hold all six Resources.
        It also has the "board": every Area, on Mars row by row from the
        top (A to J, skipping I) and each row from the left, then the two Areas off Mars:
        {"area": "E3", "name": "Noctis City" | None, "row": 5, "position": 3,
         "reserved": "ocean" | "noctis_city" | ... | None, "bonus": ["plant", "plant"],
         "tile": {"type": "city", "owner": 0} | None}
        and the five "milestones" and five "awards" in the order printed on the board:
        {"milestone": "mayor", "name": "Mayor", "condition": "Owning at least 3 Cities",
         "target": 3, "claimed_by": int | None, "counts": [int per Player]} and
        {"award": "landlord", "name": "Landlord", "condition": "...", "funded_by": int | None,
         "counts": [int per Player]}, where counts are each Player's progress or standing.
        "milestone_cost" (8) and "award_cost" (8, 14 or 20) are None once three are
        claimed or funded. "scores" is None until the Game is over.
        """

    def full_view(self) -> dict[str, Any]:
        """Everything about the Game, including what Players hide from each other.

        For Hotseat and the dev panel, never for an AI Controller. It has the Player
        View's shape, with "viewer" None.
        """

    @property
    def log(self) -> list[str]:
        """The game log: one plain-language line for each thing that has happened."""

    @property
    def is_over(self) -> bool:
        """Whether the Game is over."""

    @property
    def scores(self) -> list[dict[str, Any]] | None:
        """Each Player's final score once the Game is over, otherwise None.

        {"player": int, "terraform_rating": int, "milestones": int, "awards": int,
         "greeneries": int, "cities": int, "cards": int, "total": int,
         "megacredits": int, "rank": int}
        The six Victory Point counts add up to "total". "rank" is 1 for the winner: the
        most Victory Points, then the most MegaCredits; Players tied on both share a rank.
        """

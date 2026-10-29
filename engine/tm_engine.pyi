"""Terraforming Mars rules engine (Rust, built with PyO3).

Everything returned is plain, JSON-serializable data: dicts, lists, strings, numbers
and None. Players are indexed from 0; their names ("Player 1", ...) count from 1.
"""

from typing import Any

MAX_SEED: int
"""The largest seed, 2**53 - 1: Replays travel as JSON, and some JSON readers (the
browser's among them) keep whole numbers exact only up to there."""

def card_catalog() -> list[dict[str, Any]]:
    """The card catalog: the printed data of every v1 card, the 208 Project Cards in number
    order and then the 12 Corporations. Each card has "id" (how Scenarios, Option details and
    Replays name it), "number" (None for Corporations), "name", "type" ("automated", "active", "event" or
    "corporation"), "corporate_era", "cost" (None for Corporations), "tags", "requirements",
    "victory_points", "text", and "face": the card's middle part as the card list draws it,
    for the GUI. Implemented cards also have "effects": what they do when played, with any of
    "resources" and "production" (amounts of the six Resources, below zero to lose),
    "production_per" (Production raised per Tag or Tile, such as {"resource": "megacredits",
    "steps": 1, "per": 1, "of": {"tag": "earth"}}), "production_choice" (Production changes
    the Player chooses one of, such as [{"plants": 1}, {"energy": 2}]), "temperature" and
    "oxygen" (steps raised), "terraform_rating", "draw" (cards) and "tiles" (a list such as
    ["ocean", "ocean"], with {"tile": "greenery", "on": "ocean_areas"} for a Tile that goes on
    other Areas than usual: "ocean_areas", "land" or "next_to_two_cities"). Cards without
    "effects" are never offered; a few cards also have Rust code of their own (Robotic
    Workforce). Each call returns a new list."""

class Game:
    """A Game of Terraforming Mars, always either over or waiting on one Decision."""

    def __init__(
        self, *, seed: int, players: int = 2, implemented_cards_first: bool = False, draft: bool = True
    ) -> None:
        """A new Game from its settings; the first player is drawn from the seed. It begins with
        the setup buy: each Player is dealt 10 Project Cards from the shuffled deck to buy from.
        From Generation 2, each Research phase has the Draft unless `draft` is False. While most
        cards are not implemented yet, `implemented_cards_first` puts the implemented ones, shuffled,
        on top of the deck.

        Raises ValueError for an unsupported Player count or a seed above MAX_SEED.
        """

    @staticmethod
    def from_scenario(scenario: dict[str, Any]) -> Game:
        """A Game started from a Scenario. Anything left out takes the normal defaults.

        Fields: seed, generation, first_player (default 0, who also takes the first Turn),
        temperature, oxygen, tiles, milestones, awards, deck, discard, draft (default True:
        whether the Research phases have the Draft), and players: a list of
        {"resources": {...}, "production": {...}, "terraform_rating": int,
         "hand": [card id, ...], "played_cards": [card id, ...]}.
        Cards are named by their catalog id ("black_polar_dust"); only Project Cards, each in
        one place at most. "deck" lists the cards on top of the deck, the first drawn first;
        every other Project Card is shuffled beneath them with the seed. "discard" lists the cards
        in the discard pile. A Scenario starts in the Action phase.
        Resources and Production name any of the six Resources (megacredits, steel,
        titanium, plants, energy, heat); the rest keep their defaults: 42 MegaCredits and
        nothing else to start with, and no Production.
        Each Tile is {"area": "C3", "tile": "ocean" | "greenery" | "city", "owner": 0};
        Oceans have no owner, and the number of Oceans is the number of Ocean Tiles.
        Milestones claimed are {"milestone": "mayor", "claimed_by": 1} and Awards funded
        {"award": "landlord", "funded_by": 0}: at most three of each, each at most once.
        Raises ValueError for unknown fields or impossible values, such as a negative
        Resource, MegaCredit Production below -5 or any other Production below 0, a
        Terraform Rating below 5 (so MegaCredits never go below 0), a City on
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

        Kinds: "action" (an Action, End Turn or Pass), "payment" (how to pay for the card
        being played, with details {"type": "payment", "card": "mine", "megacredits": 2,
        "steel": 1, "titanium": 0}; it comes only when there is more than one way), "area"
        (where to place a Tile, with details {"type": "area", "area": "C3", "tile": "city"}, plus
        "on" for a Tile that goes on other Areas than usual: "ocean_areas", any free Area reserved
        for Oceans, as Mangrove's Greenery does; "land", any free Area reserved for nothing, as
        Artificial Lake's Ocean does; "next_to_two_cities", free land next to at least 2 Cities,
        as Urbanized Area's City does), "production" (the Production change the card being
        played makes: {"type": "choose_production", "card": "artificial_photosynthesis",
        "production": {...}} with all six Resources, or the building card whose production box
        Robotic Workforce copies, {"type": "copy_production_box", "card": "mine"}; it comes only
        when there is more than one change to choose from),
        "final_greenery" (convert 8 plants into a Greenery once more, or be done, after
        the final Production phase), "draft" (keep one of the cards being drafted and pass the
        rest on, with details {"type": "draft_card", "card": "mine"}), "buy_cards" (buy one more
        of the cards dealt or drafted, {"type": "buy_card", "card": "mine", "cost": 3}, or be
        done) and "sell_patents" (sell one more card from the hand, {"type": "sell_card", "card":
        "mine", "megacredits": 1}, or be done). Being done is {"type": "done"}. Playing a card,
        claiming a Milestone and funding an Award are Actions, with details
        {"type": "play_card", "card": "mine", "cost": 4},
        {"type": "claim_milestone", "milestone": "mayor", "cost": 8} and
        {"type": "fund_award", "award": "landlord", "cost": 14}.
        """

    def pick(self, index: int, sequence: int | None = None) -> None:
        """Answers the current Decision with its Option at `index`.

        Pass the Decision's `sequence` to have a stale pick rejected. Raises ValueError
        for a stale pick, an index that isn't offered, or a Game that is over.
        """

    def play_randomly(self, *, seed: int, picks: int | None = None) -> None:
        """Plays on with a Random Bot for every Player, inside the engine: random Options,
        `picks` of them or until the Game is over (a Game that is over picks nothing).

        The same `seed` always picks the same way from the same position. The picks go
        into the Replay like any others. For the speed benchmark and, later, search.
        """

    @property
    def replay(self) -> dict[str, Any]:
        """The Replay so far: where this Game started and the index of every Option picked.

        {"start": {"settings": {"players": int, "seed": int, "implemented_cards_first": bool,
         "draft": bool}} or {"scenario": {...}},
         "picks": [int, ...]}
        """

    def player_view(self, player: int) -> dict[str, Any]:
        """Everything `player` is allowed to know. Its "viewer" is `player`.

        It has the Generation, the phase ("setup", "draft", "research", "action",
        "final_greenery" or "over"), the Global Parameters (temperature, oxygen, oceans) and each
        Player's board:
        {"name": "Player 1", "resources": {...}, "production": {...}, "terraform_rating": int,
         "passed": bool, "hand_size": int, "hand": [card id, ...] | None,
         "buying": {"dealt": [...], "bought": [...]} | None,
         "drafting": {"picking_from": [...], "kept": [...], "passing_to": int} | None,
         "passed_in_draft": [{"generation": int, "to": int, "cards": [...]}, ...] | None,
         "played_cards": [card id, ...], "tags": {"building": int, ...}}, where Resources and
        Production each hold all six Resources, cards come in card-number order, and "tags"
        counts the ten Tags in play (on played Automated and Active cards; no Tag on a played
        Event counts). "hand", "buying", "drafting" and "passed_in_draft" are None but on the
        viewer's own board. "buying" is the cards dealt to buy from and those bought so far, in
        the setup and Research phases. "drafting" is the cards being drafted, keeping one and
        passing the rest to Player "passing_to", and those kept so far, in the Draft.
        "passed_in_draft" lists every set of cards the Player passed on in the Draft this Game,
        in the order passed. "deck_size" and "discard_size" are the numbers of cards in the deck
        and the discard pile, and "deck" and "discard" are None.
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
        View's shape, with "viewer" None, every Player's "hand", "buying", "drafting" and
        "passed_in_draft", the "deck" by catalog id from the top down, and the "discard" pile.
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

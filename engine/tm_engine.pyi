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
    "steps": 1, "per": 1, "of": {"tag": "earth"}}), "production_at_least" (Production raised
    only with at least so many of something, such as {"resource": "plants", "steps": 3,
    "at_least": 3, "of": {"tag": "plant"}}), "production_choice" (Production changes the Player
    chooses one of, such as [{"plants": 1}, {"energy": 2}]), "temperature" and "oxygen" (steps
    raised), "terraform_rating", "terraform_rating_per" (Terraform Rating raised per Tag, such as
    {"steps": 1, "per": 1, "of": {"tag": "jovian"}}), "draw" (cards), "look_at" (cards looked at
    from the top of the deck, some kept and the rest discarded, such as {"cards": 4, "keep": 2},
    or some bought at 3 MegaCredits each, {"cards": 1, "buy": 1}) and "tiles" (a list such as
    ["ocean", "ocean"], with {"tile": "greenery", "on": "ocean_areas"} for a Tile that goes on
    other Areas than usual: "ocean_areas", "land", "next_to_two_cities", "next_to_no_other_tile",
    "next_to_a_city", "next_to_a_greenery", "volcanoes", "steel_or_titanium_bonus",
    "steel_or_titanium_bonus_next_to_own_tile", or a card's reserved Area, "noctis_city",
    "phobos_space_haven" or "ganymede_colony"; "special" is the card's special Tile, printed with
    its symbol, and Capital's City is its special Tile too) and "claim_area" (true for Land Claim,
    whose Player claims an Area only they may place a Tile on), and "choice" (effects the Player
    chooses one of once the Tiles are placed, Imported Hydrogen's [{"resources": {"plants": 3}},
    {"add_to_another": [...]}, ...]; the same shapes again). An Active card's
    action is "action", the same shapes again (its cost as Resources lost), plus "pay" (MegaCredits
    that steel or titanium may pay, such as {"megacredits": 12, "titanium": true}),
    "resources_per" (Resources gained per Tag or Tile, such as {"resource": "megacredits",
    "amount": 1, "per": 1, "of": {"tiles_on_mars": "city"}}), "resources_choice" (Resource changes
    the Player chooses one of) and "choice" (effects the Player chooses one of, each the same
    shapes again: [{"card_resources": 1}, {"card_resources": -2, "oxygen": 1}]). A card that holds
    Card Resources has "holds" ("microbe", "science", "animal" or "fighter"), and any effects may
    have "card_resources" (added to the card itself, below zero to remove them) and "add_to_another"
    (added to other cards of the Player's, of their picking, a list of {"kind": "microbe",
    "amount": 2}; "kind" left out for any kind, "at_least" for only a card with so many on it,
    and "must_have_card": true if the effects can't be carried out without such a card; otherwise
    they are lost). An Active card's ongoing effects are "discount"
    (MegaCredits off each card its Player plays, or only those with a Tag: {"megacredits": 2,
    "tag": "space"}), "cube_values" (MegaCredits more that each steel and titanium pays: {"steel":
    1, "titanium": 1}), "requirement_steps" (how many steps easier its Player's Requirements on a
    Global Parameter are) and "when" (Triggers: what its Player gains each time something happens,
    such as [{"on": {"tile_placed": {"tile": "ocean", "by": "anyone"}}, "resources": {"plants":
    2}}], "on" being {"tile_placed": {"tile", "by": "you" | "anyone"}}, {"card_played": {"type",
    "tag"}} (either may be left out), {"tag_played": ["animal", "plant"]} (once per such Tag) or
    "standard_project" (any but Sell Patents), with "resources", "production" and "card_resources"
    (on the card itself) gained). An
    Event's "next_card" ({"discount": 8} or {"requirement_steps": 2}) changes the next card its
    Player plays this Generation. A card that takes from a Player its Player picks has
    "any_player", once its Tiles are placed: {"production": {"heat": -2}} (Production lowered, on a
    Player who can lose every step), {"remove": [{"plants": 3}]} (Resources removed up to these
    amounts, as one of the alternatives listed: Sabotage lists three; {"card_resource": "animal",
    "amount": 2} is up to so many from one of a Player's cards, Virus), {"steal": [...]} (removed
    and gained, Hired Raiders) or, only in an action, {"move_card_resource": "microbe"} (1 moved
    from any card to this one, Ants and Predators). Besides Tags ({"tag": "earth"}) and Tiles ({"tiles_in_play":
    "city"}, {"tiles_on_mars": "city"}, and for Victory Points the Tiles next to the card's own Tile,
    {"adjacent": "ocean"}), "of" may count the opponents' Tags ({"tags_of_opponents":
    "space"}), every Event played ("events_played") or for Victory Points the Card Resources on the
    card ({"card_resource": "microbe"}). Cards without "effects" are never offered; a few cards also
    have Rust code of their own (Robotic Workforce, Insulation, Power Infrastructure, Immigrant City,
    Mars University, Flooding, Mining Area, Mining Rights, Olympus Conference, Search for Life, Pets,
    Protected Habitats and Viral Enhancers).
    Each call returns a new list."""

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
         "hand": [card id, ...], "played_cards": [card id, ...],
         "card_resources": {card id: int, ...}}, the Card Resources on their played cards that
        hold some.
        Cards are named by their catalog id ("black_polar_dust"); only Project Cards, each in
        one place at most. "deck" lists the cards on top of the deck, the first drawn first;
        every other Project Card is shuffled beneath them with the seed. "discard" lists the cards
        in the discard pile. A Scenario starts in the Action phase.
        Resources and Production name any of the six Resources (megacredits, steel,
        titanium, plants, energy, heat); the rest keep their defaults: 42 MegaCredits and
        nothing else to start with, and no Production.
        Each Tile is {"area": "C3", "tile": "ocean" | "greenery" | "city", "owner": 0}, and a
        special Tile names its card, {"area": "C4", "tile": "special", "card": "nuclear_zone",
        "owner": 0} (Capital's is a "city" with "card": "capital"); Oceans have no owner, and the
        number of Oceans is the number of Ocean Tiles. "land_claim" is the Area claimed with
        Land Claim, {"area": "C3", "player": 1}.
        Milestones claimed are {"milestone": "mayor", "claimed_by": 1} and Awards funded
        {"award": "landlord", "funded_by": 0}: at most three of each, each at most once.
        Raises ValueError for unknown fields or impossible values, such as Card Resources on a
        card not played or that holds none, a negative Resource, MegaCredit Production below -5 or any other Production below 0, a
        Terraform Rating below 5 (so MegaCredits never go below 0), a City on
        an Area reserved for Oceans (only Mohole Area's Tile goes there, and only a City on an
        Area reserved for a card's City), or more than 9 Oceans.
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
        "steel": 1, "titanium": 0}, or for the action being used, with "action": true as well; it
        comes only when there is more than one way), "area"
        (where to place a Tile, with details {"type": "area", "area": "C3", "tile": "city"}, plus
        "on" for a Tile that goes on other Areas than usual: "ocean_areas", any free Area reserved
        for Oceans, as Mangrove's Greenery does; "land", any free Area reserved for nothing, as
        Artificial Lake's Ocean does; "next_to_two_cities", free land next to at least 2 Cities,
        as Urbanized Area's City does; "next_to_no_other_tile", free land next to no Tile, as
        Research Outpost's City does; the other "on" of the card file's "tiles" likewise; and
        "card" for a special Tile, such as "nuclear_zone"; or the Area Land Claim claims,
        {"type": "claim_area", "area": "C3"}), "production" (the Production change the card being
        played makes: {"type": "choose_production", "card": "artificial_photosynthesis",
        "production": {...}} with all six Resources, or the building card whose production box
        Robotic Workforce copies, {"type": "copy_production_box", "card": "mine"}; it comes only
        when there is more than one change to choose from), "keep_cards" (keep one more of the
        cards the card being played lets its Player look at, {"type": "keep_card", "card":
        "mine"}; it comes only when there are more cards than they keep; or buy one of the cards
        the action being used lets them look at, {"type": "buy_card", "card": "mine", "cost": 3},
        or be done and discard them; it comes only when they can pay for one), "resources"
        (the Resource change the action being used makes, {"type": "choose_resources", "card":
        "electro_catapult", "resources": {...}} with all six Resources; it comes only when there
        is more than one to choose from), "effects" (the effects the card being played or the action
        being used carries out, {"type": "choose_effects", "card": "regolith_eaters", "alternative":
        1}, the index in its "choice"; it comes only when there is more than one it can carry out),
        "viral_enhancers" (add 1 Card Resource to the card played or gain 1 plant, {"type":
        "viral_enhancers", "card": "fish", "add": true}, once for each plant, microbe or animal Tag on
        a card that holds Card Resources, after what else the card does), "add_to_card" (which of
        the Player's cards gets the Card Resources being added, {"type": "add_card_resources", "card":
        "aerobraked_ammonia_asteroid", "to": "tardigrades", "kind": "microbe", "amount": 2}; it
        comes only with more than one such card), "olympus_conference" (add a science to Olympus
        Conference or remove one to draw a card, {"type": "olympus_conference", "card":
        "olympus_conference", "draw": true}, once for each science Tag played once it
        has one to remove; with a Mars University discard due and a card in the hand, its Options
        too, so that the Player orders the two by picking either),
        "final_greenery" (convert 8 plants into a Greenery once more, or be done, after
        the final Production phase), "draft" (keep one of the cards being drafted and pass the
        rest on, with details {"type": "draft_card", "card": "mine"}), "buy_cards" (buy one more
        of the cards dealt or drafted, {"type": "buy_card", "card": "mine", "cost": 3}, or be
        done), "sell_patents" (sell one more card from the hand, {"type": "sell_card", "card":
        "mine", "megacredits": 1}, or be done) and "discard_to_draw" (discard a card from the hand
        to draw one, {"type": "discard_card", "card": "mine"}, or be done, once for each science
        Tag played with Mars University in play) and "target" (whom the card being played takes
        from, once its Tiles are placed: {"type": "lower_production", "card": "heat_trappers",
        "player": 1, "production": {...}}, {"type": "remove_resources", "card": "sabotage", "player":
        1, "resources": {...}} with "stolen": true for Hired Raiders, the changes to that Player with
        all six Resources, or {"type": "remove_nothing", "card": "sabotage"}; or the card the action
        being used moves a Card Resource from, {"type": "move_card_resource", "card": "ants",
        "player": 1, "from": "tardigrades", "kind": "microbe"}; it comes only when there is more
        than one Option, so for Production only with two targets or more). Being done is {"type": "done"}. Playing a card,
        using a played card's action, claiming a Milestone and funding an Award are Actions, with
        details {"type": "play_card", "card": "mine", "cost": 4} (the cost after discounts),
        {"type": "use_action", "card": "space_elevator"},
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
         "card_costs": {card id: int} | None,
         "buying": {"dealt": [...], "bought": [...]} | None,
         "drafting": {"picking_from": [...], "kept": [...], "passing_to": int} | None,
         "passed_in_draft": [{"generation": int, "to": int, "cards": [...]}, ...] | None,
         "keeping": {"card": card id, "looking_at": [...], "kept": [...], "keep": int,
                     "price": int} | None,
         "played_cards": [card id, ...], "used_actions": [card id, ...],
         "card_resources": {card id: int},
         "next_card": card id | None,
         "tags": {"building": int, ...}}, where Resources and
        Production each hold all six Resources, cards come in card-number order, and "tags" counts
        the ten Tags in play (on played Automated and Active cards; no Tag on a played Event
        counts). "hand", "buying", "drafting", "passed_in_draft" and "keeping" are None but on the
        viewer's own board. "buying" is the cards dealt to buy from and those bought so far, in the
        setup and Research phases. "drafting" is the cards being drafted, keeping one and passing
        the rest to Player "passing_to", and those kept so far, in the Draft. "passed_in_draft"
        lists every set of cards the Player passed on in the Draft this Game, in the order passed.
        "keeping" is, while the Player plays a card such as Business Contacts, the cards they look
        at and may still keep, those kept so far, and how many more they keep; the rest are
        discarded. Using the action of Inventors' Guild or Business Network, it has the "price"
        of each card, 3, and "keep" is how many more they may buy; otherwise "price" is 0.
        "used_actions" is the played cards whose action the Player has used this Generation.
        "card_resources" is how many Card Resources are on each of their played cards that can hold
        some, even if none are on it.
        "card_costs" is what the Player would pay now for each card in their hand, once their
        discounts are taken off; it is None where "hand" is. "next_card" is the Event the Player
        played whose effect waits on the next card they play this Generation (Indentured Workers,
        Special Design), or None.
        "deck_size" and "discard_size" are the numbers of cards in the deck and the discard pile,
        and "deck" and "discard" are None.
        It also has the "board": every Area, on Mars row by row from the
        top (A to J, skipping I) and each row from the left, then the two Areas off Mars:
        {"area": "E3", "name": "Noctis City" | None, "row": 5, "position": 3,
         "reserved": "ocean" | "noctis_city" | ... | None, "bonus": ["plant", "plant"],
         "tile": {"type": "city", "owner": 0} | None, "claimed_by": 1 | None}
        where a special Tile also names its card, {"type": "special", "card": "nuclear_zone",
        "owner": 0} (Capital's City is {"type": "city", "card": "capital", ...}), and "claimed_by"
        is the Player who claimed the Area with Land Claim;
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

        For Hotseat and the dev panel, never for an AI Controller. It has the Player View's shape,
        with "viewer" None, every Player's "hand", "card_costs", "buying", "drafting",
        "passed_in_draft" and "keeping", the "deck" by catalog id from the top down, and the
        "discard" pile.
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

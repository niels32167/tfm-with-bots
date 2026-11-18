"""Recorded Games replayed through the engine (ticket 10 of phase 2).

A Game starts from a chosen deal: the Corporations, Prelude Cards and Project Cards in the order the log
shows them dealt and drawn. Each Decision the engine asks is then answered from the log:
- setup, Draft and buy Decisions from the dataset's Decision records (ticket 08);
- each Action's main choice from its "anchor" line ("plays card X", "activates X", "passes", …);
- the choices within an Action (an Area, a payment, a card kept) from the lines that follow its anchor;
- cards sold or discarded without a name, in hindsight, from cards their Player never plays later;
- any other choice by trying each Option and keeping the one that leaves the trackers as the log does.

After each Action, the trackers that changed during it are compared with the engine's, and the Game stops
at its first difference, so that one difference doesn't cascade. The result keeps the engine's Replay up
to that point: every Decision in it has the engine's own Options and Player View.

This module imports the engine: it builds data and is never a Controller (tests/ai/test_fair_play.py).
"""

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import cache
from typing import Any

import tm_engine

from ai.recorded_games.hands import Keep
from ai.recorded_games.moves import expand_moves
from ai.recorded_games.names import award_id, card_id, catalog, milestone_id

PLAYERS = 2

SUBJECT = re.compile(r"^(?:private: )?Player ([12]) (.*)$")
# A line naming a Player some other way: a renamed account's old name, before what it does.
OLD_NAME = re.compile(
    r"^(\S.*?) ((?:pays|plays card|plays standard project|gains|increases|reduces|places|draws|drafts|keeps|discards"
    r"|activates|passes|claims|funds|adds|removes|skips|reveals|loses|moves) .*|passes)$"
)
STARTING_PLAYER = re.compile(r"Player ([12]) is starting player for this generation")
LISTED = re.compile(
    r"^(?:draws|keeps|reveals|drafts|keep|buy) (?:(\d+) cards?(?:/s)?: )?(.*?)(?:: it (?:has|does not have) .*)?$"
)

# Board Game Arena writes an Area as (x, y): y is the row from the top, from 1, and x counts from a point
# left of the board, so each row's first Area has its own x.
ROW_LETTERS = "ABCDEFGHJ"
ROW_STARTS = (3, 3, 2, 2, 1, 2, 2, 3, 3)
OFF_MARS = {(0, 2): "phobos_space_haven", (0, 3): "ganymede_colony"}
PLACED = re.compile(r"^places (?:tile )?(.+?) (?:on|into) (.*?) ?(?:\((\d+),(\d+)\))?$")
# Areas some logs name without coordinates.
NAMED_AREAS = {
    "Tharsis Tholus": "B2",
    "Ascraeus Mons": "C1",
    "Pavonis Mons": "D1",
    "Arsia Mons": "E1",
    "Noctis City": "E3",
    "Phobos Space Haven": "phobos_space_haven",
    "Ganymede Colony": "ganymede_colony",
}
LOCATION = re.compile(r"\((\d+),(\d+)\)$")
PAID = re.compile(r"pays (\d+) (M€|Steel|Titanium|Heat)(?: \(.*\))?")
# Some versions give a discard's reason, some don't.
SOLD = re.compile(r"^discards (\d+) card/s(?: \(Sell patents\))?$")
ONE_CARD_DRAWN = re.compile(r"^draws (?!\d+ cards)(?!.*, )(.+)$")
MARS_UNIVERSITY_DISCARD = re.compile(r"^discards (1 card/s|a card)(?: \(triggered effect of Mars University\))?$")
# A line's verb, and the word an alternative's label begins with if it does that.
EFFECT_VERBS = {
    "gains": "Gain",
    "adds": "Add",
    "removes": "Remove",
    "draws": "Draw",
    "increases": "Raise",
    "reduces": "Lower",
}
EFFECT_LINE = re.compile(r"^(gains|adds|removes|draws|increases|reduces) (?:\d+ )?(\w+)")
LOST = re.compile(r"^(?:pays|loses) \d+ (Plant|Steel|Titanium|M€|Heat|Energy)( \(immediate effect of [^)]+\))?$")
LOWERED = re.compile(r"^reduces (M€|Steel|Titanium|Plant|Energy|Heat) Production by (\d+)")
RESOURCE_KEYS = {
    "M€": "megacredits",
    "Steel": "steel",
    "Titanium": "titanium",
    "Plant": "plants",
    "Energy": "energy",
    "Heat": "heat",
}
ACTIVATION_OF = re.compile(r"activation effect of ([^)]+)")

STANDARD_PROJECTS = {
    "sellpatents": "sell_patents",
    "powerplant": "power_plant",
    "asteroid": "asteroid",
    "aquifer": "aquifer",
    "greenery": "greenery",
    "city": "city",
}

TRACKERS = {
    "M€": ("resources", "megacredits"),
    "Steel": ("resources", "steel"),
    "Titanium": ("resources", "titanium"),
    "Plant": ("resources", "plants"),
    "Energy": ("resources", "energy"),
    "Heat": ("resources", "heat"),
    "M€ Production": ("production", "megacredits"),
    "Steel Production": ("production", "steel"),
    "Titanium Production": ("production", "titanium"),
    "Plant Production": ("production", "plants"),
    "Energy Production": ("production", "energy"),
    "Heat Production": ("production", "heat"),
    "Count of Building tags": ("tags", "building"),
    "Count of Space tags": ("tags", "space"),
    "Count of Science tags": ("tags", "science"),
    "Count of Power tags": ("tags", "power"),
    "Count of Earth tags": ("tags", "earth"),
    "Count of Jovian tags": ("tags", "jovian"),
    "Count of Plant tags": ("tags", "plant"),
    "Count of Microbe tags": ("tags", "microbe"),
    "Count of Animal tags": ("tags", "animal"),
    "Count of City tags": ("tags", "city"),
}
GLOBAL_PARAMETERS = ("temperature", "oxygen", "oceans")
TERRAFORM_RATING = "TR"  # From the log's Victory Points by source.

# Decisions that begin something the log has an anchor or a record for; the rest are within an Action.
MAIN_KINDS = {"action", "draft", "buy_cards", "corporation", "prelude_cards", "play_prelude_card", "final_greenery"}
# The most picks a lookahead makes to finish an Action, and a whole Game.
LOOKAHEAD_PICKS = 60
MAX_PICKS = 20_000
# Backtracking: how many Actions back an open Decision may be, and how many retries a Game may take.
RETRY_REACH = 40
MAX_RETRIES = 30


@dataclass(frozen=True)
class Line:
    """One line of a move's description, by the Player it names (None if it names none)."""

    move: int  # The move's index in the Game's moves.
    player: int | None
    text: str  # What follows "Player 1 ".


@dataclass(frozen=True)
class Anchor:
    """A line that begins an Action, or a Prelude Card's play: what the Player chose, and where."""

    line: int  # Index into the Game's lines.
    move: int
    player: int
    kind: str  # play, activate, project, claim, fund, heat, plants, pass, end_turn
    what: str | None
    generation: int


@dataclass(frozen=True)
class Difference:
    """Where the replay stopped: the cause, a group for counting, and what exactly differed."""

    cause: str
    move_number: int | None
    detail: str


class Differs(Exception):
    """The replay and the log disagree. `picks`, if given, is how many of the Replay's picks came before the
    difference; otherwise all of them did."""

    def __init__(self, cause: str, detail: str = "", move: int | None = None, picks: int | None = None) -> None:
        super().__init__(f"{cause}: {detail}")
        self.cause, self.detail, self.move, self.picks = cause, detail, move, picks


@dataclass
class OpenDecision:
    """A Decision the log didn't settle: the Game just before it, the replay's place, and the Options still to
    try there."""

    engine: tm_engine.Game
    cursor: dict[str, Any]
    alternatives: list[int]


@dataclass
class Outcome:
    """A Game's replay: the engine's Replay as far as it matched the log, and its first difference."""

    game: str
    replay: dict[str, Any]
    complete: bool
    difference: Difference | None
    moves: int  # Moves in the log.
    moves_reached: int  # Moves before the one where the replay stopped (all of them if complete).
    generation: int  # The Generation the engine reached.
    unlogged: Counter[str] = field(default_factory=Counter)  # Decisions the log left open, by kind.
    # The picks the log didn't give (passes it left out, ties the trackers settled, cards discarded in
    # hindsight, alternatives retried), by their index in the Replay.
    inferred: list[int] = field(default_factory=list)


def area_at(x: int, y: int) -> str | None:
    """The engine's id of the Area Board Game Arena writes as (x, y)."""
    if (x, y) in OFF_MARS:
        return OFF_MARS[(x, y)]
    if not 1 <= y <= len(ROW_STARTS):
        return None
    return f"{ROW_LETTERS[y - 1]}{x - ROW_STARTS[y - 1] + 1}"


@cache
def card_kinds() -> dict[str, str]:
    return {card["id"]: card["type"] for card in catalog()}


def names_in(text: str) -> list[str]:
    """The card ids a draws, keeps, reveals or drafts line names, in order."""
    found = LISTED.match(text)
    if not found or not found.group(2) or (found.group(1) is None and re.fullmatch(r"\d+ cards?(/s)?", found.group(2))):
        return []
    ids = [card_id(name.strip()) for name in found.group(2).split(", ")]
    return [card for card in ids if card]


def read_lines(moves: list[dict[str, Any]]) -> tuple[list[Line], int]:
    """Every line of the moves, and how many name a Player by a renamed account's old name. Such a name is
    the Player's whose moves it most often begins; the name itself is dropped."""
    votes: dict[str, Counter[int]] = {}
    for move in moves:
        first = (move.get("description") or "").split(" | ")[0].strip()
        old_name = OLD_NAME.match(first) if not SUBJECT.match(first) else None
        if old_name and move.get("player") in (0, 1):
            votes.setdefault(old_name.group(1), Counter())[move["player"]] += 1
    lines = []
    renamed = 0
    for index, move in enumerate(moves):
        for text in (move.get("description") or "").split(" | "):
            text = text.strip()
            subject = SUBJECT.match(text)
            old_name = OLD_NAME.match(text) if not subject else None
            if subject:
                lines.append(Line(index, int(subject.group(1)) - 1, subject.group(2)))
            elif (
                old_name
                and not text.startswith(("You ", "Player "))
                and (old_name.group(1) in votes or move.get("player") in (0, 1))
            ):
                player = votes[old_name.group(1)].most_common(1)[0][0] if old_name.group(1) in votes else move["player"]
                lines.append(Line(index, player, old_name.group(2)))
                renamed += 1
            elif text:
                lines.append(Line(index, None, text))
    return lines, renamed


def anchor_of(line: Line, move: dict[str, Any]) -> tuple[str, str | None] | None:
    """What Action, if any, a line begins: its kind and what it names."""
    text = line.text
    if line.player is None:
        return None
    if text.startswith("plays card "):
        return "play", card_id(text.removeprefix("plays card "))
    if text.startswith("activates "):
        return "activate", card_id(text.removeprefix("activates "))
    if text.startswith("plays standard project "):
        name = re.sub(r"[^a-z]", "", text.removeprefix("plays standard project ").lower())
        return "project", STANDARD_PROJECTS.get(name, name)
    if text.startswith("claims milestone "):
        return "claim", milestone_id(text.removeprefix("claims milestone "))
    funded = re.match(r"^funds (.*) award$", text)
    if funded:
        return "fund", award_id(funded.group(1))
    if text == "passes":
        return "pass", None
    if text == "skips second action":
        return "end_turn", None
    if re.fullmatch(r"pays 8 Heat", text) and (
        move.get("action_type") == "convert_heat"
        or (
            "increases Temperature" in (move.get("description") or "")
            and move.get("action_type") not in ("standard_project", "play_card")  # Not Helion paying with heat.
        )
    ):
        return "heat", None
    if re.fullmatch(r"pays [78] Plant", text) and move.get("action_type") not in ("standard_project", "play_card"):
        return "plants", None
    return None


class RecordedGameReplay:
    """Replays one Recorded Game: `game` as read_games() gives it, `slim` as read_moves() does."""

    def __init__(self, game: dict[str, Any], slim: dict[str, Any]) -> None:
        self.game = game
        self.slim_moves = slim["moves"]
        self.moves = expand_moves(slim)
        self.lines, renamed = read_lines(self.moves)
        self.generations = [move["game_state"].get("generation") or 1 for move in self.moves]
        self.anchors = self.find_anchors()
        self.setup = {d["player"]: d for d in game["decisions"] if d["kind"] == "setup"}
        self.drafts: dict[tuple[int, int], list[dict[str, Any]]] = {}
        self.buys: dict[tuple[int, int], dict[str, Any]] = {}
        for decision in game["decisions"]:
            key = (decision["player"], decision["generation"])
            if decision["kind"] == "draft":
                self.drafts.setdefault(key, []).append(decision)
            elif decision["kind"] == "buy":
                self.buys[key] = decision
        self.engine: tm_engine.Game | None = None
        self.first_player = 0  # Read with the deal, which also sets the next two.
        self.drawn_at: list[int] = []  # The line each Project Card dealt after setup is first named at, in order.
        self.dealt_after_setup: list[str] = []
        self.prelude_card_ids = {card for card, kind in card_kinds().items() if kind == "prelude"}
        # Where the replay has got to in the log.
        self.next_anchor = 0
        self.span_start = 0  # The line the current Action's lines start from.
        self.used: set[int] = set()  # Lines a pick was read from.
        self.sold = 0
        # The move from which trackers have yet to be compared: setup's are the log's starting values.
        self.compared_to = self.anchors[0].move if self.anchors else 0
        self.megacredits_at_start = [0] * PLAYERS  # Each Player's M€ when the Action under way began.
        self.placed: list[tuple[int, str | None]] | None = None  # Every placement the log gives, once read.
        self.research_buys: dict[tuple[int, int], list[str]] = {}  # Read once each.
        self.looking_ahead = False  # Within a lookahead, which settles nothing further by looking ahead.
        self.alternatives: list[int] = []  # Other Options for the Decision being answered, to retry.
        # Trackers that disagreed at their last change: where, how, and after how many picks.
        self.suspects: dict[tuple[str, ...], tuple[int, str, int]] = {}
        self.unlogged: Counter[str] = Counter()
        if renamed:
            self.unlogged["line naming a renamed account"] += renamed
        self.picks = 0  # Picks made so far.
        self.inferred: list[int] = []  # See Outcome.inferred.
        self.guessed = False  # Whether the Decision being answered is settled by something other than the log.

    # The log, read once.

    def find_anchors(self) -> list[Anchor]:
        anchors = []
        passed: set[tuple[int, int]] = set()  # (generation, player)
        first_line_of_move: dict[int, int] = {}
        for index, line in enumerate(self.lines):
            first_line_of_move.setdefault(line.move, index)
            move = self.moves[line.move]
            generation = self.generation_before(line.move)
            found = anchor_of(line, move)
            if found:
                kind, what = found
                anchors.append(Anchor(index, line.move, line.player, kind, what, generation))
                if kind == "pass":
                    passed.add((generation, line.player))
            # A move typed "pass" without a "passes" line, where the Draft's deal follows or the Generation ends,
            # is a pass: its Player's, or the other Player's if they have passed already. Elsewhere the type
            # can be wrong ("Player 1 keeps Strip Mine").
            last_of_move = index + 1 == len(self.lines) or self.lines[index + 1].move != line.move
            ends_generation = (
                "drafts 4 cards: " in (move.get("description") or "") or self.generations[line.move] != generation
            )
            if last_of_move and move.get("action_type") == "pass" and move.get("player") in (0, 1) and ends_generation:
                in_play = [p for p in (move["player"], 1 - move["player"]) if (generation, p) not in passed]
                if in_play and not any(a.kind == "pass" and a.move == line.move for a in anchors):
                    anchors.append(Anchor(index, line.move, in_play[0], "pass", None, generation))
                    passed.add((generation, in_play[0]))
        anchors += self.unlined_anchors(anchors, first_line_of_move)
        return sorted(anchors, key=lambda anchor: anchor.line)

    def unlined_anchors(self, anchors: list[Anchor], first_line_of_move: dict[int, int]) -> list[Anchor]:
        """Plays and activations that some moves give only in their fields: a card played named only in
        "card_played" (Technology Demonstration, Research Network), and a move typed "activate_card" with no
        "activates" line, which names its card at most in a reason ("activation effect of Development
        Center"). A card is played only once, so a play named by a line too is not added again."""
        played = {anchor.what for anchor in anchors if anchor.kind == "play"}
        activated_in = {anchor.move for anchor in anchors if anchor.kind == "activate"}
        # A card's action is used once a Generation at most.
        activated = {(a.generation, a.player, a.what) for a in anchors if a.kind == "activate"}
        found = []
        for index, move in enumerate(self.moves):
            player = move.get("player")
            if player not in (0, 1) or index not in first_line_of_move:
                continue
            at = first_line_of_move[index]
            card = card_id(move.get("card_played") or "")
            if card and card not in played and card_kinds().get(card) in ("automated", "active", "event", "prelude"):
                found.append(Anchor(at, index, player, "play", card, self.generation_before(index)))
                played.add(card)
            elif index not in activated_in | {index - 1}:
                own = [line.text for line in self.lines[at:] if line.move == index and line.player == player]
                named = [ACTIVATION_OF.search(text) for text in own]
                card = next((card_id(match.group(1)) for match in named if match), None)
                generation = self.generation_before(index)
                if card and (generation, player, card) in activated:
                    continue
                if move.get("action_type") == "activate_card" or card:
                    if card is None:
                        reason = ACTIVATION_OF.search(move.get("reason") or "")
                        card = card_id(reason.group(1)) if reason else None
                    activated.add((generation, player, card))
                    found.append(Anchor(at, index, player, "activate", card, generation))
        return found

    def generation_before(self, move: int) -> int:
        return self.generations[move - 1] if move > 0 else 1

    def find_first_player(self) -> int:
        for move in self.moves[:5]:
            found = STARTING_PLAYER.search(move.get("description") or "")
            if found:
                return int(found.group(1)) - 1
        plays = [a for a in self.anchors if a.kind == "play"]
        if plays:
            return plays[0].player
        raise Differs("log names no plays", 'its moves give only "Player 1 other"')

    def deal(self) -> dict[str, Any]:
        """The deal: the first player, and the cards in the order the log shows them dealt and drawn."""
        self.first_player = self.find_first_player()
        order = [self.first_player, 1 - self.first_player]
        if set(order) - set(self.setup):
            raise Differs("setup record missing")
        offers = [self.setup[player]["offer"] for player in order]
        kinds = card_kinds()
        project_cards = [card for offer in offers for card in offer["cards"]]
        prelude_cards = [card for offer in offers for card in offer.get("prelude_cards") or []]
        seen = set(project_cards) | set(prelude_cards)
        self.drawn_at = []
        deals = 0
        dealt_moves = set()
        for line_index in self.lines_in_draw_order():
            line = self.lines[line_index]
            if line.move not in dealt_moves and line.player is not None and line.text.startswith("drafts 4 cards: "):
                drafted = {
                    other.player: names_in(other.text)
                    for other in self.lines
                    if other.move == line.move
                    and other.player is not None
                    and other.text.startswith("drafts 4 cards: ")
                }
                if len(drafted) == PLAYERS and not (set(drafted[0]) | set(drafted[1])) & seen:
                    dealt_moves.add(line.move)
                    deals += 1
                    first = (self.first_player + deals) % PLAYERS
                    # The deal comes once the Generation's last pass is done, which may be logged in the same move.
                    after_move = 1 + max(i for i, other in enumerate(self.lines) if other.move == line.move)
                    for player in (first, 1 - first):
                        project_cards += drafted[player]
                        seen.update(drafted[player])
                        self.drawn_at += [after_move] * len(drafted[player])
                    continue
            for card in names_in(line.text) if line.player is not None else []:
                if card in seen:
                    continue
                seen.add(card)
                if kinds.get(card) == "prelude":
                    prelude_cards.append(card)
                elif kinds.get(card) in ("automated", "active", "event"):
                    project_cards.append(card)
                    self.drawn_at.append(line_index)
        self.dealt_after_setup = project_cards[len(project_cards) - len(self.drawn_at) :]
        return {
            "first_player": self.first_player,
            "corporations": [card for offer in offers for card in offer["corporations"]],
            "prelude_cards": prelude_cards,
            "project_cards": project_cards,
        }

    def lines_in_draw_order(self) -> list[int]:
        """The lines in the order the engine draws the cards they name: the log's order, except that
        Experimental Forest's Greenery draws its placement bonus before the cards are revealed, which the
        log names first."""
        order = list(range(len(self.lines)))
        for number, anchor in enumerate(self.anchors):
            if anchor.kind != "play" or anchor.what != "experimental_forest":
                continue
            end = self.anchors[number + 1].line if number + 1 < len(self.anchors) else len(self.lines)
            span = range(anchor.line, end)
            kept = [
                i for i in span if self.lines[i].player == anchor.player and self.lines[i].text.startswith("keeps ")
            ]
            if not kept:
                continue
            drawn = [
                i
                for i in span
                if i > kept[0] and self.lines[i].player == anchor.player and self.lines[i].text.startswith("draws ")
            ]
            for line in drawn:
                order.remove(line)
                order.insert(order.index(kept[0]), line)
        return order

    # Replaying.

    def run(self) -> Outcome:
        difference, reached, picks = None, len(self.moves), None
        try:
            self.engine = tm_engine.Game(seed=1, prelude=self.game["prelude"], deal=self.deal())
            self.play()
        except Differs as differs:
            move = differs.move if differs.move is not None else self.current_move()
            number = self.moves[move].get("move_number") if move < len(self.moves) else None
            difference = Difference(differs.cause, number, differs.detail)
            reached, picks = min(move, self.current_move()), differs.picks
        except ValueError as error:  # The engine refused the deal or a pick.
            difference, reached = Difference("engine refused", None, str(error)), self.current_move()
        engine = self.engine
        replay = engine.replay if engine is not None else {}
        if picks is not None:  # Up to the first disagreement, not the one that confirmed it.
            replay["picks"] = replay["picks"][:picks]
        kept = len(replay.get("picks", []))
        return Outcome(
            game=self.game["game"],
            replay=replay,
            complete=difference is None,
            difference=difference,
            moves=len(self.moves),
            moves_reached=reached,
            generation=engine.full_view()["generation"] if engine is not None else 0,
            unlogged=self.unlogged,
            inferred=[pick for pick in self.inferred if pick < kept],
        )

    def play(self) -> None:
        """Answers the engine's Decisions until the Game or its log ends. A Decision the log didn't settle (a
        tie between Options, a look's buy left unlogged) stays open: at a difference, the replay goes back to
        the latest open one within reach and tries its next alternative. If none helps, the attempt that
        got furthest stands, with its first difference."""
        points: list[OpenDecision] = []
        furthest: tuple[int, Differs, tm_engine.Game, dict[str, Any]] | None = None
        retries = 0
        for _ in range(MAX_PICKS * 2):
            try:
                if self.answer_next_decision(points):
                    return
            except Differs as differs:
                if furthest is None or self.next_anchor > furthest[0]:
                    furthest = (self.next_anchor, differs, self.engine.copy(), self.snapshot())
                point = self.retry(points)
                if point is None or retries >= MAX_RETRIES:
                    _, first, self.engine, cursor = furthest
                    self.restore(cursor)
                    raise first from None
                retries += 1
        raise Differs("too many picks")

    def answer_next_decision(self, points: list[OpenDecision]) -> bool:
        """Answers one Decision; True once the Game or its log has ended."""
        engine = self.engine
        if engine.is_over:
            self.check_scores(engine)
            return True
        decision = engine.decision
        self.pass_over_automatic_plays(engine)
        if self.log_ended(decision):
            return True
        self.alternatives, self.guessed = [], False
        before = engine.copy()
        index = self.choose(engine, decision, lookahead=True)
        if self.guessed:
            self.inferred.append(self.picks)
        if self.alternatives:  # The replay's place as this Decision left it, which its alternatives share.
            points.append(OpenDecision(before, self.snapshot(), [a for a in self.alternatives if a != index]))
        engine.pick(index)
        self.picks += 1
        return False

    def retry(self, points: list[OpenDecision]) -> OpenDecision | None:
        """Goes back to the latest open Decision within reach that has an alternative left, and takes it."""
        while points:
            point = points[-1]
            if not point.alternatives or self.next_anchor - point.cursor["next_anchor"] > RETRY_REACH:
                points.pop()
                continue
            self.engine = point.engine.copy()
            self.restore(point.cursor)
            self.unlogged["Decision retried"] += 1
            self.inferred.append(self.picks)
            self.engine.pick(point.alternatives.pop(0))
            self.picks += 1
            return point
        return None

    def snapshot(self) -> dict[str, Any]:
        """Where the replay is in the log, to come back to."""
        return {
            "next_anchor": self.next_anchor,
            "span_start": self.span_start,
            "used": set(self.used),
            "sold": self.sold,
            "compared_to": self.compared_to,
            "suspects": dict(self.suspects),
            "megacredits_at_start": list(self.megacredits_at_start),
            "unlogged": Counter(self.unlogged),
            "picks": self.picks,
            "inferred": list(self.inferred),
        }

    def restore(self, cursor: dict[str, Any]) -> None:
        self.next_anchor, self.span_start, self.sold = cursor["next_anchor"], cursor["span_start"], cursor["sold"]
        self.used, self.compared_to = set(cursor["used"]), cursor["compared_to"]
        self.suspects, self.megacredits_at_start = dict(cursor["suspects"]), list(cursor["megacredits_at_start"])
        self.unlogged = Counter(cursor["unlogged"])
        self.picks, self.inferred = cursor["picks"], list(cursor["inferred"])

    def current_move(self) -> int:
        if self.next_anchor < len(self.anchors):
            return self.anchors[self.next_anchor].move
        return len(self.moves)

    def log_ended(self, decision: dict[str, Any]) -> bool:
        """Whether every Action in the log has been replayed, as far as the engine can follow: a conceded
        Game ends with its log; any other must go on to its end."""
        if self.next_anchor < len(self.anchors) or decision["kind"] not in ("action", "draft", "buy_cards"):
            return False
        if self.game["conceded"]:
            return True
        if decision["kind"] == "action" and offered(decision, type="pass") is not None:
            return False  # The last passes, which the log may leave out.
        raise Differs("log ends before the Game does", decision["kind"])

    def choose(self, engine: tm_engine.Game, decision: dict[str, Any], *, lookahead: bool) -> int:
        kind = decision["kind"]
        self.pass_over_automatic_plays(engine)
        handler = getattr(self, f"choose_{kind}", None)
        chosen = handler(engine, decision) if handler else None
        if chosen is not None:
            return chosen
        if len(decision["options"]) == 1:
            return 0
        if not lookahead:
            return 0
        return self.best_by_trackers(engine, decision)

    # Main Decisions.

    def pass_over_automatic_plays(self, engine: tm_engine.Game) -> None:
        """The engine plays a Player's last Prelude Card without a Decision: its play line begins its Action."""
        while self.next_anchor < len(self.anchors):
            anchor = self.anchors[self.next_anchor]
            if anchor.kind != "play" or anchor.what not in self.prelude_card_ids:
                return
            if anchor.what not in engine.full_view()["players"][anchor.player]["played_prelude_cards"]:
                return
            self.begin_action(engine, anchor, compare=False)

    def take_anchor(self, decision: dict[str, Any], kinds: tuple[str, ...]) -> Anchor:
        if self.next_anchor >= len(self.anchors):
            raise Differs("log has no more Actions", decision["kind"])
        anchor = self.anchors[self.next_anchor]
        if anchor.player != decision["player"] or anchor.kind not in kinds:
            raise Differs(
                "log's next Action differs",
                f"engine asks Player {decision['player'] + 1} for {decision['kind']}; the log has Player "
                f"{anchor.player + 1} {anchor.kind} {anchor.what or ''}".rstrip(),
                anchor.move,
            )
        return anchor

    def begin_action(self, engine: tm_engine.Game, anchor: Anchor, *, compare: bool = True) -> None:
        """The engine is about to take `anchor`'s Action: the previous Action is over, so the trackers that
        changed since the last comparison are compared, and this Action's lines become the ones choices are
        read from. An Action the engine has already carried out without a Decision is compared with the next."""
        if compare:
            self.compare(engine, self.compared_to, anchor.move)
            self.compared_to = anchor.move
            self.check_deck(engine, anchor)
        self.next_anchor += 1
        self.span_start = anchor.line
        self.sold = 0
        self.megacredits_at_start = [player["resources"]["megacredits"] for player in engine.full_view()["players"]]

    def choose_action(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        first_action = offered(decision, type="first_action")
        if first_action is not None:
            return first_action
        if self.next_anchor >= len(self.anchors) and not self.game["conceded"]:
            self.unlogged["pass"] += 1  # The log of a Game played to its end left out the last passes.
            self.guessed = True
            return offered(decision, type="pass")
        if self.next_anchor >= len(self.anchors):
            raise Differs("log has no more Actions", "action")
        anchor = self.anchors[self.next_anchor]
        while anchor.kind == "end_turn" and offered(decision, type="end_turn") is None:
            # Once the other Player has passed, ending a Turn changes nothing, so the engine doesn't offer it.
            self.begin_action(engine, anchor)
            if self.next_anchor >= len(self.anchors):
                raise Differs("log has no more Actions", "action")
            anchor = self.anchors[self.next_anchor]
        if anchor.player != decision["player"] or anchor.generation > engine.full_view()["generation"]:
            # The log moved on without this Player ending their Turn or passing.
            for unlogged in ("end_turn", "pass"):
                index = offered(decision, type=unlogged)
                if index is not None:
                    self.unlogged[unlogged] += 1
                    self.guessed = True
                    return index
        anchor = self.take_anchor(
            decision, ("play", "activate", "project", "claim", "fund", "heat", "plants", "pass", "end_turn")
        )
        wanted = {
            "play": {"type": "play_card", "card": anchor.what},
            "activate": {"type": "use_action", "card": anchor.what},
            "project": {"type": "standard_project", "project": anchor.what},
            "claim": {"type": "claim_milestone", "milestone": anchor.what},
            "fund": {"type": "fund_award", "award": anchor.what},
            "heat": {"type": "convert_heat"},
            "plants": {"type": "convert_plants"},
            "pass": {"type": "pass"},
            "end_turn": {"type": "end_turn"},
        }[anchor.kind]
        if anchor.kind == "activate" and anchor.what is None:
            del wanted["card"]  # Which card's action the log doesn't say: the trackers tell.
            actions = [option["index"] for option in decision["options"] if option["details"]["type"] == "use_action"]
            if not actions:
                raise self.not_offered(engine, anchor)
            self.begin_action(engine, anchor)
            self.unlogged["card action"] += 1
            return actions[0] if len(actions) == 1 else self.best_by_trackers(engine, decision, among=actions)
        index = offered(decision, **wanted)
        if index is None:
            raise self.not_offered(engine, anchor)
        self.begin_action(engine, anchor)
        return index

    def not_offered(self, engine: tm_engine.Game, anchor: Anchor) -> Differs:
        """Why the engine doesn't offer an anchor's Action, as far as the hand tells."""
        if anchor.kind == "play":
            board = engine.full_view()["players"][anchor.player]
            if anchor.what not in board["hand"]:
                return Differs("card not in hand", anchor.what or "", anchor.move)
            cost = board["card_costs"].get(anchor.what)
            return Differs("card in hand not playable", f"{anchor.what}, costing {cost}", anchor.move)
        return Differs(f"not offered: {anchor.kind}", anchor.what or "", anchor.move)

    def choose_play_prelude_card(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        anchor = self.take_anchor(decision, ("play",))
        index = offered(decision, type="play_prelude_card", card=anchor.what)
        if index is None:
            raise Differs("not offered: Prelude Card", anchor.what or "", anchor.move)
        self.begin_action(engine, anchor)
        return index

    def choose_play_card(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        anchor = self.take_anchor(decision, ("play",))
        index = offered(decision, type="play_card", card=anchor.what)
        if index is None:
            raise Differs("not offered: play", anchor.what or "", anchor.move)
        self.next_anchor += 1  # Part of the Prelude Card's Action.
        return index

    def choose_final_greenery(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        if self.next_anchor < len(self.anchors):
            anchor = self.anchors[self.next_anchor]
            if anchor.kind == "plants" and anchor.player == decision["player"]:
                index = offered(decision, type="convert_plants")
                if index is not None:
                    self.begin_action(engine, anchor)
                    return index
        return offered(decision, type="done")

    def choose_free_award(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        anchor = self.take_anchor(decision, ("fund",))
        self.next_anchor += 1
        return offered(decision, type="fund_award", award=anchor.what)

    def choose_corporation(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        picked = self.setup[decision["player"]]["picked"]["corporation"]
        return self.record_pick(decision, picked, type="choose_corporation", card=picked)

    def choose_prelude_cards(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        for card in self.setup[decision["player"]]["picked"]["prelude_cards"]:
            index = offered(decision, type="keep_prelude_card", card=card)
            if index is not None:
                return index
        raise Differs("record differs: Prelude Cards kept", str(self.setup[decision["player"]]["picked"]))

    def choose_buy_cards(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        player = decision["player"]
        generation = engine.full_view()["generation"]
        if generation == 1:
            cards = self.setup[player]["picked"]["cards"]
        else:
            cards = self.kept_in_research(player, generation)
        bought = engine.full_view()["players"][player]["buying"]["bought"]
        for card in cards:
            if card not in bought:
                return self.record_pick(decision, card, type="buy_card", card=card)
        return offered(decision, type="done")

    def choose_draft(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        player = decision["player"]
        generation = engine.full_view()["generation"]
        records = self.drafts.get((player, generation), [])
        kept = engine.full_view()["players"][player]["drafting"]["kept"]
        if len(kept) >= len(records):
            raise Differs("record missing: Draft", f"Generation {generation}, pick {len(kept) + 1}")
        picked = records[len(kept)]["picked"]
        return self.record_pick(decision, picked, type="draft_card", card=picked)

    def kept_in_research(self, player: int, generation: int) -> list[str]:
        """The cards a Player buys in a Research phase, read from its keep lines as ticket 09's hand rebuild
        reads them: a keep taken back by "drafts X", or started again after "cancels their move", counts as
        such, which the dataset's buy records (ticket 08) don't always do. With no keep line, the record says
        (a buy of nothing has no line)."""
        if (player, generation) not in self.research_buys:
            self.research_buys[(player, generation)] = self.read_research_buy(player, generation)
        return self.research_buys[(player, generation)]

    def read_research_buy(self, player: int, generation: int) -> list[str]:
        first_action = next((a.line for a in self.anchors if a.generation == generation), len(self.lines))
        keep = Keep()
        for index in range(first_action):
            line = self.lines[index]
            if line.player != player or self.generations[line.move] != generation:
                continue
            if line.text == "cancels their move":
                keep.starting_over = True
            elif line.text.startswith("drafts ") and keep.names:
                keep.take_back(line.text.removeprefix("drafts "))
            elif line.text.startswith("keeps "):
                names = [name.strip() for name in LISTED.match(line.text).group(2).split(", ")]
                keep.keep(names, whole=len(names) > 1)
        record = self.buys.get((player, generation), {}).get("picked")
        if keep.names is None:
            if record is None:
                self.unlogged["buy of nothing"] += 1
            return record or []
        cards = [card for card in (card_id(name) for name in keep.names) if card]
        if record is not None and sorted(record) != sorted(cards):
            self.unlogged["buy differing from its record"] += 1
        return cards

    def record_pick(self, decision: dict[str, Any], wanted: str, **details: Any) -> int:
        index = offered(decision, **details)
        if index is None:
            raise Differs(f"record differs: {decision['kind']}", wanted)
        return index

    # Choices within an Action, read from its lines.

    def span(self) -> range:
        """The lines of the Action under way: from its anchor to the next. A move's lines before its anchor,
        such as payments, belong to that anchor's Action."""
        end = self.anchors[self.next_anchor].line if self.next_anchor < len(self.anchors) else len(self.lines)
        start = self.span_start
        while start > 0 and self.leads_into(start - 1, start):
            start -= 1
        while end > start and end < len(self.lines) and self.leads_into(end - 1, end):
            end -= 1
        return range(start, end)

    def leads_into(self, line: int, anchor_line: int) -> bool:
        """Whether a line just before an anchor in its move is part of the anchor's Action: a payment by the
        same Player ("Player 1 pays 3 Steel | Player 1 plays card Mine")."""
        before, anchor = self.lines[line], self.lines[anchor_line]
        return (
            before.move == anchor.move
            and before.player == anchor.player
            and before.text.startswith(("pays ", "removes "))
        )

    def find_line(self, player: int | None, pattern: re.Pattern[str]) -> tuple[int, re.Match[str]] | None:
        for index in self.span():
            line = self.lines[index]
            if index in self.used or (player is not None and line.player != player):
                continue
            found = pattern.match(line.text)
            if found:
                return index, found
        return None

    def placements(self) -> list[tuple[int, str | None]]:
        """The Areas Tiles were placed on in the Action under way, in order, by the line or move they come from.
        A placement in a move's tile fields and its description is one placement."""
        found: list[tuple[int, str | None]] = []
        moves_with_line = set()
        for index in self.span():
            line = self.lines[index]
            placed = PLACED.match(line.text) if line.player is not None else None
            if placed and (placed.group(3) or placed.group(2) in NAMED_AREAS):
                at = (int(placed.group(3)), int(placed.group(4))) if placed.group(3) else None
                found.append((index, area_at(*at) if at else NAMED_AREAS[placed.group(2)]))
                moves_with_line.add(line.move)
        for move_index in sorted({self.lines[index].move for index in self.span()} - moves_with_line):
            location = LOCATION.search(self.moves[move_index].get("tile_location") or "")
            if location:
                first_line = min(index for index in self.span() if self.lines[index].move == move_index)
                found.append((first_line, area_at(int(location.group(1)), int(location.group(2)))))
        return sorted(found, key=lambda placement: placement[0])

    def choose_area(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        for line, area in self.placements():
            if line in self.used:
                continue
            self.used.add(line)
            index = offered(decision, area=area)
            if index is None:
                raise Differs("Area not offered", f"{area}", self.lines[line].move)
            return index
        # Chosen by the trackers, from placement bonuses, among the Areas the log places no Tile on later.
        self.unlogged["area"] += 1
        later = {area for line, area in self.all_placements() if line >= self.span().stop}
        free = [option["index"] for option in decision["options"] if option["details"].get("area") not in later]
        return self.best_by_trackers(engine, decision, among=free or None)

    def all_placements(self) -> list[tuple[int, str | None]]:
        if self.placed is None:
            saved = (self.span_start, self.next_anchor)
            self.span_start, self.next_anchor = 0, len(self.anchors)
            self.placed = self.placements()
            self.span_start, self.next_anchor = saved
        return self.placed

    def choose_payment(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        """The payment the Action's lines give: "pays 3 Steel", "pays 4 M€", and microbes taken off
        Psychrophiles."""
        paid = Counter()
        player = decision["player"]
        for index in self.span():
            line = self.lines[index]
            if line.player != player or index in self.used:
                continue
            found = PAID.fullmatch(line.text)
            if found:
                paid[RESOURCE_KEYS[found.group(2)]] += int(found.group(1))
            elif line.text == "removes Microbe from Psychrophiles":
                paid["microbes"] += 1
        for option in decision["options"]:
            details = option["details"]
            same = all(details.get(key, 0) == paid[key] for key in ("steel", "titanium", "heat", "microbes"))
            if same and paid["megacredits"] in (0, details.get("megacredits")):
                return option["index"]
        return None

    def choose_sell_patents(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        found = self.find_line(decision["player"], SOLD)
        selling = int(found[1].group(1)) if found else 0
        if self.sold >= selling:
            if found:
                self.used.add(found[0])
            return offered(decision, type="done")
        self.sold += 1
        return self.discard_in_hindsight(decision, "sell_card")

    def choose_discard_to_draw(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        """Mars University: discard if the log says so. Some logs drop the discard line and keep only the
        one-card draw (ticket 09); then whether the engine's draws match the log's decides."""
        player = decision["player"]
        found = self.find_line(player, MARS_UNIVERSITY_DISCARD)
        if found is not None:
            self.used.add(found[0])
            return self.discard_in_hindsight(decision, "discard_card")
        done = offered(decision, type="done")
        if self.find_line(player, ONE_CARD_DRAWN) is None:
            return done
        return self.best_by_trackers(
            engine, decision, among=[done, self.discard_in_hindsight(decision, "discard_card")]
        )

    def discard_in_hindsight(self, decision: dict[str, Any], kind: str) -> int:
        """A card the log doesn't name leaves the hand: one its Player never plays later. Any such card
        replays the same."""
        later = {
            a.what for a in self.anchors[self.next_anchor :] if a.kind == "play" and a.player == decision["player"]
        }
        for option in decision["options"]:
            if option["details"]["type"] == kind and option["details"]["card"] not in later:
                self.guessed = True
                return option["index"]
        raise Differs("no card to discard in hindsight", kind)

    def choose_keep_cards(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int:
        kept = self.find_line(decision["player"], re.compile(r"^(?:keeps|keep|buy) (.*?)(?: \(.*\))?$"))
        if kept:
            for card in names_in(self.lines[kept[0]].text):
                index = offered(decision, card=card)
                if index is not None and decision["options"][index]["details"]["type"] != "done":
                    names = names_in(self.lines[kept[0]].text)
                    if card == names[-1]:
                        self.used.add(kept[0])
                    return index
        done = offered(decision, type="done")
        if not self.looking_ahead:  # A look's buy some logs leave out: keeping a card is the alternative.
            self.alternatives = [option["index"] for option in decision["options"] if option["index"] != done]
        return done

    def choose_olympus_conference(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        """Olympus Conference, and Mars University's discard that may come first: as the lines say, and
        without lines, whether the engine's draws match the log's."""
        player = decision["player"]
        if self.find_line(player, MARS_UNIVERSITY_DISCARD):
            return self.choose_discard_to_draw(engine, decision)
        removed = self.find_line(player, re.compile(r"^removes Science from Olympus Conference"))
        added = self.find_line(player, re.compile(r"^adds Science to Olympus Conference"))
        for found, draw in ((removed, True), (added, False)):
            if found and (removed is None or added is None or found[0] <= min(removed[0], added[0])):
                index = offered(decision, type="olympus_conference", draw=draw)
                if index is not None:
                    self.used.add(found[0])
                    return index
        if any(option["details"]["type"] == "discard_card" for option in decision["options"]):
            others = [option["index"] for option in decision["options"] if option["details"]["type"] != "discard_card"]
            return self.best_by_trackers(
                engine, decision, among=[*others, self.discard_in_hindsight(decision, "discard_card")]
            )
        return offered(decision, type="done")

    def choose_add_to_card(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        added = self.find_line(decision["player"], re.compile(r"^adds (?:\d+ )?\w+ to (.+?)(?: \(.*\))?$"))
        if added:
            index = offered(decision, to=card_id(added[1].group(1)))
            if index is not None:
                self.used.add(added[0])
                return index
        return None

    def choose_viral_enhancers(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        """Viral Enhancers: a Card Resource on the card played, or a plant, as its own lines say. Other lines
        adding to the card are often the card's own effect (Decomposers), so only those giving Viral
        Enhancers as their reason count."""
        player = decision["player"]
        plant = self.find_line(player, re.compile(r"^gains 1 Plant \(triggered effect of Viral Enhancers\)"))
        added = self.find_line(player, re.compile(r"^adds \w+ to (.+?) \(triggered effect of Viral Enhancers\)$"))
        if added and (plant is None or added[0] < plant[0]):
            index = offered(decision, type="viral_enhancers", add=True, card=card_id(added[1].group(1)))
            if index is not None:
                self.used.add(added[0])
                return index
        if plant:
            self.used.add(plant[0])
            return offered(decision, type="viral_enhancers", add=False)
        return None

    def choose_effects(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        """Alternative effects ("Gain 3 plants", "Add 3 microbes to another card"): the first line of the
        Action that does what just one alternative's label says, by its verb and what it changes ("gains 3
        Plant", "adds Animal to Birds")."""
        for index in self.span():
            line = self.lines[index]
            effect = EFFECT_LINE.match(line.text)
            if index in self.used or line.player != decision["player"] or effect is None:
                continue
            verb, thing = EFFECT_VERBS[effect.group(1)], effect.group(2).lower()
            matching = [
                option["index"]
                for option in decision["options"]
                if option["label"].startswith(verb) and thing in option["label"].lower()
            ]
            if len(matching) == 1:
                self.used.add(index)
                return matching[0]
        return None

    def choose_resources(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        """An action's Resource change ("Spend 1 plant to gain 7 MegaCredits"): the one spending what a line
        shows its Player paying."""
        for index in self.span():
            line = self.lines[index]
            paid = re.match(r"^pays (\d+) (Plant|Steel|Titanium|M€|Heat|Energy)", line.text)
            if index in self.used or paid is None or line.player != decision["player"]:
                continue
            resource, amount = RESOURCE_KEYS[paid.group(2)], -int(paid.group(1))
            for option in decision["options"]:
                if (option["details"].get("resources") or {}).get(resource) == amount:
                    self.used.add(index)
                    return option["index"]
        return None

    def choose_target(self, engine: tm_engine.Game, decision: dict[str, Any]) -> int | None:
        """Whom a card takes Resources or Production from: the Player a line shows losing them ("Player 2 pays
        5 Plant (immediate effect of Asteroid)", "Player 1 reduces Plant Production by 2"), and with no such
        line, nobody if that is an Option."""
        for index in self.span():
            line = self.lines[index]
            if index in self.used or line.player is None:
                continue
            target = self.target_in(line, decision)
            if target is not None:
                self.used.add(index)
                return target
        if all(option["details"]["type"] in ("remove_resources", "remove_nothing") for option in decision["options"]):
            return offered(decision, type="remove_nothing")
        return None

    @staticmethod
    def target_in(line: Line, decision: dict[str, Any]) -> int | None:
        """The Option taking from the Player what `line` shows them losing, if any."""
        lost, lowered = LOST.match(line.text), LOWERED.match(line.text)
        if lost and (line.player != decision["player"] or lost.group(2)):  # Not paying for something of their own.
            resource, change, kind, key = RESOURCE_KEYS[lost.group(1)], None, "remove_resources", "resources"
        elif lowered:
            resource, change = RESOURCE_KEYS[lowered.group(1)], -int(lowered.group(2))
            kind, key = "lower_production", "production"
        else:
            return None
        for option in decision["options"]:
            details = option["details"]
            if details["type"] != kind or details.get("player") != line.player:
                continue
            amount = (details.get(key) or {}).get(resource, 0)
            if amount < 0 and change in (None, amount):
                return option["index"]
        return None

    # Choices the lines don't settle: the Option that leaves the trackers as the log does.

    def best_by_trackers(self, engine: tm_engine.Game, decision: dict[str, Any], among: list[int] | None = None) -> int:
        """The Option, among `among` if given, that leaves the trackers and the deck as the log does, by
        finishing the Action with each. Ties become a choice point's alternatives."""
        if self.looking_ahead:
            return among[0] if among else decision["options"][0]["index"]
        expected = self.expected(self.span_moves())
        paid = self.megacredits_changed(decision["player"])
        scored = []
        for option in decision["options"]:
            if among is not None and option["index"] not in among:
                continue
            trial = engine.copy()
            saved = (set(self.used), self.next_anchor, self.span_start, self.sold)
            self.looking_ahead = True
            try:
                trial.pick(option["index"])
                for _ in range(LOOKAHEAD_PICKS):
                    if trial.is_over or trial.decision["kind"] in MAIN_KINDS:
                        break
                    trial.pick(self.choose(trial, trial.decision, lookahead=False))
                end_line = (
                    self.anchors[self.next_anchor].line if self.next_anchor < len(self.anchors) else len(self.lines)
                )
                drawn, named = self.cards_drawn(trial, end_line)
                megacredits = trial.full_view()["players"][decision["player"]]["resources"]["megacredits"]
                spent = megacredits - self.megacredits_at_start[decision["player"]] != paid
                scored.append((len(self.mismatches(trial, expected)) + abs(drawn - named), spent, option["index"]))
            except (Differs, ValueError):
                scored.append((1_000, True, option["index"]))
            finally:
                self.used, self.next_anchor, self.span_start, self.sold = saved
                self.looking_ahead = False
        best = min(scored)
        tied = [index for score, spent, index in scored if (score, spent) == best[:2]]
        if len(tied) > 1:
            self.unlogged[f"tie: {decision['kind']}"] += 1
            self.alternatives = tied
        self.guessed = True
        return best[2]

    def megacredits_changed(self, player: int) -> int:
        """How the Action's lines change a Player's M€: "gains 3 M€", "pays 2 M€". Lines that leave the
        resource out ("gains 3") are not counted, so this only breaks ties between Options."""
        change = 0
        for index in self.span():
            line = self.lines[index]
            found = re.match(r"^(gains|pays) (\d+) M€", line.text) if line.player == player else None
            if found:
                change += int(found.group(2)) * (1 if found.group(1) == "gains" else -1)
        return change

    def span_moves(self) -> range:
        start = self.lines[self.span_start].move if self.span_start < len(self.lines) else len(self.moves)
        end = self.anchors[self.next_anchor].move if self.next_anchor < len(self.anchors) else len(self.moves)
        return range(start, max(start + 1, end))

    def expected(self, moves: range) -> dict[tuple[str, ...], int]:
        """The trackers that changed in `moves`, with their last values, as long as no Production phase
        came between (the engine can then only be compared after it)."""
        expected: dict[tuple[str, ...], int] = {}
        researched = any(self.generations[move] != self.generation_before(move) for move in moves if move > 0)
        for move in moves:
            if move >= len(self.moves):
                continue
            changed = self.slim_moves[move].get("game_state") or {}
            state = self.moves[move]["game_state"]
            for player, trackers in (changed.get("player_trackers") or {}).items():
                if player not in ("0", "1") or not isinstance(trackers, dict):
                    continue
                for name in trackers:
                    if name in TRACKERS and not (researched and TRACKERS[name][0] == "resources"):
                        expected[(player, name)] = state["player_trackers"][player][name]
            for player, points in (changed.get("player_vp") or {}).items():
                if player in ("0", "1") and "tr" in ((points or {}).get("total_details") or {}):
                    expected[(player, TERRAFORM_RATING)] = state["player_vp"][player]["total_details"]["tr"]
            for name in GLOBAL_PARAMETERS:
                if name in changed:
                    expected[(name,)] = state[name]
        return expected

    def mismatches(self, engine: tm_engine.Game, expected: dict[tuple[str, ...], int]) -> list[str]:
        view = engine.full_view()
        found = []
        for key, value in expected.items():
            if len(key) == 1:
                actual = view[key[0]]
            elif key[1] == TERRAFORM_RATING:
                actual = view["players"][int(key[0])]["terraform_rating"]
            else:
                group, name = TRACKERS[key[1]]
                actual = view["players"][int(key[0])][group][name]
            if actual != value:
                found.append(f"{' '.join(key)}: engine {actual}, log {value}")
        return found

    def compare(self, engine: tm_engine.Game, start: int, end: int) -> None:
        """The trackers that changed in moves `start` to `end` (not included), against the engine's.

        A tracker can lag: it may show the value at its change, before later gains the log left unrecorded
        (Media Group's M€ after an Event's payment). A real difference lasts, so a tracker differs only when
        it disagrees at two of its changes in a row; the difference is placed at the first."""
        expected = self.expected(range(start, end))
        for key in expected:
            found = self.mismatches(engine, {key: expected[key]})
            if not found:
                self.suspects.pop(key, None)
            elif key in self.suspects:
                move, first, picks = self.suspects[key]
                cause = f"trackers differ: {' '.join(key[1:]) or key[0]}"
                raise Differs(cause, f"{first}; then {found[0]}", move, picks)
            else:
                self.suspects[key] = (max(start, end - 1), found[0], self.picks)

    def check_deck(self, engine: tm_engine.Game, anchor: Anchor) -> None:
        """The engine must have drawn as many of the cards dealt after setup as the log names before `anchor`."""
        drawn, named = self.cards_drawn(engine, anchor.line)
        if drawn != named:
            raise Differs("deck out of step", f"engine drew {drawn} cards, the log names {named}", anchor.move)

    def cards_drawn(self, engine: tm_engine.Game, before_line: int) -> tuple[int, int]:
        """How many of the cards dealt after setup the engine has drawn, and how many the log names before a line."""
        deck = set(engine.full_view()["deck"])
        drawn = sum(1 for card in self.dealt_after_setup if card not in deck)
        return drawn, sum(1 for line in self.drawn_at if line < before_line)

    def check_scores(self, engine: tm_engine.Game) -> None:
        """A Game not conceded ends with the log's scores: its "scores 116 TOTAL VP" lines, or without them the
        dataset's, which come from the last game state and can miss the final Greenery conversion."""
        if self.game["conceded"]:
            return
        scores = [score["total"] for score in engine.scores]
        logged = [player["victory_points"] for player in self.game["players"]]
        for line in self.lines:
            total = re.fullmatch(r"scores (\d+) TOTAL VP", line.text) if line.player is not None else None
            if total:
                logged[line.player] = int(total.group(1))
        if scores != logged:
            raise Differs("final scores differ", f"engine {scores}, log {logged}", len(self.moves) - 1)


def offered(decision: dict[str, Any], **details: Any) -> int | None:
    """The index of the first Option whose details include `details`, if any."""
    for option in decision["options"]:
        if all(option["details"].get(key) == value for key, value in details.items()):
            return option["index"]
    return None


def replay_game(game: dict[str, Any], slim: dict[str, Any]) -> Outcome:
    """Replays a Recorded Game through the engine, as far as it matches the log."""
    return RecordedGameReplay(game, slim).run()


# Decisions of setup and the Research phases, which the dataset's Decision records already hold (ticket 08).
RECORDED_KINDS = {"corporation", "prelude_cards", "buy_cards", "draft"}


def action_decisions(record: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """The Decisions of a replayed Game (a line of replays.jsonl.gz) other than setup's and the Research
    phases': the Prelude Cards played and every Decision of the Action phases, up to the Game's first
    difference. Each is rebuilt through the engine as its Player saw it: "player", "generation", "kind",
    "view" (their Player View), "options" and "picked" (an index into them). Never the other Player's hand
    or the deck: only the Player View and the Decision leave the engine. "inferred" marks a pick the log
    didn't give (see Outcome.inferred), which training may leave out."""
    return replayed_decisions(record, recorded=False)


def recorded_kind_decisions(record: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """The setup and Research-phase Decisions of a replayed Game, up to its first difference, in the shape of
    action_decisions(): the Decisions the dataset's records describe, but with the full Player View (the hand,
    the Tiles and Card Resources), as the Player saw it in play (ticket 13 of phase 2)."""
    return replayed_decisions(record, recorded=True)


def replayed_decisions(record: dict[str, Any], *, recorded: bool) -> Iterator[dict[str, Any]]:
    """The Decisions of a replayed Game whose kind is among RECORDED_KINDS, or those whose kind isn't."""
    if not record["replay"]:  # The Game stopped before the engine could start it.
        return
    game = tm_engine.Game.from_replay({"start": record["replay"]["start"], "picks": []})
    inferred = set(record.get("inferred", []))
    for number, picked in enumerate(record["replay"]["picks"]):
        decision = game.decision
        if (decision["kind"] in RECORDED_KINDS) == recorded:
            view = game.player_view(decision["player"])
            yield {
                "player": decision["player"],
                "generation": view["generation"],
                "kind": decision["kind"],
                "view": view,
                "options": decision["options"],
                "picked": picked,
                "inferred": number in inferred,
            }
        game.pick(picked)

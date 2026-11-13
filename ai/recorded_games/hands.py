"""Each Player's hand, rebuilt move by move from a Recorded Game's slim moves (ai.recorded_games.moves).

The logs name most cards that enter and leave a hand, in wording that differs by scraper version. Some
removals are never named (Sell Patents, Mars University), so a hand is the cards named in it, plus
cards it holds whose names the log doesn't give, minus cards that left it without a name.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from functools import cache
from typing import Any, Literal

from ai.recorded_games.names import card_id, catalog

PLAYERS = 2

# Project Cards dealt to each Player at setup.
DEALT = 10

# "Player 1 keeps …" or "You buy …": who, and the rest of the line.
SUBJECT = re.compile(r"^(?:private: )?(Player [12]|You) (.*)$")

# Moves of the Action phase: the first ends setup or a Research phase.
ACTION_TYPES = {
    "play_card",
    "activate_card",
    "standard_project",
    "convert_heat",
    "claim_milestone",
    "fund_award",
    "place_tile",
}

# Lines that only come once the Action phase has begun. "skips" is not one: setup logs it too.
ENDS_BUYING = re.compile(
    r"^(plays card|plays standard project|passes|activates|funds |claims |first action|places |pays 8 (Heat|Plant)"
    r"|has a mandatory|cannot play card)"
)

# Lines that begin a Player's Action.
ACTION_STARTS = re.compile(r"^(plays card|activates|plays standard project|passes|claims|funds)")

# A line about a card moving in or out of a hand, whoever it names.
UNREAD_CARD_LINE = re.compile(r"^(?!Player [12] |You |private: )\S.* (plays card|draws|keeps|discards|buy|reveals) ")

COUNT = re.compile(r"^(\d+) cards?(?:/s)?(?:: (.*))?$")

# Cards that show cards from the deck to keep some, and how many they show. Newer logs mark the shown
# cards as card_options; old ones log them as a draw of that many.
LOOKS_ON_ACTIVATION = {"Inventors' Guild": 1, "Business Network": 1}
LOOKS_ON_PLAY = {"Invention Contest": 3, "Business Contacts": 4}

# Old logs give the cards Acquired Space Agency and Experimental Forest take into hand only as reveals.
# Search for Life's Microbe card is not taken.
REVEALED_TO_HAND = re.compile(r"^reveals (.*): it has an? (?:Space|Plant) tag$")

# Mars University's trigger, also the reason of the move in which its Player chooses ("Player 1 other").
# Some logs then drop the discard line ("discards 1 card/s") and log only the draw. Without that reason, a
# draw is Mars University's only if nothing else triggered could draw: Olympus Conference, Point Luna, or
# the science card itself.
MARS_UNIVERSITY = "triggered effect of Mars University"
DRAWING_TRIGGERS = re.compile(r"triggered effect of (Olympus Conference|Point Luna)")
SELF_DRAWING = {
    "Research", "Lagrange Observatory", "Technology Demonstration", "Martian Survey", "Biolabs",
    "Io Research Outpost", "Invention Contest", "Business Contacts",
}  # fmt: skip

# Valley Trust's first action shows 3 Prelude Cards and plays one of them.
VALLEY_TRUST = "valley_trust"
VALLEY_TRUST_SHOWS = 3

# Where a played card was found in its Player's hand: named there, one of the unnamed cards (the play
# gives its name), or missing (the log missed it entering).
Found = Literal["named", "unnamed", "missing"]

# Mars University, whose discard some logs drop: "triggered" once it triggers with nothing else that
# could draw, "due" once its Player has chosen ("Player 1 other") and no discard is logged yet.
MarsUniversity = Literal["triggered", "due"] | None


def known_id(name: str) -> str:
    """The catalog id of a card the log names, or the name itself if the catalog has no such card."""
    return card_id(name) or name


@cache
def prelude_cards() -> frozenset[str]:
    return frozenset(card["id"] for card in catalog() if card["type"] == "prelude")


@cache
def corporations() -> frozenset[str]:
    return frozenset(card["id"] for card in catalog() if card["type"] == "corporation")


def names_corporation(names: list[str] | None) -> bool:
    return any(known_id(name) in corporations() for name in names or [])


def mars_university_alone(move: dict[str, Any]) -> bool:
    """Whether Mars University is the only card in a move that could make its Player draw."""
    return not DRAWING_TRIGGERS.search(move.get("description") or "") and move.get("card_played") not in SELF_DRAWING


def listed(text: str) -> tuple[int, list[str] | None]:
    """How many cards a line lists after its verb, and their names if it gives them: "3 cards: A, B, C",
    "A, B", "2 card/s" or "a card". A reason in brackets at the end is left out."""
    text = text.split(" (")[0].strip()
    counted = COUNT.match(text)
    if counted:
        names = counted.group(2)
        return int(counted.group(1)), [name.strip() for name in names.split(", ")] if names else None
    if text == "a card":
        return 1, None
    names = [name.strip() for name in text.split(", ") if name.strip()]
    return len(names), names


@dataclass
class Hand:
    """A Player's hand: the cards named in it, cards whose names the log doesn't give ("unnamed"), and
    the number that left it without a name ("gone"), which are among the others. Each card is unique, so
    a card named in the hand is never added again: newer logs repeat keeps in summaries."""

    cards: Counter[str] = field(default_factory=Counter)
    unnamed: int = 0
    gone: int = 0

    @property
    def size(self) -> int:
        return self.cards.total() + self.unnamed - self.gone

    @property
    def exact(self) -> bool:
        """Whether every card in the hand is known by name."""
        return self.unnamed == 0 and self.gone == 0

    def add(self, names: list[str], unnamed: int = 0) -> None:
        for name in names:
            self.cards[known_id(name)] += 1
        self.unnamed += unnamed

    def discard(self, count: int) -> None:
        """Cards leave the hand, the log doesn't say which."""
        if self.cards:
            self.gone += count
        else:
            self.unnamed -= count

    def play(self, name: str) -> Found:
        """A card leaves the hand to be played. One not named in the hand is one of the unnamed cards, if
        any; else the log missed it entering."""
        card = known_id(name)
        if self.cards[card] > 0:
            self.cards[card] -= 1
            if self.cards[card] == 0:
                del self.cards[card]
            return "named"
        if self.unnamed > 0:
            self.unnamed -= 1
            return "unnamed"
        return "missing"

    def resync(self, counter: int) -> None:
        """Takes the size from Board Game Arena's Hand Counter: cards the log missed leaving are gone, and
        cards it missed entering are unnamed."""
        if self.size > counter:
            self.discard(self.size - counter)
        else:
            self.unnamed += counter - self.size


@dataclass(frozen=True)
class CounterCheck:
    """The rebuilt hand's size against Board Game Arena's Hand Counter, at a move where the counter is
    fresh: it changes almost only at its own Player's "plays card" moves, and lags everywhere else."""

    move_number: int
    player: int
    rebuilt: int
    counter: int


@dataclass(frozen=True)
class Play:
    """A card a Player played from their hand, and where it was found there."""

    move_number: int
    player: int
    card: str
    found: Found


@dataclass
class Keep:
    """The cards a Player is keeping at setup or buying in a Research phase, before they reach the hand.
    Newer logs list them ("keeps 5 cards: …"); old ones give the perspective Player's names one line at a
    time ("You buy …", "You got …") and a count for both Players ("keeps 5 card/s"). Some versions keep
    one card at a time, and "drafts X" of a card being kept takes it back."""

    names: list[str] | None = None
    count: int | None = None
    named_lines: list[str] = field(default_factory=list)
    starting_over: bool = False

    def keep(self, names: list[str], *, whole: bool) -> None:
        """A keep line. Several cards are the whole keep so far (a summary); one card adds to it, unless the
        Player cancelled their move, after which their next keep starts again."""
        if whole or self.names is None or self.starting_over:
            self.names = names
            self.starting_over = False
        else:
            self.names += [name for name in names if name not in self.names]

    def take_back(self, name: str) -> None:
        if self.names and name in self.names:
            self.names = [kept for kept in self.names if kept != name]

    def cards(self) -> tuple[list[str], int]:
        """The cards kept by name, and how many more were kept without one."""
        names = self.names if self.names is not None else self.named_lines
        unnamed = 0 if self.count is None else max(0, self.count - len(names))
        return names, unnamed


@dataclass
class MoveReading:
    """What one move does to the hands, gathered line by line before it is applied: cards played (by the
    Player who played them, None if no one is named), cards entering hands named or only counted (by
    kind, "draws", "keeps" or "reveals", and Player), the Players who looked at cards, and the Player
    choosing for Mars University in it."""

    plays: dict[str, int | None] = field(default_factory=dict)
    named: dict[tuple[str, int], list[str]] = field(default_factory=dict)
    counted: Counter[tuple[str, int]] = field(default_factory=Counter)
    looked: set[int] = field(default_factory=set)
    choosing: int | None = None

    def gain(self, kind: str, player: int, text: str) -> None:
        count, names = listed(text)
        if names is None:
            self.counted[(kind, player)] += count
        else:
            self.named.setdefault((kind, player), []).extend(names)

    def drawn(self, player: int) -> int:
        return max(len(self.named.get(("draws", player), [])), self.counted[("draws", player)])


class HandReader:
    """Reads a Recorded Game's slim moves in order, following each Player's hand.

    Setup and each Research phase are a buying stage: what the Players keep reaches their hands only
    when the Action phase begins, as keeps are logged one at a time, repeated, summarised or cancelled."""

    def __init__(self, *, prelude: bool, resync: bool = False) -> None:
        """With resync, each hand's size is corrected to the Hand Counter wherever the counter is fresh
        (see CounterCheck), the difference counting as cards gone or unnamed: an error then lasts only
        until the Player's next play, and the hand is marked inexact. Checks are taken before correcting."""
        self.prelude = prelude
        self.resync = resync
        self.hands = [Hand() for _ in range(PLAYERS)]
        self.keeps = [Keep() for _ in range(PLAYERS)]
        self.generation = 1
        self.buying = True
        # Cards named entering a hand that an old log's count line ("draws 2 cards") may still cover, by
        # kind ("draws" or "keeps") and Player. The count follows the names within one Action.
        self.named_uncounted: Counter[tuple[str, int]] = Counter()
        # How many cards each Player is about to look at, if a look of an old log is due.
        self.looking = [0] * PLAYERS
        self.corporations: list[str | None] = [None] * PLAYERS
        # Whether a Player's next Prelude Card is played straight from the cards Valley Trust shows.
        self.playing_from_look = [False] * PLAYERS
        self.mars_university: list[MarsUniversity] = [None] * PLAYERS
        # Each Player's plays by where the card was found in their hand.
        self.plays = [Counter(named=0, unnamed=0, missing=0) for _ in range(PLAYERS)]
        self.played: list[Play] = []
        self.checks: list[CounterCheck] = []
        self.resynced = 0  # Checks at which resync corrected a hand.
        # Lines moving cards that name a Player neither "Player 1" nor "Player 2" (an account renamed
        # since), and plays credited to no one: they can't be followed, so the hands may be wrong.
        self.unread = 0
        self.counters: list[int | None] = [None] * PLAYERS

    def read(self, move: dict[str, Any]) -> None:
        generation = (move.get("game_state") or {}).get("generation") or self.generation
        new_generation = generation != self.generation
        if new_generation:
            self.generation = generation
            self.buying = True
        elif self.buying and (move.get("card_played") or move.get("action_type") in ACTION_TYPES):
            self.end_buying()
        reading = MoveReading()
        if move.get("card_played") and not self.buying:
            mover = move.get("player")
            reading.plays[move["card_played"]] = mover  # The description may name who played it instead.
            if mover is not None:
                self.watch_for_look(mover, move["card_played"])
        for line in (move.get("description") or "").split(" | "):
            subject = SUBJECT.match(line.strip())
            if not subject:
                self.unread += bool(UNREAD_CARD_LINE.search(line))
                continue
            who, rest = subject.groups()
            player = move.get("player") if who == "You" else int(who[-1]) - 1
            if player is None:
                continue
            chosen = re.match(r"^chooses? corporation (.*)$", rest)
            if chosen:
                self.corporations[player] = known_id(chosen.group(1))
            if self.buying and not new_generation and ENDS_BUYING.match(rest):
                self.end_buying()
            if self.buying and not self.drawn_at_setup(rest):
                self.read_buying(player, rest)
            else:
                self.read_action_line(move, reading, player, rest)
        for player in reading.looked:
            self.looking[player] = 0
        self.infer_dropped_discard(move, reading)
        self.add_gains(reading)
        self.apply_plays(move, reading.plays)
        self.check(move)

    def read_action_line(self, move: dict[str, Any], reading: MoveReading, player: int, rest: str) -> None:
        """A line of the Action phase (or a draw at setup), by the given Player."""
        if ACTION_STARTS.match(rest):
            self.named_uncounted[("draws", player)] = self.named_uncounted[("keeps", player)] = 0
            self.mars_university[player] = None
            self.looking[player] = 0  # A look is due only within the Action that shows the cards.
        if rest == MARS_UNIVERSITY:
            self.mars_university[player] = "triggered" if mars_university_alone(move) else None
        elif only_other(move, player) and (
            self.mars_university[player] == "triggered" or move.get("reason") == MARS_UNIVERSITY
        ):
            self.mars_university[player] = "due"
            reading.choosing = player
        revealed = REVEALED_TO_HAND.match(rest)
        if rest.startswith("plays card "):
            card = rest.removeprefix("plays card ")
            reading.plays[card] = player  # The description names who played it.
            self.watch_for_look(player, card)
        elif (
            rest == "has a mandatory action to perform as a first action" and self.corporations[player] == VALLEY_TRUST
        ):
            self.looking[player] = VALLEY_TRUST_SHOWS
            self.playing_from_look[player] = True
        elif rest.startswith("cannot play card "):  # "…, player discards it and gains compensation"
            reading.plays[rest.removeprefix("cannot play card ").split(",")[0]] = player
        elif rest.startswith("activates "):
            self.looking[player] = LOOKS_ON_ACTIVATION.get(rest.removeprefix("activates "), self.looking[player])
        elif rest.startswith("draws "):
            count = listed(rest.removeprefix("draws "))[0]
            if str(player) in (move.get("card_options") or {}) or count == self.looking[player]:
                reading.looked.add(player)  # A look: the cards kept from it follow.
            else:
                reading.gain("draws", player, rest.removeprefix("draws "))
        elif rest.startswith(("keep ", "buy ", "keeps ")):  # Old logs name one card: "You keep X", "You buy X".
            self.looking[player] = 0
            reading.gain("keeps", player, rest.split(" ", 1)[1])
        elif revealed:
            reading.gain("reveals", player, revealed.group(1))
        elif rest.startswith("discards "):
            self.hands[player].discard(listed(rest.removeprefix("discards "))[0])
            self.mars_university[player] = None

    def watch_for_look(self, player: int, card: str) -> None:
        """A card that shows cards from the deck when played: an old log's next draw of that many is a look."""
        self.looking[player] = LOOKS_ON_PLAY.get(card, self.looking[player])

    def infer_dropped_discard(self, move: dict[str, Any], reading: MoveReading) -> None:
        """A one-card draw by a Player whose Mars University discard is due, in a later move than their
        choice, means the log dropped the discard. Any other move of theirs but a bare choice ends it."""
        player = move.get("player")
        if player not in range(PLAYERS) or player == reading.choosing or self.mars_university[player] != "due":
            return
        if reading.drawn(player) == 1:
            self.hands[player].discard(1)
            self.mars_university[player] = None
        elif not only_other(move, player):
            self.mars_university[player] = None

    def check(self, move: dict[str, Any]) -> None:
        """Compares each hand with the Hand Counter where the counter is fresh: it has just changed, at a
        move with its Player's own "plays card" line. Before its first change it may not have started."""
        trackers = (move.get("game_state") or {}).get("player_trackers") or {}
        for player in range(PLAYERS):
            counter = (trackers.get(str(player)) or {}).get("Hand Counter")
            previous, self.counters[player] = self.counters[player], counter
            own_play = re.search(rf"(?:^|\| )Player {player + 1} plays card ", move.get("description") or "")
            if None not in (counter, previous) and counter != previous and own_play and not self.buying:
                hand = self.hands[player]
                self.checks.append(CounterCheck(move.get("move_number"), player, hand.size, counter))
                if self.resync and hand.size != counter:
                    self.resynced += 1
                    hand.resync(counter)

    def apply_plays(self, move: dict[str, Any], plays: dict[str, int | None]) -> None:
        if move.get("action_type") == "play_card" and not plays and not self.buying and "player" in move:
            self.hands[move["player"]].discard(1)  # A play the log doesn't name.
        for card, player in plays.items():
            if player is None:
                self.unread += 1
            elif self.playing_from_look[player] and known_id(card) in prelude_cards():
                self.playing_from_look[player] = False
            elif known_id(card) not in corporations():
                found = self.hands[player].play(card)
                self.plays[player][found] += 1
                self.played.append(Play(move.get("move_number"), player, known_id(card), found))

    def drawn_at_setup(self, rest: str) -> bool:
        """Whether a line of setup draws cards into the hand, as Point Luna does. The deal of 10 is not,
        nor a setup keep logged as a draw (it names the Corporation)."""
        if self.generation != 1 or not rest.startswith("draws "):
            return False
        count, names = listed(rest.removeprefix("draws "))
        return count != DEALT and not names_corporation(names)

    def read_buying(self, player: int, rest: str) -> None:
        """A line of setup or a Research phase. Draws here are a deal, not the hand's, except a setup keep
        that one version logs as a draw ("draws 10 cards: Point Luna, …")."""
        keep = self.keeps[player]
        if rest == "takes back their move":
            self.keeps[player] = Keep()
        elif rest == "cancels their move":
            keep.starting_over = True
        elif rest.startswith("keeps ") or (self.generation == 1 and rest.startswith("draws ")):
            count, names = listed(rest.split(" ", 1)[1])
            if rest.startswith("draws ") and not names_corporation(names):
                return  # The deal.
            if names is None:
                keep.count = count + (2 if self.prelude and self.generation == 1 else 0)
                return
            for name in names:
                if known_id(name) in corporations():
                    self.corporations[player] = known_id(name)
            keep.keep([name for name in names if known_id(name) not in corporations()], whole=len(names) > 1)
        elif rest.startswith(("buy ", "got ")):
            keep.named_lines.append(rest.split(" ", 1)[1])
        elif rest.startswith("drafts "):
            keep.take_back(rest.removeprefix("drafts "))

    def add_gains(self, reading: MoveReading) -> None:
        """Cards drawn or kept in a move enter the hand. Old logs name the perspective Player's cards and
        count them again, so a count adds unnamed cards only beyond those named since the Action began."""
        for key in reading.named.keys() | reading.counted.keys():
            hand = self.hands[key[1]]
            names = reading.named.get(key, [])
            if names_corporation(names):
                continue  # The setup keep, logged again as a draw.
            hand.add([name for name in dict.fromkeys(names) if known_id(name) not in hand.cards])
            self.named_uncounted[key] += len(names)
            if reading.counted[key]:
                hand.add([], max(0, reading.counted[key] - self.named_uncounted[key]))
                self.named_uncounted[key] = max(0, self.named_uncounted[key] - reading.counted[key])

    def end_buying(self) -> None:
        """The Action phase begins: what each Player kept enters their hand."""
        for hand, keep in zip(self.hands, self.keeps):
            hand.add(*keep.cards())
        self.keeps = [Keep() for _ in range(PLAYERS)]
        self.buying = False


def only_other(move: dict[str, Any], player: int) -> bool:
    """Whether a move is nothing but a Player's choice the log doesn't describe ("Player 1 other")."""
    return move.get("description") == f"Player {player + 1} other"

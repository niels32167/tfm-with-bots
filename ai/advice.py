"""What a Controller would do at a human's Decision, to learn from (ADR 0015): the Option it would pick and how it rates
each one it weighed. A Controller that can say how it rates Options has `advise(handle)`; of any other, only its pick is
known. Like a pick, advice reads only the handle, so it gives away nothing its Player can't see.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from ai.controller import Controller, Handle


@dataclass(frozen=True)
class Measure:
    """Something a Controller rates Options by: its name for people, and whether it is a share of 1, shown in percent."""

    name: str
    percent: bool = False


WINS = Measure("Chance to win", percent=True)
STRONG_PLAYERS = Measure("Strong Players pick it", percent=True)
PRICE = Measure("Price in MegaCredits")


@dataclass(frozen=True)
class Advice:
    """The index of the Option a Controller would pick, and by Option index what it measures it at by each of
    `measures`, None where it has nothing. An Option it didn't weigh at all isn't in `measured`."""

    picked: int
    measures: Sequence[Measure] = ()
    measured: dict[int, list[float | None]] = field(default_factory=dict)

    def ranked(self) -> list[int]:
        """The Options rated, best first: the one it would pick, then by the first measure that tells them apart."""

        def rank(index: int) -> tuple[bool, list[tuple[bool, float]]]:
            values = [(value is None, -(value or 0.0)) for value in self.measured[index]]
            return index != self.picked, values

        return sorted(self.measured, key=rank)


def advice(controller: Controller, handle: Handle) -> Advice:
    """What `controller` would do, as far as it can say."""
    advise = getattr(controller, "advise", None)
    return Advice(controller.pick(handle)) if advise is None else advise(handle)

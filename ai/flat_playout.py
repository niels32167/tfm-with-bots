"""The Flat Playout Bot: search at its simplest, and the first Controller to look ahead fairly. For each
Option it picks that Option on Sampled Positions and plays them out with Random Bots, then picks the
Option whose playouts end with the best mean Victory Point margin over the best other Player.

It looks ahead only through the handle's Sampled Positions, never a copy of the real Game (ADR 0013).
Every Option is tried on the same samples, played out from the same seeds, so that the Options are
compared on equal terms rather than on the luck of the draw.
"""

from ai.controller import Handle

# How many Sampled Positions each Option is played out on.
PLAYOUTS = 20

# Seeds for the engine are whole numbers below 2^63.
SEEDS = 1 << 63


class FlatPlayout:
    def __init__(self, playouts: int = PLAYOUTS) -> None:
        self.playouts = playouts

    def pick(self, handle: Handle) -> int:
        options = len(handle.decision["options"])
        if options == 1:
            return 0
        seeds = [(handle.random.randrange(SEEDS), handle.random.randrange(SEEDS)) for _ in range(self.playouts)]
        margins = [self.mean_margin(handle, index, seeds) for index in range(options)]
        return margins.index(max(margins))

    def mean_margin(self, handle: Handle, index: int, seeds: list[tuple[int, int]]) -> float:
        """The mean Victory Point margin of the deciding Player over the best other Player, once the
        Game is played out at random after picking Option `index`."""
        total = 0
        for sample_seed, playout_seed in seeds:
            sample = handle.sample(seed=sample_seed)
            sample.pick(index)
            sample.play_randomly(seed=playout_seed)
            points = {score["player"]: score["total"] for score in sample.scores}
            total += points.pop(handle.player) - max(points.values())
        return total / len(seeds)

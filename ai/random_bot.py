"""The Random Bot: the first Controller on the seam, and the bottom rung of the ladder."""

from ai.controller import Handle


class RandomBot:
    """Picks one of the offered Options at random, each equally likely."""

    def pick(self, handle: Handle) -> int:
        return handle.random.randrange(len(handle.decision["options"]))

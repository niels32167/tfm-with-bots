# A Game is fully reproducible from its Replay

A Game is determined entirely by its seed and the Options picked, in order. Replaying the same Replay must always produce the same Game, on any machine.

Save files, undo, the dev panel's replay, bug reports and failing fuzz Games all rely on this. Anything that could make the engine nondeterministic, such as iterating a randomly ordered hash map or reading the clock, must not influence the game.

**Amended (2026-11-12, ticket 07 of phase 2): Sampled Positions.** A Sampled Position is the one Game that has no Replay to rebuild it from. It is made from a Player View with the hidden cards dealt at random, and its Replay starts "sampled", so that it never carries the real Game's seed or Replay, which would give the hidden cards back (ADR 0013). It is still deterministic: the same position and sample seed always give the same sample, and the Replay's picks record what was played on it. Rebuilding one is refused with an error.

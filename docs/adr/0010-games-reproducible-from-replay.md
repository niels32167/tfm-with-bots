# A Game is fully reproducible from its Replay

A Game is determined entirely by its seed and the Options picked, in order. Replaying the same Replay must always produce the same Game, on any machine.

Save files, undo, the dev panel's replay, bug reports and failing fuzz Games all rely on this. Anything that could make the engine nondeterministic, such as iterating a randomly ordered hash map or reading the clock, must not influence the game.

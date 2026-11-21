"""Ticket 16: do Option labels repeat within a Decision? The Search Bot's tree finds Options again by label."""
import collections, random
import tm_engine
repeats = collections.Counter(); decisions = 0; rng = random.Random(0)
for seed in range(50):
    game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True)
    for _ in range(5000):
        decision = game.decision
        if decision is None:
            break
        labels = [o["label"] for o in decision["options"]]
        decisions += 1
        if len(set(labels)) < len(labels):
            repeats[decision["kind"]] += 1
            if repeats[decision["kind"]] == 1:
                print(decision["kind"], [l for l, n in collections.Counter(labels).items() if n > 1][:3])
        game.pick(rng.randrange(len(labels)))
print(decisions, "Decisions;", dict(repeats))

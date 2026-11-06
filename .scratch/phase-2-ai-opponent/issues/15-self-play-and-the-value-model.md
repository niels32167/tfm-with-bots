# 15 — Self-play and the Value Model

**What to build:** A training loop that starts from the Imitation Model and improves by self-play, and the Value Model, which estimates a Player's chance of winning from their Player View.

**The loop:**
- Many processes play Games on the CPU cores, with one process batching model evaluations on the GPU if that proves faster.
- Opponents come from a pool of earlier versions, including the Card Economy Bot and the Imitation Model, so that the model doesn't forget how to beat old strategies.
- A new version joins only if it wins a Match against the current best.

**The Value Model:** it first learns from Recorded Games' results and from self-play. A Controller then picks by trying each Option on a Sampled Position, averaged over a few samples, and comparing what the model says. This is the TD-Gammon recipe, and it fits cheap copies and a game with chance. Whether the policy from the Imitation Model stays to narrow which Options are tried is a call for this ticket.

**Limits:** 16 cores, 12 GB of RAM, a 6 GB GPU and limited disk. Training is streamed and checkpointed, and long runs need my OK. Games aren't stored unless a check needs them.

**Blocked by:** 07 — Sampled Positions; 14 — Imitation Model for all Decisions

**Status:** ready-for-agent

- [ ] One command runs the loop, stops and resumes safely, and stays within the limits above, with memory and disk measured under Comments.
- [ ] Progress is visible: a rating over time against a fixed set of old Controllers, plotted or logged.
- [ ] The result wins a Match against the Controller from ticket 14, with the interval above 50%, using a budget of a few seconds per Decision or less.
- [ ] Its Games against itself are recorded beside the human benchmark.
- [ ] Test: the loop runs end to end on a tiny model in the normal test suite, with no GPU, and its Controllers go through the fair handle.
- [ ] A training run's settings, seed and engine version are saved with its model, so that it can be repeated.

## Comments

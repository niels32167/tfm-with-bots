# The AI is built as a ladder of Controllers, not one training loop

We build a series of Controllers, each playable and each the benchmark for the next: Card Economy Bot, Imitation Model, Value Model trained by self-play, then search with Sampled Positions at play time. A Controller moves up only by winning a Match against the one before it.

**Considered options:**
- *AlphaZero-style search on every self-play Decision.* It has the highest ceiling, but plain AlphaZero assumes no hidden information, and at 100 search steps over about 430 Decisions it needs about 43,000 network evaluations per Game on an RTX 3050. Failures are also hard to diagnose.
- *A policy network trained with PPO, without search.* It has fast Games and simple plumbing, but long Games and a noisy final result make learning hard, and it tends to get stuck.

With a ladder, each step gives something usable even if the next one fails, and search is spent at play time, where a few seconds per Decision is affordable.

**Strategy knowledge goes in as model inputs and as a training start, never as fixed rules.** The model is given computed facts such as payback, Generations left and distance to Requirements, and is free to overrule them. A hand-written rule that overrides the model would cap its strength wherever the rule is wrong.

**No Controller sees hidden cards, including in lookahead.** Trying an Option on a copy of the real Game would leak them, as soon as a draw shows the next card. So every lookahead uses a Sampled Position, and a Controller is handed only the Player View, the Decision and a way to get Sampled Positions, never the Game itself. The goal of beating a human fairly depends on this.

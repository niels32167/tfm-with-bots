"""The Value Model (CONTEXT.md; ticket 15 of phase 2): it estimates a Player's chance of winning from their Player
View, and learns it first from Recorded Games' results and then from self-play.

- encoded.py: a Player View alone as a position, what the model reads.
- samples.py: positions with whether their Player won and by how many Victory Points, from Recorded Games'
  replays and from the loop's Games.
- model.py: the model, warm-started from the Imitation Model's weights, and how it is saved and loaded.
- train.py: training on streamed samples.
- bot.py: the Value Bot, the Controller that tries the Imitation Model's likeliest Options on Sampled Positions and
  picks the one the Value Model rates best.
- loop.py: `uv run python -m ai.value.loop`, the self-play loop.

Models and the loop's runs are saved in .cache/models: out of git, never published.
"""

from ai.imitation import MODELS_FOLDER

# The model the registered Value Bot plays with: the best version of a loop's run, copied there.
MODEL = MODELS_FOLDER / "value.pt"
# Where the loop keeps its runs, one folder each.
RUNS_FOLDER = MODELS_FOLDER / "value-runs"

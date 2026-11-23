#!/bin/bash
# Gathers the Hugging Face Space's files (ADR 0014) into a folder: the committed project, the three models the bots
# play with, and the Space's card as its README. The Space builds the Dockerfile at the folder's root.
#   deploy/huggingface/make_space.sh [folder]    (default .cache/deploy/space)
# Then upload it, logged in to Hugging Face with `uvx --from huggingface_hub hf auth login`:
#   uvx --from huggingface_hub hf upload <user>/<space> <folder> . --repo-type space
set -euo pipefail
# The project is the one this script is in, wherever it is run from.
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
cd "$root"
out=${1:-.cache/deploy/space}
if [ -n "$(git status --porcelain)" ]; then
    echo "commit first: the Space is made from the committed project, and nothing else may be waiting" >&2
    exit 1
fi
rm -rf "$out"
mkdir -p "$out/.cache/models"
git archive HEAD | tar -x -C "$out"
cp .cache/models/imitation.pt .cache/models/imitation-draft-buy.pt .cache/models/value.pt "$out/.cache/models/"
# The project's own README is kept beside the Space's card, which Hugging Face reads for the Space's settings.
mv "$out/README.md" "$out/PROJECT.md"
cp deploy/huggingface/README.md "$out/README.md"
echo "$out: the Space's files for $(git rev-parse --short HEAD), $(du -sh "$out" | cut -f1)"

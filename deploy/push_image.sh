#!/bin/bash
# Builds the hosted server's image (Dockerfile, ADR 0014) from the committed project, with the three models from
# .cache/models, and pushes it to GitHub's registry as ghcr.io/niels32167/terraforming-mars, tagged with the commit
# and "latest". Render runs "latest". Log Docker in to ghcr.io first (README: Host it online).
#   deploy/push_image.sh
set -euo pipefail
# The project is the one this script is in, wherever it is run from.
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
cd "$root"
if [ -n "$(git status --porcelain)" ]; then
    echo "commit first: the image is built from the committed project, and nothing else may be waiting" >&2
    exit 1
fi
image=ghcr.io/niels32167/terraforming-mars
commit=$(git rev-parse --short HEAD)
docker build -t "$image:$commit" -t "$image:latest" .
docker push "$image:$commit"
docker push "$image:latest"
echo "pushed $image:$commit and :latest"

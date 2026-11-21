#!/bin/bash
# Ticket 16's budget sweep against the Value Bot, on seeds from 3,000,000 (not the final Match's 0-199), one Match at
# a time, each report kept in .cache/ticket-16/.
set -u
out=.cache/ticket-16
run() { echo "== $1 $(date +%T)"; uv run python -u -m ai.match "$1" value --games "$2" --processes 10 --first-seed 3000000 > "$out/sweep-$3.txt" 2>&1; echo "done $(date +%T)"; }
run "search?seconds=0.1" 100 0.1s
run "search?seconds=1" 100 1s
run "search?seconds=1&leaves=playouts" 40 1s-playouts
run "search?seconds=5" 20 5s

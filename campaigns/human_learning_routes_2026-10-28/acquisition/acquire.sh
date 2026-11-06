#!/bin/sh
# Public source only. Run from repository root. Expected MD5 recorded below.
set -eu
target=campaigns/human_learning_routes_2026-10-28
curl -L --fail --retry 2 --max-time 300 -D "$target/acquisition/trials.headers" -o "$target/inputs/processed_data_2026.csv" https://zenodo.org/api/records/23072548/files/processed_data_2026.csv/content
.venv/bin/python "$target/experiments/inspect_inputs.py"
# Published MD5: 5bc8ccf8bdca2e89fc21d20ffb7c1695

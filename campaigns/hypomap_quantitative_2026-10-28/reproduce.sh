#!/usr/bin/env bash
# Offline scientific reproduction using the finalized preserved inputs.
# Invoke with bash; does not install packages or acquire network data.
set -euo pipefail
campaign_dir="$(cd "$(dirname "$0")" && pwd)"
repo_dir="$(cd "$campaign_dir/../.." && pwd)"
cd "$repo_dir"
export MPLCONFIGDIR="$repo_dir/.mplconfig"
analysis_python="$repo_dir/.venv/bin/python"
acquisition_python="$campaign_dir/.venv/bin/python"
shasum -a 256 -c "$campaign_dir/PROTOCOL.sha256"
"$acquisition_python" "$campaign_dir/experiments/acquire_verify.py" > "$campaign_dir/logs/reproduce_integrity.log" 2> "$campaign_dir/logs/reproduce_integrity.stderr"
"$analysis_python" "$campaign_dir/experiments/provenance_review/reconcile_metadata.py" > "$campaign_dir/logs/reproduce_metadata.log" 2> "$campaign_dir/logs/reproduce_metadata.stderr"
"$analysis_python" "$campaign_dir/experiments/provenance_review/reconcile_depth.py" > "$campaign_dir/logs/reproduce_depth.log" 2> "$campaign_dir/logs/reproduce_depth.stderr"
"$analysis_python" "$campaign_dir/experiments/abundance.py" selected > "$campaign_dir/logs/reproduce_abundance.log" 2> "$campaign_dir/logs/reproduce_abundance.stderr"
"$analysis_python" "$campaign_dir/experiments/signature_eligibility.py" > "$campaign_dir/logs/reproduce_signature.log" 2> "$campaign_dir/logs/reproduce_signature.stderr"
"$analysis_python" "$campaign_dir/experiments/technical/run.py" --stage all --reps 10 > "$campaign_dir/logs/reproduce_technical.log" 2> "$campaign_dir/logs/reproduce_technical.stderr"
"$analysis_python" "$campaign_dir/experiments/technical/extra_controls.py" > "$campaign_dir/logs/reproduce_extra.log" 2> "$campaign_dir/logs/reproduce_extra.stderr"
"$acquisition_python" "$campaign_dir/experiments/adversarial/audit.py" > "$campaign_dir/logs/reproduce_audit.log" 2> "$campaign_dir/logs/reproduce_audit.stderr"
"$analysis_python" "$campaign_dir/experiments/adversarial/sensitivity_review.py" > "$campaign_dir/logs/reproduce_sensitivity_review.log" 2> "$campaign_dir/logs/reproduce_sensitivity_review.stderr"
printf 'Offline quantitative campaign reproduction completed. Logs: %s\n' "$campaign_dir/logs"

"""Exact finite-source information calculation; no learning fits or scores.

Only actual trials 0:200 supply person-specific evidence. Future source-table
inputs are compared after source identification, without future human outcomes.
"""
import csv
import hashlib
import io
import json
import math
import resource
import sys
from datetime import datetime, timezone

from inspect_source import ROOT, OUT, SRC, workbook


def main():
    started = datetime.now(timezone.utc).isoformat()
    tables = []
    pins = []
    explicit_bytes = 0
    for n in range(10):
        path = SRC / ("pregen_sequence_%d.xlsx" % n)
        raw, members, cells = workbook(path)
        header = {"".join(c for c in k if c.isalpha()): v for k, v in cells[0].items()}
        rows = []
        for cellrow in cells[1:601]:
            r = {header["".join(c for c in k if c.isalpha())]: v for k, v in cellrow.items()}
            eccentricity = float(r["eccentricity"])
            delta = float(r["contrastDelta"])
            assert eccentricity in (-15., 15.)
            side = 1 if eccentricity < 0 else -1
            # The original preprocessing normalizes the .5..7 high grating
            # contrast to 0..1; this is checked against cached prefix inputs.
            visible_c = side * delta / .2
            rows.append((visible_c, side, float(r["bias"])))
        assert len(rows) == 600
        tables.append(rows)
        explicit_bytes += len(raw) + sum(members.values())
        pins.append({"path": str(path.relative_to(ROOT)), "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest(),
                     "zip_uncompressed_directory_sum": sum(members.values()),
                     "exposure": "All source-sheet XML strings decoded; numeric interpretation limited to first600 planned inputs."})

    # Exact distinguishability of the ten finite planned input tables.
    source_units = []
    for i in range(10):
        candidates = list(range(10))
        first_unique = None
        for t in range(200):
            candidates = [j for j in candidates if abs(tables[j][t][0] - tables[i][t][0]) < 1e-8]
            if len(candidates) == 1 and first_unique is None:
                first_unique = t + 1
        source_units.append({"source": i, "visible_contrast_only_first_unique_trial_one_based": first_unique,
                             "candidate_sources_after200": candidates})

    path = ROOT / "campaigns/human_learning_routes_2026-10-28/inputs/validation_numeric.csv"
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    prefixes = {}
    tokenized_rows = 0
    fields = None
    for r in csv.DictReader(io.StringIO(text)):
        fields = list(r)
        tokenized_rows += 1
        trial = int(float(r["trial"]))
        if trial >= 200:
            continue
        subject = r["subject"].zfill(3)
        c = float(r["sideContrast"])
        ch = float(r["choice"])
        if r["feedbackType"]:
            fb = float(r["feedbackType"])
        else:
            assert ch == 0., "Missing feedback on a responding prefix trial"
            fb = math.nan
        prefixes.setdefault(subject, []).append((trial, c, ch, fb))
    pins.append({"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                 "exposure": "Whole already-consumed CSV acquired/UTF8 decoded/tokenized; numeric choice-feedback interpretation restricted to actual first200 per person."})
    explicit_bytes += 3 * len(raw)

    people = []
    for subject, prefix in sorted(prefixes.items()):
        prefix.sort()
        assert [r[0] for r in prefix] == list(range(200))
        cset = list(range(10))
        rset = list(range(10))
        earliest_c = earliest_r = None
        counts = {"contrast": [], "contrast_and_past_revelation": []}
        for t, c, ch, fb in prefix:
            cset = [i for i in cset if abs(tables[i][t][0] - c) < 1e-8]
            rset = [i for i in rset if abs(tables[i][t][0] - c) < 1e-8]
            if ch in (-1., 1.) and fb in (-1., 1.):
                revealed = ch * fb
                rset = [i for i in rset if tables[i][t][1] == revealed]
            assert cset and rset
            counts["contrast"].append(len(cset))
            counts["contrast_and_past_revelation"].append(len(rset))
            if len(cset) == 1 and earliest_c is None:
                earliest_c = t + 1
            if len(rset) == 1 and earliest_r is None:
                earliest_r = t + 1
        assert len(cset) == len(rset) == 1 and cset == rset
        # With singleton support every probability law supported on compatible
        # source files assigns the same entire future. No prior is assumed.
        future = tables[rset[0]][200:]
        future_degrees = [len({tables[i][t][1] for i in rset}) for t in range(200, 600)]
        assert set(future_degrees) == {1}
        people.append({"subject": subject, "prefix_n": len(prefix), "source": rset[0],
                       "first_unique_contrast_trial_one_based": earliest_c,
                       "first_unique_contrast_and_revealed_trial_one_based": earliest_r,
                       "candidates_after200": rset, "candidate_counts_through_prefix": counts,
                       "future_target_support_size_each_opportunity": sorted(set(future_degrees)),
                       "future400_input_tuple_sha256": hashlib.sha256(json.dumps(future).encode()).hexdigest()})
    assert len(people) == 39

    # Numerical known-answer checks for the information-set implementation.
    # Identical visible prefixes with distinct futures must remain ambiguous.
    mock = [[(0., 1), (1., 1)], [(0., -1), (-1., -1)]]
    contrast_candidates = [i for i in range(2) if mock[i][0][0] == 0.]
    revealed_candidates = [i for i in contrast_candidates if mock[i][0][1] == 1]
    assert contrast_candidates == [0, 1] and revealed_candidates == [0]
    assert len({mock[i][1][1] for i in contrast_candidates}) == 2

    result = {"started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
              "question": "Is future planned teaching input still unobserved after the original permitted first200 calibration in the admitted finite source universe?",
              "scope": "Exact source-support calculation, no probability assignment to IDs or source files, no teacher draws, no learning prediction or score.",
              "source_tables": source_units, "people": people,
              "summary": {"people": len(people), "csv_rows_tokenized": tokenized_rows,
                          "people_singleton_from_visible_contrast_only": sum(len(p["candidates_after200"]) == 1 for p in people),
                          "max_first_unique_contrast_trial_one_based": max(p["first_unique_contrast_trial_one_based"] for p in people),
                          "max_first_unique_contrast_and_revealed_trial_one_based": max(p["first_unique_contrast_and_revealed_trial_one_based"] for p in people),
                          "future_target_support_size_at_all_39x400_opportunities": 1,
                          "conditional_entropy_bits_for_any_source_prior_giving_positive_mass_to_observed_prefix": 0},
              "controls": {"constructed_shared_visible_prefix_retains_two_candidates": True,
                           "constructed_revelation_separates_the_two": True,
                           "constructed_distinct_future_support_retained_without_revelation": True,
                           "actual_cached_prefix_contrast_matches_original_source_rescaling": True},
              "pins": pins, "explicit_source_read_decode_allowance_bytes": explicit_bytes,
              "rss_bytes_darwin": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "python": sys.version, "failures": []}
    (OUT / "FIRST_CALCULATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("completed_utc", "summary", "controls", "explicit_source_read_decode_allowance_bytes", "rss_bytes_darwin")}, indent=2))


if __name__ == "__main__":
    main()

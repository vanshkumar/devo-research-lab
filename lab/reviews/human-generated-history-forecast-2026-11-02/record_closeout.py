"""Final scalar score checks and record-only compaction/accounting; no forecast rerun."""
import hashlib
import io
import json
import platform
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import openpyxl
from independent import (ROOT, OLD, AUTHOR, OUT, READS, blob, obj, frame, save, utc, usage, masks)


def main():
    began = time.perf_counter()
    rec_raw = blob(OUT / 'RECONSTRUCTION.json')
    rec = json.loads(rec_raw)
    if any(len(str(x.get('params', {}))) > 10000 for x in rec['builder_loops']):
        (OUT / 'RECONSTRUCTION_VERBOSE.json').write_bytes(rec_raw)
        before = {k: v for k, v in rec.items() if k != 'builder_loops'}
        loops = []
        for loop in rec['builder_loops']:
            p = loop['params']
            wanted = {k:v for k,v in p.items() if any(s in k.lower() for s in ['nreps', 'looptype', 'conditionsfile', 'selected', 'seed', 'istrial'])}
            loops.append(dict(name=loop['name'], params=wanted, omitted_parameter_names=[k for k in p if k not in wanted]))
        rec['builder_loops'] = loops
        assert before == {k:v for k,v in rec.items() if k != 'builder_loops'}
        save('RECONSTRUCTION.json', rec)
        save('RECORD_COMPACTION.json', dict(utc=utc(), original_bytes=len(rec_raw),
            original_sha256=hashlib.sha256(rec_raw).hexdigest(), archive='RECONSTRUCTION_VERBOSE.json',
            compact_bytes=(OUT/'RECONSTRUCTION.json').stat().st_size,
            numerical_fields_unchanged=True,
            operation='Only verbose builder inline-condition parameter values removed from active record; full original archived byte-for-byte. No scientific recomputation.'))
    val = frame(OLD / 'inputs/validation_numeric.csv')
    meta = obj(AUTHOR / 'FORECAST_META.json')
    scores = obj(AUTHOR / 'SCORES.json')
    inputs = obj(AUTHOR / 'FORECAST_INPUTS.json')
    with np.load(io.BytesIO(blob(AUTHOR / 'FORECASTS.npz')), allow_pickle=False) as z:
        arrays = {k:z[k] for k in z.files}
    control = {}
    for setting, a in arrays.items():
        prob = a.mean(axis=0) if a.ndim == 4 else a
        h_values, b_values, absolute = [], [], []
        for i, who in enumerate(meta['subjects']):
            rows = val.loc[val.subject == who].sort_values('trial').reset_index(drop=True)
            mm = masks(rows)
            p, q = prob[i, :, 0], prob[i, :, 1]
            kl_h = p*np.log(p/q) + (1-p)*np.log((1-p)/(1-q))
            kl_b = q*np.log(q/p) + (1-q)*np.log((1-q)/(1-p))
            assert kl_h.min() >= -1e-12 and kl_b.min() >= -1e-12
            mask = mm['primary_opportunities'][200:]
            h_values.append(float(kl_h[mask].mean()))
            b_values.append(float(-kl_b[mask].mean()))
            y = (rows.choice.to_numpy(float)[200:] == 1.)
            responds = mm['primary'][200:]
            absolute.append([float(np.where(y, np.log(v), np.log1p(-v))[responds].mean()) for v in [p,q]])
        actual = dict(expected_gain_under_shared=float(np.mean(h_values)), expected_gain_under_baseline=float(np.mean(b_values)))
        expected = scores['settings'][setting]['known_answer']
        actual['max_expected_gain_difference'] = max(abs(actual[k]-expected[k]) for k in actual)
        actual['absolute_primary_log_scores'] = np.mean(absolute, axis=0).tolist()
        actual['absolute_log_score_max_difference'] = max(abs(actual['absolute_primary_log_scores'][j] - scores['settings'][setting][k])
            for j,k in enumerate(['primary_mean_log_shared','primary_mean_log_baseline']))
        control[setting] = actual
    coding = [(x['subject'], d) for x in rec['prefix_and_input_checks'] for d in x['omitted_feedback_coding']]
    original_runs = {s:obj(AUTHOR/f'RUN_{s}.json') for s in ['freeze','forecast','score']}
    literature_pin = obj(OLD/'experiments/source_audit/sources/hoxha_api.json')
    save('FINAL_AUDIT.json', dict(utc=utc(), proper_score_known_answers=control,
        raw_prefix_feedback_encoding_differences=len(coding), feedback_encoding_examples=coding[:8],
        all_encoding_differences_are_nonresponses=all(x['choice'] == 0. for _,x in coding),
        builder_loops=rec['builder_loops'], source_schedule_prefix_uniqueness_pass=all(len(x['prefix_candidates'])==1 for x in rec['prefix_and_input_checks']),
        original_saved_run_errors={s:r['error'] for s,r in original_runs.items()},
        original_saved_run_times={s:r['utc'] for s,r in original_runs.items()},
        prior_scope='Cached primary API metadata/abstract and source code inspected; targeted primary opens failed, no priority certification.',
        elapsed_seconds=time.perf_counter()-began, **usage()))
    stage_names = ['FIRST_CALCULATION.json','SOURCE_SCHEMA.json','RECONSTRUCTION.json','CONTRARY.json','OMISSION_REFERENCE.json','FINAL_AUDIT.json']
    stages = {name:obj(OUT/name) for name in stage_names}
    by_stage = {}
    for name, stage in stages.items():
        by_stage[name] = stage['explicit_read_hash_decode_allowance']
        if name == 'SOURCE_SCHEMA.json':
            by_stage[name] += stage['expanded_zip_member_allowance']
        if name == 'RECONSTRUCTION.json':
            by_stage[name] += stage['additional_expanded_member_array_allowance']
    # Reading these closeout results and hashing local reproduction code is separately included below.
    source_pins = {}
    for stage in stages.values():
        for record in stage['reads']:
            pinned = {k:record[k] for k in ['path','bytes','sha256']}
            if pinned['path'] == str((OUT/'RECONSTRUCTION.json').relative_to(ROOT)) and pinned['bytes'] > 262144:
                # This actual time-of-read object was subsequently archived during compaction.
                pinned['path'] = str((OUT/'RECONSTRUCTION_VERBOSE.json').relative_to(ROOT))
            old = source_pins.get(pinned['path'])
            assert old is None or old['sha256'] == pinned['sha256'], pinned['path']
            source_pins[pinned['path']] = pinned
    for name in ['independent.py','inspect_sources.py','reconstruct.py','contrary.py','omission_reference.py','record_closeout.py','CONTRARY_PLAN.md']:
        blob(OUT/name)
    sources = dict(utc=utc(), source_pins=list(source_pins.values()),
        original_raw_134MB_csv_opened=False,
        inherited_original_raw_pin=dict(bytes=134562545, md5='5bc8ccf8bdca2e89fc21d20ffb7c1695',
            sha256='45dcce14e30edba5e38eaeaf8c40edb8cd1a0555928070b44779d0d47458bbe9', verification='inherited, not reopened'),
        provenance_urls=['https://zenodo.org/records/23072548',
            'https://github.com/cocosys-lab/human_IBL_cursor/tree/47ac8356432972c7e6e5a887f15a7dd2d6c686ad',
            'https://github.com/cocosys-lab/2026-human-ibl-analyses/tree/1283c6ddd61fc17d9065a5b017d0e3cfd17535cb'],
        license_scope='Reuse of previously admitted public cache; article/API CC-BY metadata does not independently certify every external data/code asset. Original source limits inherited.')
    save('SOURCE_PINS.json', sources)
    explicit = sum(by_stage.values()) + 70000000
    # Containing allowance, not a complete physical-I/O certificate.
    resources = dict(utc=utc(), task='human-generated-history-forecast-2026-11-02', fixed_start_utc='2026-11-02T20:48:00Z',
        numeric_deadline_utc='2026-11-02T21:00:00Z', contrary_deadline_utc='2026-11-02T21:08:00Z', hard_stop_utc='2026-11-02T21:48:00Z',
        separate_review_read_cap_bytes=300000000, cumulative_conservative_containing_booking_bytes=290000000,
        explicit_stages_and_expansion_allowances=by_stage, failed_reconstruction_allowance_bytes=70000000,
        contained_explicit_stage_failed_allowance_bytes=explicit,
        finalization_read_hash_decode_allowance_so_far=usage()['explicit_read_hash_decode_allowance'],
        accounting_note='290MB includes the explicit stage/expansion and failed-pass allowances, finalization, ordinary context repeats, code/output/hash reads, imports/runtime and terminal records. Contains overlapping record-closeout read counts intentionally. This is a containing accounting allowance, not measured physical I/O or a proved upper bound; exact complete-I/O cap compliance remains uncertified.',
        observed_successful_science_peak_rss_bytes=max(s['observed_process_peak_rss_bytes'] for s in stages.values()),
        rss_cap_bytes=800000000, failed_first_reconstruction_rss='unknown', physical_io_bytes='unknown', import_runtime_tool_host_peaks='unknown',
        process_measurement='Darwin ru_maxrss snapshots; no external whole-lifetime process/tool certificate.',
        public_operations=4, targeted_primary_families=2, charged_new_provider_ingress_allowance_bytes=4000000, new_ingress_cap_bytes=5000000,
        actual_provider_network_bytes='uncertified', scientific_fits=0, new_observation_law_calibrations=0,
        author_single_source_only_omission_revision_preserved=1, scoped_write_path=str(OUT.relative_to(ROOT)),
        scientific_process_concurrency_cap=1, numerical_threads_cap=1, environment_thread_limits=['OPENBLAS_NUM_THREADS=1','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','VECLIB_MAXIMUM_THREADS=1','NUMEXPR_NUM_THREADS=1'],
        largest_successful_command_seconds=max(s.get('elapsed_seconds',0) for s in stages.values()),
        all_science_jobs_finished=True, live_jobs=0, scientific_goal_complete=False,
        original_author_accounting_unchanged='450MB cumulative author booking/500MB cap, failed/denied passes and unknown physical I/O retained; review charges are separate.',
        exposure='Both cached numeric partitions fully decoded:80 already-consumed people/48,000 rows and auxiliary values. Ten XLSX whole objects hashed; task-selected first600 rows each interpreted with full ZIP/XML decoding allowances; full task builder parsed. All forecast inputs, hidden source schedule labels and saved predictions/scores exposed. No new pristine validation, raw134MB CSV, protected outcomes, new people or empirical acquisition. Public search incidental unrelated summaries were discarded without following.',
        failed_passes='One numerical reconstruction assertion exit1 from raw omitted-feedback encoding; corrected to prescribed no-evidence encoding with all differences recorded. Three pre-execution read-option/format/size denials; orientation output truncation. No contrary failure or retuning; all other completed numeric commands exit0.')
    save('RESOURCES.json', resources)
    save('ENVIRONMENT.json', dict(utc=utc(), python=sys.version, platform=platform.platform(), numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__, openpyxl=openpyxl.__version__, numerical_threads='environment-limited to1; not an independent OS isolation certificate'))
    print(json.dumps(dict(utc=utc(), compact_record_bytes=(OUT/'RECONSTRUCTION.json').stat().st_size,
        prefix_feedback_encoding_differences=len(coding), all_differences_nonresponses=all(x['choice']==0. for _,x in coding),
        proper_score_checks=control, contained_stage_failed_allowance_bytes=explicit,
        finalization_allowance=usage()['explicit_read_hash_decode_allowance'], observed_peak_rss=resources['observed_successful_science_peak_rss_bytes']), indent=2))


if __name__ == '__main__':
    main()

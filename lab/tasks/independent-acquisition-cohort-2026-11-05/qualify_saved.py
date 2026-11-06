"""Qualify the already saved 2021 standard catalogue; no behavioral reads."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import resource
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT/'sources/longitudinal_learning_feasibility_2026-10-28'
sys.path.insert(0, str(SOURCE/'tools'))
import duckdb

IO = Counter()
PINS = {}


def read(path):
    data = path.read_bytes()
    IO['explicit_file_reads'] += len(data)
    PINS[str(path.relative_to(ROOT))] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return data


def get(path):
    return json.loads(read(path))


def norm(s):
    return re.sub('[^a-z0-9]', '', s.lower())


def save(name, obj):
    (HERE/name).write_text(json.dumps(obj, indent=2, default=str)+'\n')


def main():
    cpu, wall = time.process_time(), time.monotonic()
    old = ROOT/'campaigns/learning_rule_transport_2026-10-28'
    pop = ROOT/'campaigns/population_learning_transport_2026-10-28'
    main = HERE.parent/'calibration-frontier-main-2026-11-05'
    split = get(old/'protocols/SPLIT.json')
    prep, evaluation = get(main/'PREP_ACCESS.json'), get(main/'MAIN_ACCESS.json')
    freeze = get(pop/'protocols/FREEZE.json')
    events = [json.loads(s) for p in [old/'protocols/EXPOSURE.jsonl',pop/'protocols/EXPOSURE.jsonl']
              for s in read(p).splitlines()]
    original138 = set(prep['subjects']) | set(evaluation['evaluation_subjects'])
    original154 = {r['subject'] for r in split['standard']}
    exposed = {e['subject'] for e in events if 'subject' in e}
    assert len(original138) == 138 and len(original154) == 154
    assert original138 <= original154 and exposed <= original154
    restrictions = {'NYU-21':'first3000 consumed; later473 remain closed',
                    'SWC_007':'all517 opportunities remain protected; aliases SWC007/SWC-007'}
    assert original154-exposed == {'SWC_007'}
    pan = set(freeze['external_subjects']) | set(split['external_prefix_gap_excluded'])
    assert len(pan) == 22
    subjects = []
    for row in split['standard']:
        s = row['subject']
        category = 'original138' if s in original138 else 'additional_prior_consumed' if s in exposed else 'protected'
        subjects.append(dict(**row, canonical_exclusion_key=norm(s), category=category,
                             restriction=restrictions.get(s,'all animal/later sessions excluded from new-unit status')))
    names = sorted(original154 | pan | {'BW362'})
    save('ORIGINAL_EXCLUSIONS.json', dict(
        scope='Every original154 animal excluded before any new payload. Global nicknames are normalized conservatively, including separator/case aliases. Shared session UUIDs must also be excluded across releases; a disjoint nickname alone never certifies freshness.',
        original138_count=len(original138), original154_count=len(original154),
        additional16=sorted(original154-original138),
        additional16_categories=dict(Counter(x['category'] for x in subjects if x['subject'] not in original138)),
        any_original_subject_with_exposure_record=len(exposed),
        protected_ibl_restrictions=restrictions, subjects=subjects,
        external_pan_names=sorted(pan), exclusion_keys=sorted({norm(s) for s in names}),
        all_other_protected_sources='Entirely outside this IBL standard training source scope. No Pan/FP, HABITS, Flesch, memory, worm, motor or optogenetic outcome objects are eligible.'))
    con = duckdb.connect(':memory:')
    p = SOURCE/'standard_cache/sessions.pqt'
    read(p)  # hash/read charge; DuckDB reads the same file separately below
    IO['engine_file_read_conservative_charge'] += p.stat().st_size
    cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{p}')").fetchall()
    rows = con.execute(f"SELECT id,subject,lab,date,number,task_protocol FROM read_parquet('{p}') ORDER BY subject,date,number,id").fetchall()
    IO['decoded_metadata_utf8_representation_bytes'] += len(json.dumps(rows, default=str).encode())
    training = [r for r in rows if 'trainingChoiceWorld' in r[-1]]
    allnames = {r[1] for r in rows}
    assert {r[1] for r in training} == original154
    eids = {str(r[0]) for r in rows}
    assert len(eids) == len(rows)
    save('ORIGINAL_SESSION_IDS.json', dict(
        cache='2021_Q1_IBL_et_al_Behaviour', sessions=[dict(eid=str(r[0]),subject=r[1],lab=r[2],date=str(r[3]),number=r[4],protocol=r[5]) for r in rows],
        purpose='Identity exclusion metadata only. No behavioral payload or performance column read. All sessions of these subjects, including later dates/new releases, remain the same animals.'))
    noel = get(ROOT/'sources/prospective_acquisition_feasibility_2026-10-28/noel_training_metadata.json')
    feasible = get(ROOT/'sources/prospective_acquisition_feasibility_2026-10-28/FEASIBILITY.json')
    summary = dict(
        utc=datetime.now(timezone.utc).isoformat(),status='saved2021 catalogue has zero eligible new standard-training animals',
        full_cache_schema=cols,all_sessions=len(rows),all_subjects=len(allnames),
        training_sessions=len(training),training_subjects=len({r[1] for r in training}),
        new_training_animals_after_exclusions=0,
        nontraining_only_subjects=sorted(allnames-original154),
        nontraining_only_protocols=dict(Counter(r[-1] for r in rows if r[1] not in original154)),
        original138=len(original138),additional16_categories=dict(Counter(x['category'] for x in subjects if x['subject'] not in original138)),
        saved_noel_metadata=dict(training_animals=len(noel['rows']),training_sessions=sum(r[2] for r in noel['rows']),
             catalogue_nickname_overlap=sorted({r[0] for r in noel['rows']} & original154),
             alias_independence='not certified by nicknames alone',
             measurement_sample=feasible['alternative_public_release']['sample_schema_verified'],
             limitation=feasible['alternative_public_release']['limitations'],
             decision='Not promoted to source-equivalent standard WT confirmation; genotype/subject identity mapping and sufficient discrimination unqualified. Published group summaries already exposed in prior task.'),
        current_public_catalogue='Unavailable in this execution: sandbox DNS failure and two platform escalation rejections. Pending user authorization is not approval.',
        no_new_trial_payload_or_prefix=True, new_ingress_bytes=0,
        io=dict(IO),pins=PINS,cpu_seconds=time.process_time()-cpu,
        process_wall_seconds=time.monotonic()-wall,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        unknowns=['Physical engine reads and runtime/import/provider overhead not measured; full engine file sizes conservatively charged separately.'])
    save('SAVED_QUALIFICATION.json', summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['pins','full_cache_schema','nontraining_only_subjects']}, indent=2))


if __name__ == '__main__':
    main()

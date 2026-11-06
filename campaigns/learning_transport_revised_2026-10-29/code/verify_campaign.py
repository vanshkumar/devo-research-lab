"""Read-only completion check of this finite campaign; no trial decoding."""
from pathlib import Path
import datetime as dt
import hashlib
import json

C=Path(__file__).resolve().parents[1]
ROOT=C.parents[1]
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
POP=ROOT/'campaigns/population_learning_transport_2026-10-28'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def verify_entries(path, base):
    obj=read(path)
    entries=obj['files'] if 'files' in obj else [dict(path=p,sha256=s) for p,s in obj['pins'].items()]
    for entry in entries:
        assert sha(base/entry['path'])==entry['sha256'],entry['path']
    return len(entries)


def run():
    counts={}
    for path,base in [(OLD/'protocols/FREEZE.json',OLD),
                      (OLD/'protocols/RNN_FREEZE.json',OLD),
                      (POP/'protocols/FREEZE.json',ROOT),
                      (C/'protocols/FIT_FREEZE.json',ROOT),
                      (C/'protocols/COMPARISON_FREEZE.json',ROOT),
                      (C/'artifacts/decision_controls/CALIBRATION_FREEZE.json',ROOT),
                      (C/'artifacts/known_learner/FREEZE.json',ROOT)]:
        counts[str(path.relative_to(ROOT))]=verify_entries(path,base)
    metadata=read(C/'audits/METADATA_ACCESS_AUDIT.json')
    for p,s in metadata['pins'].items():
        assert sha(ROOT/p)==s,p
    # Preserve the real pre-final-print log mismatch and prove its narrow cause.
    control=C/'artifacts/decision_controls'
    original=read(control/'MANIFEST.json')
    correction=read(control/'POSTEXECUTION_LOG_MANIFEST.json')
    assert sha(control/'MANIFEST.json')==correction['original_manifest_sha256']
    differences=[]
    for p,s in original.items():
        actual=sha(C/p)
        if actual!=s:differences.append(dict(path=p,expected=s,actual=actual))
    assert differences==correction['mismatches']
    assert len(differences)==1 and differences[0]['path']=='artifacts/decision_controls/RUN.stdout'
    for p,s in correction['final_files'].items():assert sha(C/p)==s,p
    lines=(control/'RUN.stdout').read_bytes().splitlines(keepends=True)
    assert hashlib.sha256(b''.join(lines[:-1])).hexdigest()==differences[0]['expected']
    result=read(control/'RESULT.json')
    assert json.loads(lines[-1])==dict(status=result['status'],duration_seconds=result['duration_seconds'])
    comparison=read(C/'artifacts/source_comparison/RESULT.json')
    for entry in comparison['forecast_records']:
        assert sha(ROOT/entry['path'])==entry['sha256'],entry['path']
    fit=read(C/'artifacts/transition_fit/RESULT.json')
    grid_files=0
    for grid in fit['grid_results']:
        for entry in grid['records']:
            assert sha(ROOT/entry['forecast_path'])==entry['forecast_sha256']
            grid_files+=1
    assert sha(C/'model_session_transition.npz')==fit['selected_model_sha256']
    independent=read(C/'audits/INDEPENDENT_RESULT_CHECK.json')
    assert independent['passed'] and independent['stop_before_protected_prefixes']
    for p,s in independent['inputs_sha256'].items():assert sha(ROOT/p)==s,p
    for p,s in independent['historical_ledger_sha256_after'].items():assert sha(ROOT/p)==s,p
    status=read(C/'protocols/VALIDATION_STATUS.json')
    assert not comparison['source_readiness_passed']
    assert not result['primary_controls_passed']
    assert status['external']['prefix_accesses']==status['external']['outcome_accesses']==0
    assert status['external']['release_adopted'] is False
    assert status['scientific_question_resolved'] is False
    assert status['campaign_status']=='complete_at_prespecified_stop_before_protected_prefixes'
    ledger=[json.loads(line) for line in (C/'protocols/EXPOSURE.jsonl').read_text().splitlines()]
    allowed=set(read(C/'protocols/FIT_FREEZE.json')['fit_subjects']+read(C/'protocols/FIT_FREEZE.json')['comparison_subjects'])
    for event in ledger:
        if event.get('event')=='reuse_consumed_source':
            assert event['subject'] in allowed and 0<event['cap']<=4000
        assert not str(event.get('subject','')).startswith('fip_')
    out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),passed=True,
        no_trial_arrays_decoded=True,freeze_file_counts=counts,
        historical_metadata_and_ledger_pins_pass=True,
        comparison_forecast_hashes=len(comparison['forecast_records']),fit_grid_forecast_hashes=grid_files,
        control_original_log_manifest_mismatch_preserved=differences,
        control_postexecution_log_record_verified=True,
        source_readiness_passed=False,decision_controls_passed=False,
        independent_result_audit_passed=True,external_prefixes=0,external_futures=0,
        scientific_question_resolved=False,scientific_branch_stopped=True,
        status_sha256=sha(C/'protocols/VALIDATION_STATUS.json'))
    (C/'protocols/PROVENANCE_CHECKS.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':run()

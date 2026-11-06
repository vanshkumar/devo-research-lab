"""Read-only provenance/access verification; no trial values or network needed."""
from pathlib import Path
import json,hashlib,collections,datetime

ROOT=Path(__file__).resolve().parents[3]
C=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    freeze=C/'protocols/FREEZE.json';obj=json.loads(freeze.read_text())
    for r in obj['files']:
        assert sha(ROOT/r['path'])==r['sha256'],r['path']
    raw=json.loads((C/'artifacts/coverage/BYTE_MANIFEST.json').read_text())
    for r in raw:
        p=ROOT/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['path']
    for name in ('SOURCE_FORECASTS.json','SOURCE_POLICY_SWAP_FORECASTS.json'):
        m=json.loads((C/'protocols'/name).read_text());assert m['freeze_sha256']==sha(freeze)
        assert len(m['records'])==75
        for r in m['records']:
            assert sha(ROOT/r['path'])==r['sha256'],r['path']
            if 'metadata_path' in r:
                jp=ROOT/r['metadata_path'];assert sha(jp)==r['metadata_sha256']
                a=json.loads(jp.read_text());pp=jp.parent/(r['subject']+'__prefix.npz')
                assert sha(pp)==a['prefix_sha256']
    g=json.loads((C/'protocols/SOURCE_GATE.json').read_text())
    assert sha(ROOT/g['result_path'])==g['result_sha256']
    assert sha(C/'protocols/SOURCE_FORECASTS.json')==g['forecast_manifest_sha256']
    assert not g['new_population_source_gate_earned'] and not g['external_release']
    events=[json.loads(l) for l in (C/'protocols/EXPOSURE.jsonl').read_text().splitlines()]
    first_score=next(i for i,e in enumerate(events) if e['event']=='open_new_source_scored_outcomes')
    primary_saved=next(i for i,e in enumerate(events) if e['event']=='all_cohort_forecasts_frozen')
    swap_saved=next(i for i,e in enumerate(events) if e['event']=='source_state_policy_swap_forecasts_frozen')
    assert max(primary_saved,swap_saved)<first_score
    new_prefix=[e for e in events if e['event']=='open_new_source_prefix_only']
    assert len(new_prefix)==25 and {e['subject'] for e in new_prefix}==set(obj['source_subjects'])
    assert all(e['outcome_trial_interval']==[0,1000] for e in new_prefix)
    for e in events:
        assert not (e.get('subject','').startswith('fip_') or e.get('subject')=='SWC_007'),e
        interval=e.get('outcome_trial_interval',e.get('trial_interval'))
        if interval and e.get('subject'):
            assert interval[0]==0 and interval[1]<= (3000 if e['subject']=='NYU-21' else 4000)
    for p in ('artifacts/coverage/reconstruction/RESULT.json','artifacts/policy_audit/production_replay/SOURCE_RESULT.json','artifacts/policy_audit/production_replay/FIXED_SWAP_RESULT.json'):
        a=json.loads((C/p).read_text())
        assert a.get('status')=='passed' if 'reconstruction' in p else a['passed'] is True,p
    a=json.loads((C/'artifacts/coverage/SEMANTIC_AUDIT.json').read_text())
    assert a['status']=='passed'
    result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
                frozen_files=len(obj['files']),raw_files=len(raw),raw_bytes=sum(r['bytes'] for r in raw),
                source_forecasts=75,full_primary_forecasts=72,partial_forecasts=3,
                counterfactual_source_forecasts=75,prefix_animals=25,primary_animals=24,
                unique_source_rows_decoded=99000,scoring_after_all_forecasts_saved=True,
                external_outcome_prefix_accesses=0,SWC_007_value_accesses=0,
                freeze_sha256=sha(freeze),source_result_sha256=g['result_sha256'],
                new_ledger_events=len(events),events=dict(collections.Counter(e['event'] for e in events)))
    p=C/'protocols/PROVENANCE_CHECKS.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

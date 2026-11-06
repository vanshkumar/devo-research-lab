"""Finite assignment budget from metadata and ZIP directories only."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
C=ROOT/'campaigns/population_learning_transport_2026-10-28'
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
AUTHOR=ROOT/'lab/tasks/learning-forecast-information-audit-2026-11-01'
HISTORY=ROOT/'experiments/matched_history_diagnostic_2026-10-29'

def main():
    metadata_read=0
    def js(p):
        nonlocal metadata_read
        b=p.read_bytes();metadata_read+=len(b)
        return json.loads(b)
    freeze=js(C/'protocols/FREEZE.json')
    subjects=freeze['source_primary_subjects']
    assert len(subjects)==24 and not set(subjects)&{'NYU-21','SWC_007'}
    sessions=js(C/'artifacts/coverage/SESSIONS.json')
    files={r['path']:r for r in js(C/'artifacts/coverage/FILE_METADATA.json')}
    raw=[]
    for subject in subjects:
        rem=4000
        for s in (s for s in sessions if s['subject']==subject):
            if not rem:break
            take=min(rem,int(s['rows']));rem-=take
            for field,path in s['files'].items():
                m=files[path]
                decoded=int(m['rows'])*len(m['columns'])*16 if field=='table' else int(m['expected_bytes'])
                raw.append(dict(path=path,subject=subject,returned_rows=take,
                                containing_file_bytes=int(m['bytes']),containing_decode_charge=decoded))
        assert rem==0
    paths=[]
    for s in subjects:
        for suffix in ('__prefix.npz','__rnn.npz','__observed.npz'):
            paths.append(C/'artifacts/forecasts/source'/(s+suffix))
        paths.append(HISTORY/(s+'__conditional.npz'))
        paths.append(C/'artifacts/forecasts/source'/(s+'__rnn.json'))
    paths += [AUTHOR/'MATCHED_PREDICTIONS.npz',AUTHOR/'UNCERTAINTY_DRAWS.npz',
              OLD/'artifacts/rnn/rnnglm32_nested_best.npz',OLD/'artifacts/baselines/nested_growth_bank.npz',
              HISTORY/'SOURCE_PINS.json',AUTHOR/'PREDICTION_MANIFEST.json',AUTHOR/'RESULT.json']
    # Fixed representative files, selected by position in the original frozen identity list.
    selected=[subjects[0],subjects[-1]]
    paths += [AUTHOR/'predictions'/(s+'.npz') for s in selected]
    assets=[]
    directory_allowance=0
    for p in paths:
        size=p.stat().st_size
        if p.suffix=='.npz':
            with zipfile.ZipFile(p) as z:decoded=sum(q.file_size for q in z.infolist())
            # Charge an entire containing compressed asset even for directory inspection.
            directory_allowance+=size
        else:decoded=size
        assets.append(dict(path=str(p.relative_to(ROOT)),bytes=size,decode_charge=decoded))
    first=js(OUT/'FIRST_CALCULATION.json')['resources']['conservative_cumulative_read_charge_bytes']
    strict=2*sum(int(r['bytes']) for r in freeze['files'])
    repeated=48*(C/'artifacts/coverage/SESSIONS.json').stat().st_size
    repeated+=24*((C/'protocols/FREEZE.json').stat().st_size+(C/'protocols/SOURCE_FORECASTS.json').stat().st_size)
    rawcharge=sum(r['containing_file_bytes']+r['containing_decode_charge'] for r in raw)
    assetcharge=sum(a['bytes']+a['decode_charge'] for a in assets)
    total=first+metadata_read+directory_allowance+strict+repeated+rawcharge+assetcharge+45_000_000
    assert total<350_000_000,total
    plan=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),subjects=subjects,
              saved_full_trial_file_checks=selected,raw_containing_assets=raw,scientific_artifacts=assets,
              first_calculation_charge=first,plan_metadata_read=metadata_read,
              conservative_zip_directory_inspection_charge=directory_allowance,
              two_complete_freeze_hash_passes=strict,repeated_reader_metadata_charge=repeated,
              raw_containing_read_decode_charge=rawcharge,artifact_read_hash_decode_charge=assetcharge,
              context_code_runtime_output_closeout_allowance=45_000_000,
              conservative_total_charge_bytes=total,cap_bytes=350_000_000,
              peak_rss_cap_bytes=800_000_000,expected_peak_rss_bytes=450_000_000,
              processes=1,numerical_threads=1,public_operations=0,ingress_bytes=0,
              physical_io_internal_parquet_decode_unknown=True,
              first_native_exit=0,first_native_output='12:30:05.092235Z; gap6.350495115134546pp; 34378opportunities; RSS39485440; read12835045bytes')
    (OUT/'RESOURCE_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k not in ('raw_containing_assets','scientific_artifacts','subjects')},indent=2),flush=True)

if __name__=='__main__':main()

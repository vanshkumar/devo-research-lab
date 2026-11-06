"""Charge the preserved failed compiler pass using saved inventory; no raw reads."""
from pathlib import Path
import datetime as dt
import hashlib
import json

O=Path(__file__).resolve().parent
R=O.parents[2]
def main():
    b=(O/'ORIGINAL_RESOURCE_PLAN.json').read_bytes();plan=json.loads(b)
    first=plan['subjects'][0]
    required=['experiments/matched_history_diagnostic_2026-10-29/SOURCE_PINS.json',
              'lab/tasks/learning-forecast-information-audit-2026-11-01/MATCHED_PREDICTIONS.npz',
              'lab/tasks/learning-forecast-information-audit-2026-11-01/PREDICTION_MANIFEST.json',
              'campaigns/learning_rule_transport_2026-10-28/artifacts/rnn/rnnglm32_nested_best.npz',
              'campaigns/learning_rule_transport_2026-10-28/artifacts/baselines/nested_growth_bank.npz']
    required += ['campaigns/population_learning_transport_2026-10-28/artifacts/forecasts/source/'+first+s
                 for s in ('__prefix.npz','__rnn.npz','__observed.npz','__rnn.json')]
    required += ['experiments/matched_history_diagnostic_2026-10-29/'+first+'__conditional.npz']
    inventory={a['path']:a for a in plan['scientific_artifacts']}
    artifact=sum(inventory[p]['bytes']+inventory[p]['decode_charge'] for p in required)
    raw=sum(a['containing_file_bytes']+a['containing_decode_charge'] for a in plan['raw_containing_assets'] if a['subject']==first)
    # The failed pass read one strict freeze and first animal's repeated reader metadata.
    freeze=plan['two_complete_freeze_hash_passes']//2
    metadata=plan['repeated_reader_metadata_charge']//24
    allowance=12_000_000
    charge=artifact+raw+freeze+metadata+allowance+len(b)*3
    total=plan['conservative_total_charge_bytes']+charge
    assert total<350_000_000,(total,charge)
    failure=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),native_exit=1,
                 failed_source_sha256=hashlib.sha256((O/'FAILED_FIRST_EXECUTED_review.py').read_bytes()).hexdigest(),
                 cause='Numba rejects float(bool) in independent scalar reference; compilation stopped in first prefix reference',
                 remedy='Explicit 1./0. indicators; inspection also indexes the model three-vector scale by coordinate',
                 last_stage='First subject original prefix sequence evaluated; no autonomous/conditional/contrary comparison completed',
                 complete_artifact_read_decode_charge=artifact,whole_first_subject_raw_containing_charge=raw,
                 strict_freeze_charge=freeze,repeated_reader_metadata_charge=metadata,
                 code_runtime_compile_and_failure_closeout_allowance=allowance,plan_read_allowance=len(b)*3,
                 failed_pass_conservative_charge_bytes=charge,physical_io_unknown=True,
                 failed_peak_rss_bytes=json.loads((O/'FAILED_FIRST_STOP.json').read_text())['peak_rss_bytes'])
    (O/'FAILED_PASS_RESOURCES.json').write_text(json.dumps(failure,indent=2)+'\n')
    plan['original_successful_plan_bytes']=plan['conservative_total_charge_bytes']
    plan['failed_pass_additional_charge_bytes']=charge
    plan['conservative_total_charge_bytes']=total
    plan['amendment_utc']=failure['utc']
    (O/'RESOURCE_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(failure=failure,amended_conservative_total_bytes=total,cap_bytes=350_000_000),indent=2),flush=True)

if __name__=='__main__':main()

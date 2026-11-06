"""Run only after recovery/model specifications accepted. Does not release outcomes."""
from analysis import *
import datetime

def freeze():
 assert not (ROOT/'protocol/FINAL_FREEZE.json').exists(),'Do not overwrite freeze; use a documented amendment'
 for readout in ['all','stationary']:
  # Recompute development prediction coefficients after restriction correction.
  run('development',readout=readout,save_predictions=True)
  src=ROOT/'outputs'/f'development_Hand_raw_change_{readout}_predictions.json'
  dst=ROOT/'protocol'/f'PREDICTORS_{readout}.json';dst.write_bytes(src.read_bytes())
 preds={}
 for r in ['all','stationary']:
  a=json.loads((ROOT/'outputs'/f'development_Hand_raw_change_{r}.json').read_text());preds[r]=a[FILES[0]]['summary']
 record={'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prediction':'Set A development prior-stationary ±4 clamp halfcontrast transported unchanged in degrees to external Figure3 NoJump versus JumpTo index at nonzero±4 clamp. No refitting of substantive interaction. External nuisance fits estimate the independently observed contrast only.','predictions':preds,'external_outcomes_inspected':False}
 (ROOT/'protocol/TRANSFER_PREDICTION.json').write_text(json.dumps(record,indent=2)+'\n')
 paths=list((ROOT/'experiments').glob('*.py'))+list((ROOT/'audits').rglob('*.py'))+[ROOT/'requirements.txt',ROOT/'audits/state_models/DESIGN.md',ROOT/'audits/state_models/GLS_REPAIR_DESIGN.md',ROOT/'outputs/state_models_frozen_predictions.json',ROOT/'outputs/state_models_fgls_frozen_predictions.json']+[ROOT/'protocol'/f for f in ['split.json','INITIAL_DECISIONS.md','AMENDMENTS.md','ANALYSIS_PROTOCOL.md','PREDICTORS_all.json','PREDICTORS_stationary.json','TRANSFER_PREDICTION.json']]
 hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
 rec={'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exposure':'Primary development20 consumed; primary validation20 and externalFigure3/4 outcomes sealed. Published aggregates known.','files_sha256':hashes}
 path=ROOT/'protocol/FINAL_FREEZE.json';assert not path.exists(),'Do not overwrite freeze; use a documented amendment'
 path.write_text(json.dumps(rec,indent=2)+'\n');print('Freeze saved',rec['frozen_utc'])
if __name__=='__main__':freeze()

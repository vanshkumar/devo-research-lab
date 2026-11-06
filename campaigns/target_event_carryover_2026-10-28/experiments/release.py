"""Explicit, single-use outcome-exposure ledger after verification of the freeze."""
from analysis import ROOT,hashlib,json
import datetime,sys
kind=sys.argv[1].upper();assert kind in ['VALIDATION','TRANSFER']
path=ROOT/'protocol'/f'{kind}_RELEASE.json';assert not path.exists(),'Release already recorded; repeat analyses are reproductions, not fresh validation.'
fp=ROOT/'protocol/FINAL_FREEZE.json';f=json.loads(fp.read_text())
for p,h in f['files_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
r={'released_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':kind,'freeze_sha256':hashlib.sha256(fp.read_bytes()).hexdigest(),'frozen_files_verified':len(f['files_sha256']),'exposure_before_release':'No raw outcomes from this reserved population examined; input schedules, published aggregates and synthetic recovery known.','authorized_scope':'20 reserved primary people' if kind=='VALIDATION' else '18 Figure3 independent-laboratory people only; Figure4 and optional210-person source remain sealed.'}
path.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

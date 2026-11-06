"""Finite task accounting from saved sizes; no outcome reads."""
from pathlib import Path
import json,zipfile,hashlib,datetime,sys
OUT=Path(__file__).resolve().parent
p=OUT/'consumed_inputs.npz'
with zipfile.ZipFile(p) as z:decoded=sum(v.file_size for v in z.infolist())
one=p.stat().st_size+decoded
failed=OUT/'corrected/controls.stdout'
dest=OUT/'corrected/failed_controls_summary.stdout'
if failed.exists() and not dest.exists():dest.write_bytes(failed.read_bytes())
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),consumed_npz_compressed_bytes=p.stat().st_size,
       consumed_npz_full_npy_decoded_bytes=decoded,charge_each_full_load_bytes=one,
       consumed_npz_full_loads_so_far=4,anticipated_controls_restart_loads=1,
       fixed_prior_certification_build_and_failed_sample_charge_bytes=160000000,
       anticipated_total_before_independent_audit_bytes=160000000+5*one,
       cap_bytes=750000000,
       current_explicit_code_sha256=hashlib.sha256((OUT/'analysis_explicit.py').read_bytes()).hexdigest())
(OUT/'RESOURCE_SNAPSHOT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

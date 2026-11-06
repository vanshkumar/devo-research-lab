"""Pin public evidence, analysis code and semantic network caches after review."""
from pathlib import Path
import hashlib,json,sys,platform,subprocess,os
BASE=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(BASE/'outputs/.mplconfig'))
Path(os.environ['MPLCONFIGDIR']).mkdir(parents=True,exist_ok=True)
import numpy as np,scipy,matplotlib,pandas,PIL
PDF_PYTHON=Path('/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3')
def digest(b):return hashlib.sha256(b).hexdigest()
def model_fingerprint(path):
    if path.suffix=='.json':
        d=json.loads(path.read_text());d.pop('elapsed_seconds',None)
        return {'type':'json_without_execution_time','sha256':digest(json.dumps(d,sort_keys=True).encode())}
    with np.load(path) as d:
        return {'type':'numpy_arrays','arrays':{k:{'shape':list(d[k].shape),'dtype':str(d[k].dtype),'sha256':digest(d[k].tobytes())} for k in sorted(d.files)}}
def main():
    files=set(p for p in (BASE/'inputs').rglob('*') if p.is_file())
    files.update(BASE.rglob('*.py'));files.update(BASE.rglob('*.cpp'))
    for pat in ['experiments/*PROTOCOL.md','experiments/*PLAN.md','audits/**/EXTRACTION_PLAN.md','audits/model_audit/PRE_SPEC.md','audits/prior_work/COOLING_EXTRACTION_PLAN.md']:
        files.update(BASE.glob(pat))
    for name in ['requirements-lock.txt','audits/prior_work/zhao_table_independent.json']:
        files.add(BASE/name)
    rec=[{'path':str(p.relative_to(BASE)),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(files)]
    (BASE/'INPUTS.json').write_text(json.dumps({'date':'2026-10-28','meaning':'public source snapshots, acquisition metadata, frozen choices and runnable code; includes retained failed responses honestly identified in source manifests','files':rec},indent=2)+'\n')
    cached={str(p.relative_to(BASE)):model_fingerprint(p) for p in sorted((BASE/'outputs/hvc').glob('*_seed*_period*_steps*')) if p.suffix in ['.json','.npz']}
    (BASE/'CACHED_MODELS.json').write_text(json.dumps({'meaning':'semantic outputs of executed source/stress/pilot networks; timing telemetry and ZIP metadata excluded','models':cached},indent=2)+'\n')
    pdf=json.loads(subprocess.check_output([str(PDF_PYTHON),'-c','import json,sys,pdfplumber,pypdf; print(json.dumps(dict(python=sys.version,pdfplumber=pdfplumber.__version__,pypdf=pypdf.__version__)))']).decode())
    env={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
      'packages':{'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pandas.__version__,'matplotlib':matplotlib.__version__,'pillow':PIL.__version__},
      'pdf_runtime':str(PDF_PYTHON),'pdf_packages':pdf,'compiler':subprocess.check_output(['clang++','--version']).decode(),
      'full_network_run_limit':'two concurrent local processes; longest working arrays~245MB per process plus small temporaries; no fast-math or BLAS in network kernel'}
    (BASE/'ENVIRONMENT.json').write_text(json.dumps(env,indent=2)+'\n')
    prior=BASE/'inputs/prior_work'
    zipm=json.loads((prior/'mackevicius_range_manifest.json').read_text());tm=json.loads((prior/'trialtimes_manifest.json').read_text())
    resource={'zhao_retained_public_responses':json.loads((BASE/'inputs/zhao/MANIFEST.json').read_text())['retained_download_bytes_excluding_derived_text'],
      'tanaka_public_html':203915,'roberts_retained_public_resources':7080029,
      'prior_code_zip_capped_attempt':zipm['initial_capped_attempt_bytes'],
      'prior_code_ranges':sum(x['bytes'] for x in zipm['ranges']),
      'trialtimes_ranges':sum(x['bytes'] for x in tm['ranges']),
      'peer_review_pdf':753729,'long_fee_proof_pdf':1340302}
    resource['counted_bytes_subtotal']=sum(resource.values())
    resource['additional_transfer_limit']='prior auditor failed Roberts PDF acquisition at most6,000,001bytes, exact not retained; browser/search metadata and transport overhead unmetered. Subtotal is not total network usage.'
    resource['model_compute_child_process_seconds']=json.loads((BASE/'outputs/hvc/SUMMARY.json').read_text())['elapsed_sum_child_process_seconds']
    (BASE/'RESOURCE_ACCOUNTING.json').write_text(json.dumps(resource,indent=2)+'\n')
    print('Pinned',len(rec),'evidence/code files and',len(cached),'semantic network cache files')
if __name__=='__main__':main()

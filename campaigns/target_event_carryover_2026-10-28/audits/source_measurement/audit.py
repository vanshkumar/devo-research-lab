"""Independent source audit. Only frozen primary DEVELOPMENT outcomes are read.

All external outcomes and reserved primary outcomes are discarded at ingestion.
No target-effect or learning statistic is estimated. Re-run from repository root.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'sources/learning_intervention_feasibility_2026-10-28'
SPLIT = json.loads((HERE.parents[1] / 'protocol/split.json').read_text())['split']

def number(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return float('nan')

def maxabs(a):
    good = np.isfinite(a)
    return float(np.max(np.abs(a[good]))) if good.any() else None

def gitblob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

out = {'scope': 'Primary development-only transformation checks; all external input-only; no empirical target effects.',
       'split_sha256': hashlib.sha256((HERE.parents[1] / 'protocol/split.json').read_bytes()).hexdigest(),
       'development_transformations': [], 'inputs': [], 'code_integrity': [],
       'source_integrity': [], 'development_cross_person_differences': []}
manifest=json.loads((SOURCE/'source_manifest.json').read_text())
for item in manifest['files']:
    if item['local']=='tsay_parajump.csv':
        continue
    b=(SOURCE/item['local']).read_bytes()
    assert gitblob(b)==item['expected_git_blob']
    out['source_integrity'].append({'file':item['local'],'sha256':hashlib.sha256(b).hexdigest(),
        'git_blob':gitblob(b),'bytes':len(b),'url':item['url']})
inventory = json.loads((HERE / 'repository_inventory.json').read_text())
expected = {Path(i['path']).name:i for items in inventory.values() for i in items if i['type']=='file'}
expected['tsay_notebook.html'] = expected['TargetJump_5Feb2022.nb.html']
for p in sorted((HERE/'code').iterdir()):
    b = p.read_bytes()
    item = expected[p.name]
    assert gitblob(b) == item['sha'], p.name
    out['code_integrity'].append({'local': str(p.relative_to(HERE)), 'git_blob':gitblob(b),
       'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'url':item['download_url']})

input_fields = {'SN','TN','clamp_size','tgt_jump_size','Exp','Subject','TrialNum',
                'ClampAngle','TargetJump','TrialLabel','TgtSize','TgtAngle','TrialType','ClampApplied'}
for fn in ['tsay_TE_SPE.csv','tsay_controljump.csv','task_success_fig3.csv','task_success_fig4.csv']:
    inputs=[]
    dev=[]
    with (SOURCE/fn).open() as f:
        reader=csv.DictReader(f)
        columns=reader.fieldnames
        for r in reader:
            inputs.append({k:v for k,v in r.items() if k in input_fields})
            # This guard occurs before any outcome is copied or parsed.
            if fn in SPLIT and r['SN'] in SPLIT[fn]['development']:
                dev.append({k:number(r[k]) for k in ['SN','TN','Hand','Hand_raw','Hand_dt','Hand_Diff']})
    if fn in SPLIT:
        devkeys={(int(r['SN']),int(r['TN'])):r for r in dev}
        for sn in map(int,SPLIT[fn]['development']):
            if (sn+1,1) in devkeys:
                residual=devkeys[sn,824]['Hand_Diff']-(devkeys[sn+1,1]['Hand_dt']-devkeys[sn,824]['Hand_dt'])
                out['development_cross_person_differences'].append({'file':fn,'from_SN':sn,'to_SN':sn+1,
                    'Hand_Diff_at_TN824_minus_cross_person_dt_difference':residual})
        core=[r for r in inputs if int(r['TN'])>100]
        cells=Counter((r['clamp_size'],r['tgt_jump_size']) for r in core)
        out['inputs'].append({'file':fn,'columns':columns,'cells':[{'clamp':k[0],'jump':k[1],'n':v} for k,v in sorted(cells.items())]})
        for sn in SPLIT[fn]['development']:
            rows=sorted([r for r in dev if r['SN']==int(sn)],key=lambda r:r['TN'])
            a={k:np.array([r[k] for r in rows]) for k in rows[0]}
            assert np.all(np.diff(a['TN'])==1)
            raw=a['Hand_raw']; h=a['Hand']; dt=a['Hand_dt']; dif=a['Hand_Diff']
            offset=raw-dt
            good=np.isfinite(offset)
            x=a['TN'][good]; y=offset[good]
            slope=np.sum((x-x.mean())*(y-y.mean()))/np.sum((x-x.mean())**2)
            intercept=y.mean()-slope*x.mean()
            expected_diff=np.r_[np.diff(dt),np.nan]
            boxcars=[]
            for win in [3,5,7,9,11,21,51,101]:
                half=win//2
                pred=np.array([np.mean(raw[i-half:i+half+1]) for i in range(half,len(raw)-half)])
                err=pred-offset[half:len(raw)-half]
                boxcars.append({'window':win,'interior_rmse':float(np.sqrt(np.nanmean(err**2))), 'interior_max_error':maxabs(err)})
            out['development_transformations'].append({
                'file':fn,'SN':sn,'rows':len(rows),
                'missing':{k:int(np.sum(~np.isfinite(a[k]))) for k in ['Hand','Hand_raw','Hand_dt','Hand_Diff']},
                'Hand_minus_Hand_raw_max_abs':maxabs(h-raw),
                'Hand_and_Hand_dt_masks_equal':bool(np.array_equal(np.isnan(h),np.isnan(dt))),
                'Hand_Diff_minus_next_Hand_dt_minus_current_max_abs':maxabs(dif-expected_diff),
                'Hand_Diff_mask_equals_adjacent_Hand_dt_mask':bool(np.array_equal(np.isnan(dif),np.isnan(expected_diff))),
                'Hand_Diff_interior_mask_equals_adjacent_Hand_dt_mask':bool(np.array_equal(np.isnan(dif[:-1]),np.isnan(expected_diff[:-1]))),
                'Hand_Diff_finite_at_person_final_trial':bool(np.isfinite(dif[-1])),
                'Hand_dt_mask_differences_TN':a['TN'][np.isnan(h)!=np.isnan(dt)].astype(int).tolist(),
                'Hand_Diff_minus_next_Hand_raw_minus_current_max_abs':maxabs(dif[:-1]-np.diff(raw)),
                'raw_minus_dt_best_linear_residual_max_abs':maxabs(y-(slope*x+intercept)),
                'raw_minus_dt_best_linear_slope':float(slope),
                'boxcar_candidates':boxcars,
                'baseline_raw_mean':float(np.mean(raw[a['TN']<=100])),
                'baseline_raw_median':float(np.median(raw[a['TN']<=100]))
            })
    else:
        last=903 if 'fig3' in fn else 967
        core=[r for r in inputs if 104<=int(r['TrialNum'])<=last]
        cells=Counter((r['ClampAngle'],r['TargetJump'],r.get('TrialLabel',''),r['TgtSize']) for r in core)
        out['inputs'].append({'file':fn,'columns':columns,'cells':[{'clamp':k[0],'jump':k[1],'label':k[2],'size':k[3],'n':v} for k,v in sorted(cells.items())],
            'randomized_zero_clamps':sum(float(r['ClampAngle'])==0 for r in core),
            'fig4_jump_to_is_opposite_raw_clamp':all(float(r['TargetJump'])==-float(r['ClampAngle']) for r in core if r.get('TrialLabel')=='Jump To') if 'fig4' in fn else None})
(HERE/'audit_results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'development_people':len(out['development_transformations']),
    'Hand_equals_raw_where_finite':all(r['Hand_minus_Hand_raw_max_abs']==0 for r in out['development_transformations']),
    'Hand_Diff_matches_dt_max_abs':max(r['Hand_Diff_minus_next_Hand_dt_minus_current_max_abs'] for r in out['development_transformations']),
    'Hand_Diff_mask_algebra_all':all(r['Hand_Diff_mask_equals_adjacent_Hand_dt_mask'] for r in out['development_transformations']),
    'unmasked_raw_all_finite':all(r['missing']['Hand_raw']==0 for r in out['development_transformations']),
    'verified_code_files':len(out['code_integrity'])},indent=2))

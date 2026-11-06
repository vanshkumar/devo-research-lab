"""Development-only source-statistic extraction and recovery-noise calibration.

No validation or external outcomes are copied/parsed. This is an independent
implementation using original source bytes, not the lead's data preparation.
Run from repository root with .venv/bin/python.
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import t as t_dist

HERE=Path(__file__).resolve().parent
CAMPAIGN=HERE.parents[1]
ROOT=HERE.parents[3]
SOURCE=ROOT/'sources/learning_intervention_feasibility_2026-10-28'
OUT=CAMPAIGN/'outputs'
SPLIT_PATH=CAMPAIGN/'protocol/split.json'
SPLIT=json.loads(SPLIT_PATH.read_text())['split']
MISSING={'NA','NaN','nan',''}

def num(s):
    return np.nan if s in MISSING else float(s)

def robust_sd(x):
    x=np.asarray(x);x=x[np.isfinite(x)]
    return float(1.482602218505602*np.median(abs(x-np.median(x))))

def corr(x,y):
    x=np.asarray(x);y=np.asarray(y)
    g=np.isfinite(x)&np.isfinite(y);x=x[g];y=y[g]
    x=x-x.mean();y=y-y.mean()
    return float(np.sum(x*y)/np.sqrt(np.sum(x*x)*np.sum(y*y)))

def trend(x,y):
    x=np.asarray(x);y=np.asarray(y)
    slope=np.sum((x-x.mean())*(y-y.mean()))/np.sum((x-x.mean())**2)
    fitted=y.mean()+slope*(x-x.mean())
    return float(slope),y-fitted

def summary(x):
    x=np.asarray(x,dtype=float);x=x[np.isfinite(x)]
    se=np.std(x,ddof=1)/np.sqrt(len(x))
    delta=t_dist.ppf(.975,len(x)-1)*se
    return {'n_people':len(x),'mean':float(x.mean()),'se':float(se),
            'ci95_low':float(x.mean()-delta),'ci95_high':float(x.mean()+delta),
            'median':float(np.median(x)),'min':float(x.min()),'max':float(x.max())}

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

condition_rows=[];people=[];noise=[];extraction=[]
for filename,s in SPLIT.items():
    subjects={int(sn):[] for sn in s['development']}
    with (SOURCE/filename).open() as f:
        for raw in csv.DictReader(f):
            # Guard before copying/parsing any outcome or missingness.
            sn=int(raw['SN'])
            if sn not in subjects:
                continue
            r={k:num(raw[k]) for k in ['TN','Hand','Hand_raw','Hand_dt','Hand_Diff','clamp_size','tgt_jump_size']}
            r['source_complete']=all(v not in MISSING for v in raw.values())
            subjects[sn].append(r)
    for sn,rows in subjects.items():
        rows.sort(key=lambda r:r['TN'])
        a={k:np.asarray([r[k] for r in rows]) for k in rows[0]}
        tn=a['TN'].astype(int)
        assert len(rows)==824 and np.array_equal(tn,np.arange(1,825))
        y=-a['Hand_raw']
        rebuilt_dt=np.r_[np.diff(a['Hand_dt']),np.nan]
        rebuilt_raw=np.r_[np.diff(a['Hand_raw']),np.nan]
        rebuilt_hand=np.r_[np.diff(a['Hand']),np.nan]
        interior=tn<824
        main=(tn>100)&(((tn-101)%181)<180)
        # A source randomized index must have its response in the same portion.
        main_transition=main&(((tn-101)%181)<179)
        diff_error=a['Hand_Diff'][interior]-rebuilt_dt[interior]
        good=np.isfinite(diff_error)
        extraction.append({'source_file':filename,'SN':sn,'n_interior_pairs':int(good.sum()),
            'max_abs_difference_error':float(np.max(abs(diff_error[good]))),
            'missingness_equal_interior':bool(np.array_equal(np.isnan(a['Hand_Diff'][interior]),np.isnan(rebuilt_dt[interior]))),
            'source_complete_rows':int(a['source_complete'].sum()),
            'source_complete_baseline_rows':int(np.sum(a['source_complete']&(tn<=100))),
            'source_terminal_difference_finite':bool(np.isfinite(a['Hand_Diff'][-1]))})
        scopes={'source_all_complete':a['source_complete'],
                'source_complete_interior':a['source_complete']&interior,
                'randomized_same_portion':main_transition}
        measures={'supplied_Hand_Diff':a['Hand_Diff'],'rebuilt_Hand_dt_difference':rebuilt_dt,
                  'rebuilt_unmasked_raw_difference':rebuilt_raw,'rebuilt_source_masked_Hand_difference':rebuilt_hand}
        cells=sorted(set(zip(a['clamp_size'][main],a['tgt_jump_size'][main])))
        for scope,mask in scopes.items():
            for measure,values in measures.items():
                for clamp,jump in cells:
                    keep=mask&(a['clamp_size']==clamp)&(a['tgt_jump_size']==jump)&np.isfinite(values)
                    condition_rows.append({'source_file':filename,'SN':sn,'scope':scope,'measure':measure,
                        'clamp':clamp,'jump':jump,'n':int(keep.sum()),'median':float(np.median(values[keep])) if keep.any() else np.nan})
        for scope in scopes:
            for measure in measures:
                cc=[r for r in condition_rows if r['source_file']==filename and r['SN']==sn and r['scope']==scope and r['measure']==measure and abs(r['clamp'])==4]
                nojump=[-np.sign(r['clamp'])*r['median'] for r in cc if r['jump']==0]
                jump=[-np.sign(r['clamp'])*r['median'] for r in cc if r['jump']!=0]
                # Equal-weight signed-cell medians, like source aggregation.
                people.append({'source_file':filename,'SN':sn,'scope':scope,'measure':measure,
                    'nojump_compensation':float(np.mean(nojump)),
                    'jump_compensation':float(np.mean(jump)),
                    'jump_minus_nojump':float(np.mean(jump)-np.mean(nojump))})
        baseline=y[tn<=100]
        bas_slope,bas_resid=trend(tn[tn<=100],baseline)
        residual=np.full(len(tn),np.nan);blockmeans=[];blockslopes=[]
        for b in range(4):
            mask=(tn>=101+b*181)&(tn<=280+b*181)
            sl,res=trend(tn[mask],y[mask]);residual[mask]=res
            blockmeans.append(float(np.mean(y[mask])));blockslopes.append(sl)
        pair=main_transition[:-1]
        rawdiff=np.diff(y)[pair]
        noise.append({'source_file':filename,'SN':sn,
            'baseline_level_sd':float(np.std(baseline,ddof=1)),
            'baseline_level_robust_sd':robust_sd(baseline),
            'baseline_detrended_sd':float(np.std(bas_resid,ddof=1)),
            'baseline_detrended_robust_sd':robust_sd(bas_resid),
            'baseline_difference_sd':float(np.std(np.diff(baseline),ddof=1)),
            'baseline_difference_robust_sd':robust_sd(np.diff(baseline)),
            'baseline_difference_robust_sd_over_sqrt2':robust_sd(np.diff(baseline))/np.sqrt(2),
            'baseline_ar1_detrended_correlation':corr(bas_resid[:-1],bas_resid[1:]),
            'baseline_linear_change_over_99_trials':bas_slope*99,
            'main_level_sd':float(np.std(y[main],ddof=1)),
            'main_level_robust_sd':robust_sd(y[main]),
            'main_adjacent_difference_sd':float(np.std(rawdiff,ddof=1)),
            'main_adjacent_difference_robust_sd':robust_sd(rawdiff),
            'main_ar1_raw_correlation':corr(y[:-1][pair],y[1:][pair]),
            'main_ar1_block_detrended_correlation':corr(residual[:-1][pair],residual[1:][pair]),
            'main_block_detrended_sd':float(np.nanstd(residual,ddof=1)),
            'main_block_detrended_robust_sd':robust_sd(residual),
            'main_block_mean_sd':float(np.std(blockmeans,ddof=1)),
            'main_block_mean_range':float(np.ptp(blockmeans)),
            'main_max_abs_linear_change_over_179_trials':float(max(abs(v)*179 for v in blockslopes)),
            'main_rms_linear_change_over_179_trials':float(np.sqrt(np.mean(np.array(blockslopes)**2))*179)})

write_csv(OUT/'source_controls_condition_medians.csv',condition_rows)
write_csv(OUT/'source_controls_people.csv',people)
write_csv(OUT/'source_controls_noise.csv',noise)
write_csv(OUT/'source_controls_extraction.csv',extraction)

group=[]
for filename in SPLIT:
    for scope in ['source_all_complete','source_complete_interior','randomized_same_portion']:
        for measure in ['supplied_Hand_Diff','rebuilt_Hand_dt_difference','rebuilt_unmasked_raw_difference','rebuilt_source_masked_Hand_difference']:
            pp=[r for r in people if r['source_file']==filename and r['scope']==scope and r['measure']==measure]
            group.append({'source_file':filename,'scope':scope,'measure':measure,
               **{k:summary([r[k] for r in pp]) for k in ['nojump_compensation','jump_compensation','jump_minus_nojump']}})
noise_summary={filename:{k:summary([r[k] for r in noise if r['source_file']==filename])
                        for k in noise[0] if k not in ['source_file','SN']} for filename in SPLIT}
out={'scope':'Development only. Published next-trial condition contrasts are extraction controls, not old-input propagation effects.',
     'split_sha256':hashlib.sha256(SPLIT_PATH.read_bytes()).hexdigest(),
     'n_people':len(noise),'group_condition_controls':group,'noise_summary':noise_summary,
     'extraction_max_error_deg':max(r['max_abs_difference_error'] for r in extraction),
     'extraction_masks_all_match_interior':all(r['missingness_equal_interior'] for r in extraction),
     'noise_caveat':'Baseline is veridical-feedback calibration. Main adjacent differences and AR include programmed-input effects, state dynamics and drift; they are descriptive, not pure observation-noise estimates.',
     'external_sign_evidence':{'source':'code/analysis_fig3_tsayrep.Rmd','endpoint_line':72,'difference_line':115,
       'sign_flip_lines':[173,177],'rule':'positive ClampAngle response HandError difference multiplied by -1; use y=-HandError to align primary y=-Hand_raw.'}}
(OUT/'source_controls_summary.json').write_text(json.dumps(out,indent=2)+'\n')
brief=[]
for row in group:
    if row['scope']=='randomized_same_portion' and row['measure'] in ['rebuilt_unmasked_raw_difference','rebuilt_Hand_dt_difference']:
        brief.append(row)
print(json.dumps({'extraction_max_error_deg':out['extraction_max_error_deg'],
   'controls':brief,'noise_summary':{f:{k:v for k,v in q.items() if k in ['baseline_detrended_robust_sd','baseline_ar1_detrended_correlation','main_adjacent_difference_robust_sd','main_ar1_block_detrended_correlation','main_rms_linear_change_over_179_trials']} for f,q in noise_summary.items()}},indent=2))

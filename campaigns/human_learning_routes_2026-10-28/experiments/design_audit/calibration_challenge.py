"""Pre-validation synthetic diagnosis of noisy/regularized calibration.

Reads input schedules and fixed generator definitions only. No empirical
responses are read. All variants see identical simulated task choices; the
independent sensory observations are newly simulated measurement probes.
"""
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse, hashlib, json, sys, time
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'experiments'))
import model, recovery, analysis

VARIANTS = ['association', 'association_z', 'psychometric_z', 'oracle_skill',
            'oracle_skill_wide3', 'independent_200', 'independent_800', 'independent_3200']


def stimulus_basis(contrast):
    out = np.zeros(len(contrast))
    for level, coef in [(.1, .4), (.25, .8), (.5, 1.6), (1., 2.7)]:
        out += np.sign(contrast) * np.isclose(np.abs(contrast), level) * coef
    return out


def psychometric_slopes(features):
    values = {}
    for sid, s in features.rows.groupby('subject'):
        idx = s.index.to_numpy()
        q = stimulus_basis(s.sideContrast.to_numpy())
        previous = features.nuisance[idx, 5]
        X = np.column_stack([np.ones(len(s)), q, features.history[idx], previous])
        y = (s.choice.to_numpy() == 1).astype(float)
        ans = []
        for lo, hi in [(0,100), (100,200)]:
            good = (s.trial.to_numpy() >= lo) & (s.trial.to_numpy() < hi) & s.choice.isin([-1,1]).to_numpy()
            xx, yy = X[good], y[good]
            center = np.array([0., 1., 0., 0., 0., 0.])
            sd = np.array([1.5, 2., 1., 1., 1., 1.])
            def objective(b):
                eta = np.einsum('ij,j->i', xx, b)
                residual = expit(eta)-yy
                value = np.sum(np.logaddexp(0,eta)-yy*eta)+.5*np.sum(((b-center)/sd)**2)
                gradient = np.einsum('ij,i->j',xx,residual)+(b-center)/sd**2
                return value,gradient
            fit = minimize(objective,center,jac=True,method='BFGS',options={'gtol':1e-7,'maxiter':200})
            assert np.max(np.abs(objective(fit.x)[1])) < 1e-4
            ans.append(float(fit.x[1]))
        values[sid] = ans
    return values


def independent_measurement(subjects, shared_skill, bias, seed, sizes=(200,800,3200)):
    """Idealized fully learned sensory-only task: known lapse, no history.

    Prefixes N200/800/3200 share draws. Estimate bias and sensory scale jointly.
    This is an optimistic information bound, not a proposed literal task model.
    """
    rng = np.random.default_rng(seed+8000000)
    result = {n:{} for n in sizes}
    total=max(sizes)
    for i,row in enumerate(subjects.itertuples()):
        q = rng.choice([-2.7,-1.6,-.8,-.4,.4,.8,1.6,2.7],total)
        lapse = .07-.04*(row.instructions-.5)
        scale = np.clip(1+.22*shared_skill[i],.3,1.8)
        truep = lapse/2+(1-lapse)*expit(bias[i]+q*scale)
        y = (rng.random(total)<truep).astype(float)
        for n in result:
            xx=np.column_stack([np.ones(n),q[:n]]); yy=y[:n]
            prior=np.array([0.,1.]); sd=np.array([1.,.5])
            def objective(b):
                eta=np.einsum('ij,j->i',xx,b); sig=expit(eta)
                p=lapse/2+(1-lapse)*sig
                value=-np.sum(yy*np.log(p)+(1-yy)*np.log1p(-p))+.5*np.sum(((b-prior)/sd)**2)
                r=(p-yy)/(p*(1-p))*(1-lapse)*sig*(1-sig)
                grad=np.einsum('ij,i->j',xx,r)+(b-prior)/sd**2
                return value,grad
            fit=minimize(objective,prior,jac=True,method='BFGS',options={'gtol':1e-7,'maxiter':200})
            assert np.max(np.abs(objective(fit.x)[1])) < 1e-3
            result[n][row.subject]=[(float(fit.x[1])-1)/.22,0.]
    return result


def replace_calibration(features, mapping, center=None, scale=None):
    raw=features.calibration_raw.copy()
    for i,row in raw.iterrows():
        raw.loc[i,list(model.CALIBRATION_NAMES[:2])]=mapping[row.subject]
    vals=raw[list(model.CALIBRATION_NAMES)].to_numpy(float)
    if center is None: center=vals.mean(axis=0)
    if scale is None: scale=np.ones(4)
    transform=dict(features.calibration_transform,center=np.asarray(center).tolist(),scale=np.asarray(scale).tolist())
    indexed=raw.set_index('subject')
    cal=(indexed.loc[features.rows.subject,list(model.CALIBRATION_NAMES)].to_numpy()-center)/scale
    return replace(features,calibration=cal,calibration_raw=raw,calibration_transform=transform)


def one_job(scenario, rep, scales, variants):
    started=time.monotonic();inputs,_=recovery.load_inputs()
    scenario_index=list(recovery.SCENARIOS).index(scenario)
    # Independent seeds from main recovery; the first latent draw is pinned.
    seed=302610280+10000*scenario_index+rep
    frame,truth=recovery.simulate(inputs,scenario,seed,scales[scenario])
    subjects=inputs[['subject','instructions','partition']].drop_duplicates()
    rng=np.random.default_rng(seed);u=rng.normal(0,.55,len(subjects));g=subjects.instructions.to_numpy()-.5
    shared_skill=u+(.23/.22)*g
    bias=.2*g+rng.normal(0,.35,len(subjects))
    skill_map=dict(zip(subjects.subject,shared_skill))
    dev=frame[frame.partition.eq('development')];val=frame[~frame.partition.eq('development')]
    df=model.prepare_features(dev);vf=model.prepare_features(val,df.calibration_transform)
    raw=pd.concat([df.calibration_raw,vf.calibration_raw])
    associations={row.subject:[row.sensory_first100,row.sensory_second100] for row in raw.itertuples()}
    psych={}
    if 'psychometric_z' in variants: psych={**psychometric_slopes(df),**psychometric_slopes(vf)}
    independent={}
    if any(v.startswith('independent_') for v in variants): independent=independent_measurement(subjects,shared_skill,bias,seed)
    rows=[]
    for variant in variants:
        if variant.startswith('association'): mapping=associations
        elif variant=='psychometric_z': mapping=psych
        elif variant.startswith('oracle'): mapping={s:[v,0.] for s,v in skill_map.items()}
        else: mapping=independent[int(variant.split('_')[1])]
        nf=replace_calibration(df,mapping)
        scale=np.ones(4)
        if variant.endswith('_z'):
            scale[:2]=np.maximum(nf.calibration_raw[list(model.CALIBRATION_NAMES[:2])].std(ddof=1).to_numpy(),.05)
            nf=replace_calibration(df,mapping,scale=scale)
        nv=replace_calibration(vf,mapping,np.asarray(nf.calibration_transform['center']),scale)
        # Source participants in the transform must remain training only.
        nv=replace(nv,calibration_transform=nf.calibration_transform)
        cfg=model.ModelConfig(condition_history_sd=3. if variant.endswith('wide3') else 1.)
        fits={v:model.fit_model(nf,v,config=cfg) for v in ['shared','condition']}
        w=analysis.windows(nv.rows)
        delta=model.log_score(model.predict_model(fits['condition'],nv),nv.y)-model.log_score(model.predict_model(fits['shared'],nv),nv.y)
        score=w[['subject','instructions','partition']].copy();score['delta_log']=delta
        score=score[w.primary_responded].groupby(['subject','instructions','partition']).delta_log.mean().reset_index().rename(columns={'instructions':'condition'})
        lo,hi=recovery.score_ci(score,np.random.default_rng(seed+9000000),reps=2000)
        effect,_=analysis.standardized_effect(fits['condition'],nv)
        # C-to-skill measurement association, pooled across same80 people.
        measure=np.array([mapping[s][1] if variant in ['association','association_z','psychometric_z'] else mapping[s][0] for s in subjects.subject])
        rows.append(dict(scenario=scenario,replicate=rep,seed=seed,variant=variant,
                         truth_effect=truth['mean'],effect=effect['mean'],effect_bias=effect['mean']-truth['mean'],
                         delta_log=float(score.delta_log.mean()),score_low=lo,score_high=hi,score_detect=lo>0,
                         max_gradient=max(x.diagnostics['max_abs_gradient'] for x in fits.values()),
                         converged=all(x.diagnostics['success'] for x in fits.values()),
                         skill_correlation=float(np.corrcoef(measure,shared_skill)[0,1]),
                         seconds=time.monotonic()-started))
    return rows


def summarize(d):
    return d.groupby(['scenario','variant']).agg(reps=('replicate','size'),truth=('truth_effect','mean'),
        effect=('effect','mean'),bias=('effect_bias','mean'),effect_sd=('effect','std'),
        score_gain=('delta_log','mean'),score_detection=('score_detect','mean'),
        skill_correlation=('skill_correlation','mean'),all_converged=('converged','all')).reset_index()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reps',type=int,default=30);parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--label',default='calibration_challenge');parser.add_argument('--variants',nargs='+',default=VARIANTS)
    parser.add_argument('--scenarios',nargs='+',default=['carryover_null','slow_05','slow_minus05']);args=parser.parse_args()
    out=Path(__file__).parent/args.label;out.mkdir(exist_ok=True)
    assert not (out/'replicates.csv').exists(), 'Choose a new label to preserve the existing experiment'
    definitions=json.loads((ROOT/'outputs/recovery/final/scenario_definitions.json').read_text())
    scales={s:definitions[s]['scale'] for s in args.scenarios}
    manifest=dict(args=vars(args),scales=scales,variants=VARIANTS,scope='simulated choices only; no empirical outcome access',
        independent_measurement='Idealized fully learned sensory-only logistic mixture, known lapse, estimated bias; no history, equal contrast allocation. Optimistic measurement-information diagnostic.',
        seed_rule='302610280+10000*scenario_index+replicate',
        hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['experiments/model.py','experiments/recovery.py','outputs/recovery/final/scenario_definitions.json']})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows=[]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        jobs=[executor.submit(one_job,s,rep,scales,args.variants) for rep in range(args.reps) for s in args.scenarios]
        for future in as_completed(jobs):
            result=future.result();rows.extend(result);d=pd.DataFrame(rows)
            d.to_csv(out/'replicates.csv',index=False);summarize(d).to_csv(out/'summary.csv',index=False)
            print(json.dumps(dict(scenario=result[0]['scenario'],rep=result[0]['replicate'],variants=len(result),seconds=round(result[-1]['seconds'],1))),flush=True)
    print(summarize(pd.DataFrame(rows)).to_string(index=False),flush=True)


if __name__=='__main__':main()

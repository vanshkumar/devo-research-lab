#!/usr/bin/env python3
"""Pre-exposure gate calibration on consumed source outcomes only.

Never imports a source loader or opens a new-source/external file. All writes
are to the new campaign's method_audit directory. Statistical controls concern
the selected animal mixture, not uncertainty over arbitrary new laboratories.
"""
from pathlib import Path
import argparse, hashlib, json, os, sys, time

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / 'campaigns/learning_rule_transport_2026-10-28'
OUT = Path(__file__).resolve().parents[1] / 'artifacts/method_audit'
OUT.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
os.environ['NUMBA_CACHE_DIR'] = str(OUT / 'numba_cache')
sys.path.insert(0, str(OLD / 'code'))
import numpy as np
from scipy.stats import t as student_t
from scipy.stats import beta as beta_dist
from rnn_learning import load_rnn
from rnn_rollout import calibration_particles
from baselines import draw_initial, competence_at, omission_at, load_bank
from trainer import VectorTrainer
from run_forecasts import seed_for


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SavedCalibration:
    def __init__(self, model, calibration):
        self.model, self.cal, self.hidden = model, calibration, model.hidden

    def initial_state(self, prefix, method):
        return dict(w=np.array(self.cal['endpoint']),
                    h=np.array(self.cal['hidden_endpoint']),
                    w0=np.array(self.cal['w0']))

    def sequence(self, *args, **kwargs):
        return self.model.sequence(*args, **kwargs)


def exact_target(signed, choices):
    signed, choices = np.atleast_2d(signed), np.atleast_2d(choices)
    m = len(signed)
    values, counts = np.empty((m, 6)), np.empty((m, 6, 2), int)
    for b in range(6):
        x, c = signed[:, b*500:(b+1)*500], choices[:, b*500:(b+1)*500]
        side_values = []
        for j, side in enumerate((-1., 1.)):
            mask = np.isclose(x, side, atol=1e-12, rtol=0)
            den = mask.sum(1)
            side_values.append(np.divide((mask & (c == -side)).sum(1), den,
                out=np.full(m, np.nan), where=den>0))
            counts[:, b, j] = den
        values[:, b] = np.mean(side_values, axis=0)
    return values, counts


def source_precision(particles=128):
    order = json.loads((OLD/'artifacts/results/SUBJECT_ORDER.json').read_text())
    allocation = {r['subject']:r for r in json.loads((OLD/'protocols/SPLIT.json').read_text())['standard']}
    modelpath = OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
    bankpath = OLD/'artifacts/baselines/nested_growth_bank.npz'
    model, bank = load_rnn(modelpath), load_bank(bankpath)
    ys, ms, gs, allcounts, labs = [], [], [], [], []
    records = []
    for subject in order:
        start = time.monotonic()
        info = allocation[subject]
        tag = 'rnn_source_animals' if info['split']=='animal_holdout' else 'rnn_source_labs'
        meta = json.loads((OLD/'artifacts/forecasts'/tag/(subject+'__rnnglm32.json')).read_text())
        if meta['model_sha256'] != digest(modelpath):
            raise RuntimeError('Wrong saved source calibration')
        # These 40 animals' whole indexed outcomes are already consumed. We
        # read the archived processed arrays, never a protected new animal.
        p = OLD/'data/processed'/info['split']/(subject+'.npz')
        with np.load(p, allow_pickle=False) as f:
            full = {k:f[k] for k in f.files if k!='metadata_json'}
        prefix = {k:v[:1000] for k,v in full.items()
                  if isinstance(v,np.ndarray) and v.ndim and len(v)==len(full['choice'])}
        s = np.nan_to_num(full['contrastRight'][1000:4000])-np.nan_to_num(full['contrastLeft'][1000:4000])
        observed, count = exact_target(s, full['choice'][1000:4000])
        if not np.isfinite(observed).all():
            raise RuntimeError('Empty consumed source exact100 endpoint; report before continuing')
        starts = full['session_start'][1000:4000]
        seed = seed_for(subject)
        common = draw_initial(prefix, bank, particles, seed+211, exclude=subject, competence='growth')
        initial, _ = calibration_particles(SavedCalibration(model,meta['calibration']),prefix,particles,seed+313)
        saved = {}
        for kind in ('rnn','growth'):
            rng=np.random.default_rng(seed+101)
            state={k:v.copy() for k,v in initial.items()}
            trainer=VectorTrainer.from_prefix(prefix,particles,seed+419,'standard')
            xs=np.empty((particles,3000)); cs=np.empty((particles,3000),np.int8)
            for i in range(3000):
                if starts[i]: trainer.new_session()
                x=trainer.sample()['signed_contrast']
                if kind=='growth': state['w']=competence_at(common,i)
                choice=np.where(rng.random(particles)<model.probs(state,x),-1,1).astype(np.int8)
                choice[rng.random(particles)<omission_at(common,i)]=0
                feedback=trainer.observe(choice)
                if kind=='rnn':
                    model.update(state,x,choice,feedback['feedbackType'],session_start=bool(starts[i]))
                xs[:,i],cs[:,i]=x,choice
            saved[kind], _ = exact_target(xs,cs)
            if not np.isfinite(saved[kind]).all(): raise RuntimeError('Empty simulated side cell')
        ys.append(observed[0]); ms.append(saved['rnn']); gs.append(saved['growth'])
        allcounts.append(count[0]);labs.append(info['lab'])
        records.append(dict(subject=subject,lab=info['lab'],processed_sha256=digest(p),
                            seconds=time.monotonic()-start))
        print(json.dumps(records[-1]),flush=True)
    y,m,g=np.asarray(ys),np.asarray(ms),np.asarray(gs)
    np.savez_compressed(OUT/'CONSUMED_SOURCE_EXACT100.npz',subject=np.array(order),lab=np.array(labs),
                        observed=y,rnn=m,growth=g,counts=np.array(allcounts))
    residual=y-m.mean(1)
    scalar=residual.mean(1)
    summary=dict(scope='Consumed-source exploratory precision only; no new26/external outcomes or prefixes',
        endpoint='equal-side ±100% correct share, omissions failures; opportunities1000:4000; six500bins',
        n=len(y),particles=particles,source_model_sha256=digest(modelpath),bank_sha256=digest(bankpath),
        mean_curves=dict(observed=y.mean(0).tolist(),rnn=m.mean((0,1)).tolist(),growth=g.mean((0,1)).tolist()),
        scalar_residual_sd=float(scalar.std(ddof=1)),mean_bias=float(scalar.mean()),
        residual_covariance=np.cov(residual,rowvar=False).tolist(),
        population_mae=dict(rnn=float(np.abs(residual.mean(0)).mean()),
                            growth=float(np.abs(y.mean(0)-g.mean((0,1))).mean())),
        t_gate_consumed_only=gate(residual,labs),records=records)
    (OUT/'SOURCE_PRECISION.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def gate(error,labs,leave_lab=True,cluster_check=True):
    """The same deterministic gate definition used in repeated controls.

    Error shape animal×six bins. A 90% t CI corresponds to two one-sided5%
    equivalence tests at the fixed±.05 boundary. Lab/curve checks only reduce
    acceptance. Their point tolerances are practical safeguards, not CIs.
    """
    e=np.asarray(error,float); labs=np.asarray(labs)
    if e.ndim!=2 or e.shape[1]!=6 or not np.isfinite(e).all() or len(e)<2:
        return dict(passed=False,reason='nonfinite/insufficient error matrix')
    z=e.mean(1);bias=z.mean();half=student_t.ppf(.95,len(z)-1)*z.std(ddof=1)/np.sqrt(len(z))
    curve=e.mean(0)
    lab_bias={str(l):float(z[labs==l].mean()) for l in np.unique(labs)}
    loo={str(l):float(z[labs!=l].mean()) for l in np.unique(labs) if (labs!=l).sum()}
    groups=np.unique(labs);G=len(groups)
    if G>1:
        lab_sums=np.array([np.sum(z[labs==l]-bias) for l in groups])
        cluster_se=np.sqrt(G/(G-1)*np.sum(lab_sums**2)/len(z)**2)
        cluster_half=student_t.ppf(.95,G-1)*cluster_se
    else:
        cluster_half=np.inf
    checks=dict(scalar_CI_within_5pp=bool(abs(bias)+half<=.05),
        cluster_CI_within_5pp=bool(not cluster_check or abs(bias)+cluster_half<=.05),
        curve_MAE_at_most5pp=bool(np.abs(curve).mean()<=.05),
        maximum_bin_bias_at_most7p5pp=bool(np.abs(curve).max()<=.075),
        every_lab_point_bias_at_most10pp=bool(max(map(abs,lab_bias.values()))<=.10),
        leave_one_lab_out_bias_at_most5pp=bool(not leave_lab or max(map(abs,loo.values()))<=.05))
    return dict(passed=all(checks.values()),bias=float(bias),scalar_CI90=[float(bias-half),float(bias+half)],
        cluster_CI90=[float(bias-cluster_half),float(bias+cluster_half)],
        population_curve_MAE=float(np.abs(curve).mean()),max_bin_bias=float(np.abs(curve).max()),
        lab_bias=lab_bias,leave_one_lab_out_bias=loo,checks=checks)


def repeated_gate(errors,labs,cluster_check=True):
    # Vectorized identical calculations; groups/lab count fixed before outcomes.
    e=np.asarray(errors);labs=np.asarray(labs);z=e.mean(2);bias=z.mean(1)
    half=student_t.ppf(.95,e.shape[1]-1)*z.std(1,ddof=1)/np.sqrt(e.shape[1])
    curve=e.mean(1)
    scalar=(np.abs(bias)+half<=.05)
    accept=scalar&(np.abs(curve).mean(1)<=.05)&(np.abs(curve).max(1)<=.075)
    groups=np.unique(labs);G=len(groups)
    sums=np.stack([np.sum(z[:,labs==lab]-bias[:,None],axis=1) for lab in groups],axis=1)
    cluster_half=student_t.ppf(.95,G-1)*np.sqrt(G/(G-1)*np.sum(sums*sums,axis=1)/e.shape[1]**2)
    cluster_accept=(np.abs(bias)+cluster_half<=.05)
    if cluster_check: accept &= cluster_accept
    for lab in np.unique(labs):
        accept &= (np.abs(z[:,labs==lab].mean(1))<=.10)
        accept &= (np.abs(z[:,labs!=lab].mean(1))<=.05)
    return accept,scalar,bias,half,cluster_accept,cluster_half


def controls(repetitions=20000,counts=(6,2,1,11,6),seed=10282617):
    with np.load(OUT/'CONSUMED_SOURCE_EXACT100.npz',allow_pickle=False) as f:
        residual=f['observed']-f['rnn'].mean(1)
    residual-=residual.mean(0)
    rng=np.random.default_rng(seed);n=sum(counts);labs=np.repeat(np.arange(len(counts)),counts)
    results=[]
    for mode in ('gaussian','empirical','low_variance_known_answer','heterogeneous','lab_shift_fixed','lab_shift_random','stopping_selected'):
        cov=np.cov(residual,rowvar=False)
        if mode=='gaussian':
            e=rng.multivariate_normal(np.zeros(6),cov,size=(repetitions,n))
        else:
            e=residual[rng.integers(len(residual),size=(repetitions,n))]
        # All known true scalar means below are analytical construction means,
        # not sample means that would falsely label random fluctuations bias.
        if mode=='low_variance_known_answer':
            e=e*.25
        elif mode=='heterogeneous':
            mult=np.sqrt(2.5)*np.sqrt(rng.chisquare(2,size=(repetitions,n,1))/2)
            # Independent scale with E(scale²)=2.5; preserve zero mean.
            e=e*mult
        elif mode=='lab_shift_fixed':
            offset=np.array([.10,-.08,.06,-.025,0.])[:len(counts)]
            offset-=np.average(offset,weights=counts)
            e=e+offset[labs,None]
        elif mode=='lab_shift_random':
            shifts=rng.normal(0,.06,size=(repetitions,len(counts)))
            e=e+shifts[:,labs,None]
        elif mode=='stopping_selected':
            # Completion selects higher residual trajectories. Recenter to the
            # selected population target: it must not retain an all-animal mean.
            weights=np.exp(3*residual.mean(1));weights/=weights.sum()
            selected_mean=(weights[:,None]*residual).sum(0)
            e=residual[rng.choice(len(residual),size=(repetitions,n),p=weights)]-selected_mean
        for bias in (0.,.025,.05,.075,.10,.25,-.05,-.075,-.25):
            accept,scalar,b,half,cluster_accept,cluster_half=repeated_gate(e+bias,labs)
            rate=float(accept.mean());mcse=float(np.sqrt(rate*(1-rate)/repetitions))
            k=int(accept.sum())
            upper=float(beta_dist.ppf(.975,k+1,repetitions-k)) if k<repetitions else 1.
            results.append(dict(generator=mode,true_scalar_bias=bias,
                source_gate_acceptance=rate,scalar_gate_acceptance=float(scalar.mean()),
                cluster_gate_acceptance=float(cluster_accept.mean()),
                acceptance_MC_SE=mcse,acceptance_MC_upper95=upper,
                median_halfwidth=float(np.median(half)),repetitions=repetitions,
                median_cluster_halfwidth=float(np.median(cluster_half)),
                interpretation=('arbitrary new-lab shift sensitivity; outside conditional fixed-lab guarantee'
                                if mode=='lab_shift_random' else 'fixed selected animal-mixture calibration')))
    # A zero-scalar but strongly wrong curve must fail max-bin/MAE controls.
    e=residual[rng.integers(len(residual),size=(repetitions,n))]
    for name,change in [('opposite_bin_errors',np.array([.12,.12,.12,-.12,-.12,-.12])),
                        ('policy_mismatch',np.array([.08,.27,.29,.27,.26,.26]))]:
        a,s,_,h,ca,ch=repeated_gate(e+change,labs)
        results.append(dict(generator=name,true_scalar_bias=float(change.mean()),
                            source_gate_acceptance=float(a.mean()),scalar_gate_acceptance=float(s.mean()),
                            cluster_gate_acceptance=float(ca.mean()),
                            repetitions=repetitions))
    within=[r for r in results if abs(r['true_scalar_bias'])>=.05]
    worst=max(within,key=lambda r:r['source_gate_acceptance'])
    result=dict(scope='Controls of fixed gate using consumed-source centered exact100 residual covariance; not learner fit or biological validation',
        seed=seed,source_residual_pool_n=len(residual),counts=list(counts),n=n,
        scalar_interval='90% Student-t on animal scalar errors; ±5pp equivalence at 5% one-sided levels',
        additional_cluster_interval='CR1 cluster sandwich on animal scalar error mean; t(G-1),90%; controls include randomlabshifts',
        gate=dict(curve_MAE=.05,max_bin=.075,lab_point_abs=.10,leave_one_lab_point_abs=.05),
        validity_scope='control-calibrated selected animal mixture with five observed lab clusters; no arbitrary-new-lab or missing-future calibration guarantee',
        worst_material_bias_control=worst,results=results,
        caveats=['Resampling controls cannot certify arbitrary real residual distributions.',
                 'Singleton lab point check is a safeguard on this sample, never an estimate of that lab mean calibration.',
                 'Random shared lab offsets violate the animal-independent target and can inflate false equivalence; report separately.',
                 'Stopping control targets the selected complete-history population; no claim for all started animals.'])
    (OUT/'CONTROLS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2),flush=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--precision',action='store_true');p.add_argument('--controls',action='store_true')
    p.add_argument('--particles',type=int,default=128);p.add_argument('--repetitions',type=int,default=20000)
    p.add_argument('--counts',default='6,2,1,11,6');a=p.parse_args()
    if a.precision: source_precision(a.particles)
    if a.controls: controls(a.repetitions,tuple(map(int,a.counts.split(','))))


if __name__=='__main__':main()

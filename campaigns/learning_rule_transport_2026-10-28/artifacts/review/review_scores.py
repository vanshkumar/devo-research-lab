"""Independent retained-forecast review; never reads raw/external outcomes.

Only saved source curves (future trials 1001--6000) are used. This deliberately
does not import the campaign score/gate implementation or refit any model.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MODELS = ['dnnglm32', 'dnnglm', 'reinforce', 'reinforce_pure', 'growth', 'persistence']
BASELINES = ['growth', 'persistence']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_score(a, y):
    valid = np.isfinite(y)
    assert np.isfinite(a[:, valid]).all()
    n = len(a)
    # Ordered order-statistic expansion of the all-distinct-pair U statistic.
    z = np.sort(a, axis=0)
    c = (2 * np.arange(1, n + 1) - n - 1)[:, None, None]
    cell = np.mean(np.abs(a-y), axis=0) - np.sum(c*z, axis=0)/(n*(n-1))
    by_metric = np.array([cell[:, j][valid[:, j]].mean() for j in range(4)])
    err = np.abs(a.mean(axis=0)-y)
    mae = np.array([err[:, j][valid[:, j]].mean() for j in range(4)])
    lo, hi = np.quantile(a, [.1, .9], axis=0)
    covered = (y >= lo) & (y <= hi)
    cov = np.array([covered[:, j][valid[:, j]].mean() for j in range(4)])
    width = np.array([(hi-lo)[:, j][valid[:, j]].mean() for j in range(4)])
    return dict(crps=float(by_metric.mean()), crps_by_metric=by_metric.tolist(),
                high_accuracy_mae=float(mae[:2].mean()), mae_by_metric=mae.tolist(),
                coverage80=float(covered[valid].mean()), coverage80_by_metric=cov.tolist(),
                high_coverage80=float(covered[:, :2][valid[:, :2]].mean()),
                coverage80_by_bin_metric=np.where(valid, covered.astype(float), np.nan).tolist(),
                width80_by_metric=width.tolist())


def average(rows):
    keys = ['crps', 'crps_by_metric', 'high_accuracy_mae', 'mae_by_metric',
            'coverage80', 'coverage80_by_metric', 'high_coverage80', 'width80_by_metric']
    return {k: np.mean([r[k] for r in rows], axis=0).tolist() for k in keys}


def boot(d):
    d = np.asarray(d)
    bs = d[np.random.default_rng(891).integers(0, len(d), (10000, len(d)))].mean(axis=1)
    return dict(n=len(d), mean=float(d.mean()), lo95=float(np.quantile(bs, .025)),
                hi95=float(np.quantile(bs, .975)), lower00625=float(np.quantile(bs, .00625)),
                upper99375=float(np.quantile(bs, .99375)))


def main():
    coverage = {r['subject']: r for r in json.loads((ROOT/'data/COVERAGE.json').read_text())}
    rows = []
    manifest = []
    score_diff_max = 0.
    conditional = []
    primary_observed = []
    primary_means = {m: [] for m in MODELS}
    prefix_state = []
    for tag in ['source_animals', 'source_labs']:
        folder = ROOT/'artifacts/forecasts'/tag
        saved = json.loads((folder/'scores.json').read_text())
        for p in sorted(folder.glob('*__observed.npz')):
            subject = p.name.removesuffix('__observed.npz')
            y_all = np.load(p)['observed']
            if len(y_all) >= 6:
                primary_observed.append(y_all[:6])
            manifest.append(dict(path=str(p.relative_to(ROOT)), sha256=digest(p)))
            for model in MODELS:
                path = folder/(subject+'__'+model+'.npz')
                z = np.load(path)
                assert z['samples'].shape[1] <= 10
                if len(y_all) >= 6:
                    primary_means[model].append(z['samples_primary'][:, :6].mean(axis=0))
                    if model == 'dnnglm32':
                        meta = json.loads(path.with_suffix('.json').read_text())
                        prefix_state.append(dict(subject=subject,
                            pool_at_prefix=meta['trainer']['pool'][0],
                            endpoint_covariance_eigenvalues=np.linalg.eigvalsh(meta['calibration']['endpoint_covariance']).tolist()))
                manifest.append(dict(path=str(path.relative_to(ROOT)), sha256=digest(path)))
                for horizon in [1000, 3000, 5000]:
                    b = min(horizon//500, len(y_all))
                    for arm, key in [('autonomous','samples_primary'), ('raw_autonomous','samples')]:
                        r = dict(subject=subject, lab=coverage[subject]['lab'], split=coverage[subject]['split'],
                                 model=model, arm=arm, horizon=horizon, full_horizon=len(y_all)>=horizon//500,
                                 actual_bins=b, **independent_score(z[key][:, :b], y_all[:b]))
                        ref = [x for x in saved if x['subject']==subject and x['model']==model and x['horizon']==horizon and x['arm']==arm]
                        assert len(ref)==1
                        score_diff_max = max(score_diff_max, abs(r['crps']-ref[0]['crps']))
                        rows.append(r)
        conditional += [r for r in saved if r['arm']=='conditional_diagnostic' and r['horizon']==3000 and r['full_horizon']]
    summary = []
    groups = ['all', 'animal_holdout', 'lab_holdout', 'hoferlab', 'wittenlab']
    for horizon in [1000, 3000, 5000]:
      for full in [True, False]:
       for arm in ['autonomous', 'raw_autonomous']:
        for group in groups:
         for model in MODELS:
            rr = [r for r in rows if r['horizon']==horizon and (r['full_horizon'] or not full) and r['arm']==arm and r['model']==model and (group=='all' or r['split']==group or r['lab']==group)]
            if not rr: continue
            entry = dict(horizon=horizon, full_only=full, arm=arm, group=group, model=model, n=len(rr), **average(rr))
            if horizon==3000 and full:
                entry['coverage80_by_bin_metric'] = np.nanmean([r['coverage80_by_bin_metric'] for r in rr], axis=0).tolist()
            summary.append(entry)
    paired = []
    canonical_order = json.loads((ROOT/'artifacts/results/SUBJECT_ORDER.json').read_text())
    for group in groups:
      for model in MODELS[:4]:
       for baseline in BASELINES:
        rr = [r for r in rows if r['horizon']==3000 and r['full_horizon'] and r['arm']=='autonomous' and r['model'] in [model, baseline] and (group=='all' or r['split']==group or r['lab']==group)]
        a = {r['subject']:r for r in rr if r['model']==model}
        b = {r['subject']:r for r in rr if r['model']==baseline}
        assert set(a)==set(b)
        ids = [s for s in canonical_order if s in a]
        gain = [b[s]['crps']-a[s]['crps'] for s in ids]
        mae_gain = [b[s]['high_accuracy_mae']-a[s]['high_accuracy_mae'] for s in ids]
        paired.append(dict(group=group, model=model, baseline=baseline,
                           relative_crps_gain=float(np.mean(gain)/np.mean([b[s]['crps'] for s in b])),
                           high_mae_relative_gain=float(np.mean(mae_gain)/np.mean([b[s]['high_accuracy_mae'] for s in b])),
                           crps=boot(gain), high_mae=boot(mae_gain)))
    cond_summary = []
    for model in MODELS[:4]:
        rr = [r for r in conditional if r['model']==model]
        cond_summary.append(dict(model=model, n=len(rr), binary_nll=float(np.mean([r['binary_nll'] for r in rr])),
                                 curve_crps_diagnostic=float(np.mean([r['crps'] for r in rr]))))
    result = dict(scope='retained source future curves only; no external prefixes/outcomes; no refits',
                  freeze_sha256=digest(ROOT/'protocols/FREEZE.json'),
                  n_independent_animals_primary=len({r['subject'] for r in rows if r['horizon']==3000 and r['full_horizon']}),
                  score_max_abs_difference=score_diff_max, summary=summary, paired=paired,
                  conditional_diagnostic=cond_summary, source_forecast_manifest=manifest)
    (OUT/'SOURCE_REVIEW_STATS.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    (OUT/'SOURCE_REVIEW_SCORES.json').write_text(json.dumps(rows, indent=2, allow_nan=False)+'\n')
    means = dict(n=len(primary_observed), observed_mean=np.mean(primary_observed, axis=0).tolist(),
                 forecasts={m: np.mean(primary_means[m], axis=0).tolist() for m in MODELS})
    (OUT/'SOURCE_MEAN_CURVES.json').write_text(json.dumps(means, indent=2, allow_nan=False)+'\n')
    (OUT/'PREFIX_STATE_DIAGNOSTICS.json').write_text(json.dumps(prefix_state, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['n_independent_animals_primary','score_max_abs_difference','conditional_diagnostic']},indent=2))
    print(json.dumps([r for r in summary if r['horizon']==3000 and r['full_only'] and r['group']=='all' and r['arm']=='autonomous'],indent=2))
    print(json.dumps([r for r in paired if r['group']=='all' and r['baseline']=='growth'],indent=2))


if __name__=='__main__':main()

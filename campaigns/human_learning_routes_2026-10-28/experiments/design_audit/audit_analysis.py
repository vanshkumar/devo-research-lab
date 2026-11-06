"""Independent scoring/counterfactual checks on inputs with SYNTHETIC choices.

No raw data or validation outcomes are opened. The artificial choices are
alternating ±1 with deterministic omissions and are not empirical results.
"""
from pathlib import Path
import sys, json, hashlib, math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments'))
import model
import analysis
from run_study import model_old_context


def main():
    d = pd.read_csv(ROOT / 'outputs/input_only/trial_inputs.csv', dtype={'subject': str})
    d['choice'] = np.where(d.trial % 2, 1., -1.)
    d.loc[d.trial % 47 == 0, 'choice'] = 0.
    d['feedbackType'] = d.choice * d.stimSide
    split = pd.read_csv(ROOT / 'protocol/split_manifest.csv', dtype={'subject': str})
    d = d.merge(split[['subject', 'partition']], on='subject', validate='many_to_one')
    f = model.prepare_features(d)
    w = analysis.windows(f.rows)
    mask = []; old = []; offsets = []; per_subject = {}
    for subject, s in f.rows.groupby('subject'):
        sides = s.probabilityLeft.to_numpy(); prior_switch = None
        subject_masks = []
        for local, row in enumerate(s.itertuples()):
            if local and sides[local] != sides[local-1] and sides[local] != .5 and sides[local-1] != .5 and row.trial >= 200:
                prior_switch = local
            off = row.trial - s.trial.iloc[prior_switch] if prior_switch is not None else 999
            old_side = (1 if sides[prior_switch-1] > .5 else -1) if prior_switch is not None else 0
            eligible = 200 <= row.trial < 600 and off < 30 and row.stimContrast in [0., .1]
            mask.append(eligible); old.append(old_side); offsets.append(off); subject_masks.append(eligible)
        per_subject[subject] = sum(subject_masks)
    np.testing.assert_array_equal(mask, w.primary.to_numpy())
    np.testing.assert_array_equal(old, w.old_majority.to_numpy())
    np.testing.assert_array_equal(offsets, w.switch_offset.to_numpy())
    np.testing.assert_array_equal(np.asarray(mask) & f.responded, w.primary_responded.to_numpy())
    coverage = pd.read_csv(Path(__file__).with_name('input_coverage.csv'), dtype={'subject': str}).set_index('subject')
    assert all(per_subject[s] == coverage.loc[s, 'n30'] for s in per_subject)

    fits = {}
    for variant in ['shared', 'condition']:
        X, Z, names, rnames, _ = model.build_design(f, variant)
        beta = np.zeros(len(names)); beta[1:5] = [.3, .8, 1.2, 1.6]
        for name, value in [('history_tau2', .2), ('history_tau8', .5), ('history_tau32', .1)]: beta[names.index(name)] = value
        if variant == 'condition': beta[-3:] = [.1, -.5, .8]
        fits[variant] = model.FitResult(variant, beta, np.zeros((80, 5)), f.subjects,
                                        names, rnames, f.config, f.calibration_transform, {})
    scored, pp, _, summary = analysis.score_predictions(f, fits)
    manual = {}
    for sid, s in scored.loc[scored.primary_responded].groupby('subject'):
        vals = []
        for row in s.itertuples():
            y = int(row.choice == 1)
            vals.append(math.log(row.p_condition if y else 1-row.p_condition) - math.log(row.p_shared if y else 1-row.p_shared))
        manual[sid] = sum(vals)/len(vals)
    check = pp.set_index('subject').delta_log
    assert max(abs(manual[s] - check[s]) for s in manual) < 1e-14
    assert abs(sum(manual.values())/len(manual) - summary['delta_log']['mean']) < 1e-14

    zf = analysis.zero_contrast_features(f)
    X, Z, names, rnames, _ = model.build_design(zf, 'condition')
    sensory_columns = [i for i, name in enumerate(names) if 'contrast_' in name or 'sensory_time' in name]
    assert np.all(X[:, sensory_columns] == 0.)
    assert np.all(Z[:, 1] == 0.)
    np.testing.assert_equal(zf.history, f.history)
    np.testing.assert_equal(zf.calibration, f.calibration)
    shift = model.predict_adaptation_contrast(fits['condition'], zf) * np.asarray(old)
    submeans = []
    for sid, s in w.groupby('subject'):
        ix = s.index[s.switch_offset.between(0, 19)].to_numpy()
        submeans.append(float(np.mean(shift[ix])))
    eff, _ = analysis.standardized_effect(fits['condition'], f)
    assert abs(eff['mean'] - np.mean(submeans)) < 1e-14

    # Reset-feedback trace equals a direct weighted sum beginning at the switch.
    max_error = 0.
    for sid, s in w.groupby('subject'):
        evidence = (s.choice * s.feedbackType).to_numpy()
        for row in s.loc[s.switch_offset.between(0,29)].itertuples():
            t, sw, idx = row.trial, row.switch_trial, row.Index
            start_idx = s.index[s.trial == sw][0]
            for j, tau in enumerate([2., 8., 32.]):
                removed = f.history[idx,j] - f.history[start_idx,j] * math.exp(-(t-sw)/tau)
                independent = sum(evidence[u] * (1-math.exp(-1/tau)) * math.exp(-(t-u-1)/tau) for u in range(sw,t))
                max_error = max(max_error, abs(removed-independent))
    assert max_error < 1e-14
    result = dict(passed=True, data_scope='input-only trial arrays; all choices synthetic',
                  hashes={name: hashlib.sha256((ROOT/'experiments'/name).read_bytes()).hexdigest() for name in ['analysis.py','run_study.py']},
                  checks=['independent switch/primary/omission masks', 'independent scalar participant log scores',
                          'equal participant aggregate', 'zero-contrast sensory removal',
                          'fixed histories/calibration', 'independent standardized mean',
                          'old-context trace removal equals direct postswitch sum'],
                  max_reset_history_error=max_error)
    Path(__file__).with_name('analysis_audit_results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()

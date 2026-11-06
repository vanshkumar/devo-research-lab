"""Finite source-only input and engagement sensitivities; no evaluation I/O."""
from pathlib import Path
import sys
import numpy as np
from scipy.special import expit, logit, ndtr
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
DEVELOPMENT = HERE.parent / 'acquisition-rule-vs-tracker-2026-11-05'
sys.path.insert(0, str(DEVELOPMENT))
import early as inherited
from pilot import subject, track
from trainer import VectorTrainer, FULL_CONTRASTS
from baselines import draw_initial, competence_at, omission_at
from rnn_rollout import calibration_particles


def causal_contexts(a):
    """No current choice/outcome enters the current pretrial context."""
    n = len(a)
    x = np.nan_to_num(a[:, 1]) - np.nan_to_num(a[:, 0])
    contrast = np.abs(x)
    idx = np.abs(contrast[:, None] - FULL_CONTRASTS).argmin(1)
    if not np.allclose(contrast, FULL_CONTRASTS[idx], atol=1e-8):
        raise ValueError('Source contrast outside the six frozen levels')
    context = np.zeros(n, np.int8)
    wheelbin = np.zeros(n, np.int8)
    position = np.zeros(n, np.int32)
    previous_omission = np.zeros(n)
    buf = [0] * 10
    previous = 0
    prevomit = 0
    pos = 0
    for t in range(n):
        if a[t, 6]:
            buf = [0] * 10
            previous = 0
            prevomit = 0
            pos = 0
        context[t] = previous
        wheelbin[t] = sum(c == 1 for c in buf) // 2
        position[t] = pos
        previous_omission[t] = prevomit
        previous = 0 if a[t, 3] > 0 else 1 + int(idx[t])
        prevomit = int(a[t, 2] == 0)
        buf = (buf + [int(a[t, 2])])[-10:]
        pos += 1
    return dict(idx=idx, side=(x < 0).astype(int),
                # At zero contrast signed x loses physical side; inspect source columns.
                left=(np.isfinite(a[:, 0]) &
                      (~np.isfinite(a[:, 1]) | (a[:, 0] >= a[:, 1]))).astype(int),
                context=context, wheelbin=wheelbin, position=position,
                previous_omission=previous_omission,
                stage=np.minimum(np.arange(n) // 500, 5))


def fit_input(raw, train_ids, labs):
    sites = sorted({labs[s] for s in train_ids})
    con = np.zeros((len(sites), 6, 7, 6), np.int64)
    side = np.zeros((len(sites), 7, 6, 2), np.int64)
    rows = 0
    for s in train_ids:
        a = raw[s]
        c = causal_contexts(a)
        j = sites.index(labs[s])
        np.add.at(con[j], (c['stage'], c['context'], c['idx']), 1)
        np.add.at(side[j], (c['context'], c['wheelbin'], c['left']), 1)
        rows += len(a)
    pooled = con.sum(0)
    marginal = pooled.sum(1) + .5
    marginal = marginal / marginal.sum(-1, keepdims=True)
    pooled_con = (pooled + 20 * marginal[:, None, :]) / (pooled.sum(-1, keepdims=True) + 20)
    site_con = (con + 50 * pooled_con[None]) / (con.sum(-1, keepdims=True) + 50)
    pooled = side.sum(0)
    marginal = pooled.sum(0) + .5
    marginal = marginal / marginal.sum(-1, keepdims=True)
    pooled_side = (pooled + 20 * marginal[None]) / (pooled.sum(-1, keepdims=True) + 20)
    site_side = (side + 50 * pooled_side[None]) / (side.sum(-1, keepdims=True) + 50)
    return dict(sites=sites, contrast_counts=con, side_counts=side,
                contrast=site_con, side=site_side,
                pooled_contrast=pooled_con, pooled_side=pooled_side, fit_rows=rows)


def input_tables(fit, lab):
    if lab in fit['sites']:
        j = fit['sites'].index(lab)
        return fit['contrast'][j], fit['side'][j]
    return fit['pooled_contrast'], fit['pooled_side']


class SourceContextTrainer(VectorTrainer):
    """Empirical finite input sensitivity; feedback and reward use original code."""
    def __init__(self, *args, input_fit, lab, **kwargs):
        super().__init__(*args, **kwargs)
        self.contrast_table, self.side_table = input_tables(input_fit, lab)
        self.source_context = np.zeros(self.n, np.int8)
        self.absolute_opportunity = 0

    def _record(self, contrast, side, choice, correct, repeats, reward):
        super()._record(contrast, side, choice, correct, repeats, reward)
        idx = np.abs(contrast[:, None] - FULL_CONTRASTS).argmin(1)
        self.source_context = np.where(correct, 0, 1 + idx).astype(np.int8)
        self.absolute_opportunity += 1

    def new_session(self):
        super().new_session()
        self.source_context[:] = 0

    def sample(self):
        if self.current is not None:
            raise RuntimeError('observe is required')
        stage = min(self.absolute_opportunity // 500, 5)
        probs = self.contrast_table[stage, self.source_context]
        idx = (self.rng.random(self.n)[:, None] >= np.cumsum(probs, axis=1)).sum(1)
        idx = np.minimum(idx, 5)
        contrast = FULL_CONTRASTS[idx]
        wheelbin = self.response_sum_right // 2
        pleft = self.side_table[self.source_context, wheelbin, 1]
        side = np.where(self.rng.random(self.n) < pleft, -1, 1)
        self.prob_left[:] = pleft
        self.current = dict(signed_contrast=contrast * side, contrast=contrast,
                            side=side.astype(np.int8), correct_choice=(-side).astype(np.int8),
                            reward_ul=self.reward_ul.copy(), rep_num=np.zeros(self.n, np.int16),
                            is_repeat=np.zeros(self.n, bool), gain=self.gain.copy(),
                            contrastLeft=np.where(side < 0, contrast, np.nan),
                            contrastRight=np.where(side > 0, contrast, np.nan))
        return {k: v.copy() for k, v in self.current.items()}


def deterministic_omission(a, cutoff, bank, s):
    """Source conditional fitting offset; excludes self, mirrors nearest donor law."""
    w, _, o = inherited.estimate(a, cutoff, None)
    dist = np.sum(((bank['prefix'] - np.r_[w, logit(o)]) / [1.5, 1.5, 1.5, 2.]) ** 2, axis=1)
    dist[bank['subjects'] == s] = np.inf
    order = np.argsort(dist)
    order = order[np.isfinite(dist[order])]
    result = np.zeros(len(a) - cutoff)
    for b in range(10):
        lo = b * 500
        hi = min(len(result), lo + 500)
        if hi <= lo:
            break
        donors = order[bank['valid'][order, b]][:15]
        if not len(donors):
            raise ValueError('No valid independent engagement donors')
        # Mean log-odds offset is a conditional fitting approximation.
        result[lo:hi] = logit(o) + bank['delta_omit'][donors, b].mean()
    return result


def engagement_design(a, cutoff, bank, s):
    c = causal_contexts(a)
    return np.column_stack([np.ones(len(a)-cutoff), deterministic_omission(a, cutoff, bank, s),
                            np.log1p(c['position'][cutoff:] / 50), c['previous_omission'][cutoff:]])


def fit_engagement(raw, train_ids, canonical, cutoff):
    xs = []
    ys = []
    ids = []
    for s in train_ids:
        a = raw[s]
        if len(a) <= cutoff:
            continue
        xs.append(engagement_design(a, cutoff, canonical, s))
        ys.append((a[cutoff:, 2] == 0).astype(float))
        ids.append(s)
    X = np.concatenate(xs)
    y = np.concatenate(ys)
    reference = np.array([0., 1., 0., 0.])
    def objective(beta):
        z = np.einsum('ij,j->i', X, beta)
        p = expit(z)
        delta = beta - reference
        return (np.logaddexp(0, z).sum() - y @ z + .5 * delta @ delta,
                np.einsum('ij,i->j', X, p-y) + delta)
    opt = minimize(objective, reference, method='L-BFGS-B', jac=True,
                   bounds=[(-6, 6), (0, 2), (-3, 3), (-3, 5)], options=dict(maxiter=500, ftol=1e-12))
    if not opt.success:
        raise RuntimeError(str(opt.message))
    return dict(beta=opt.x, fit_subjects=ids, rows=len(y), omissions=int(y.sum()),
                iterations=int(opt.nit), gradient=np.asarray(opt.jac),
                conditional_loss=float(objective(opt.x)[0] / len(y)),
                approximation='conditional fit uses mean donor log odds; autonomous forecasts transform actual correlated donor draws')


def simulate(s, a, cutoff, name, model, canonical, candidate=None, half=None, n=128,
             condition='primary', input_fit=None, lab=None, engagement_fit=None, stream_offset=0,
             exact_gru=False):
    """Only a[:cutoff] values and a[:,6] future boundaries are ever read."""
    stream = inherited.original_seed(s) + stream_offset
    prefix = subject(a[:cutoff])
    shared = draw_initial(prefix, canonical, n, stream+211, exclude=s, neighbors=15, competence='growth')
    info = None
    if name == 'gru':
        state, info = calibration_particles(model, prefix, n, stream+313)
        if exact_gru:
            # w0 draws retained; propagate nonlinear prefix for each draw.
            rng = np.random.default_rng(stream+313)
            delta = rng.multivariate_normal(np.zeros(3), np.asarray(info['initial_covariance']), size=n)
            delta *= info['endpoint_sd_cap_factor']
            for j in range(n):
                _, _, endpoint = model.sequence(prefix, np.asarray(info['w0']) + delta[j])
                state['w'][j] = endpoint['w']
                state['h'][j] = endpoint['h']
    elif name == 'recent_growth':
        choice = inherited.choice_draw(s, a, cutoff, half, candidate, n, stream)
    if cutoff == 1000:
        action = np.random.default_rng(stream+101)
        teacher_seed = stream+419
    else:
        action = np.random.default_rng(stream+900101)
        teacher_seed = stream+900419
    if condition == 'source_context_input':
        teacher = SourceContextTrainer.from_prefix(prefix, n, teacher_seed, 'standard', input_fit=input_fit, lab=lab)
    else:
        teacher = VectorTrainer.from_prefix(prefix, n, teacher_seed, 'standard')
    contexts = causal_contexts(a[:cutoff])
    pos = int(contexts['position'][-1]) + 1
    previous_omission = np.full(n, a[cutoff-1, 2] == 0, dtype=float)
    counts = np.zeros((n, 7), np.int32)
    saved = []
    # Blocks on the shared scored opportunities, for omission burst checks.
    omission_blocks = []
    omission_block = np.zeros(n, np.int32)
    for absolute in range(cutoff, 3000):
        t = absolute-cutoff
        if absolute == 1000 and cutoff < 1000:
            action = np.random.default_rng(stream+101)
            teacher.rng = np.random.default_rng(stream+419)
        day = bool(a[absolute, 6])
        if day:
            teacher.new_session()
            pos = 0
            previous_omission[:] = 0
        task = teacher.sample()
        x = task['signed_contrast']
        f = track.psych(x)
        if name == 'gru':
            p = model.probs(state, x)
        elif name == 'growth':
            p = expit(np.sum(competence_at(shared, t)*f, axis=1))
        else:
            p = expit(np.sum(competence_at(choice, t)*f, axis=1))
        q = omission_at(shared, t, 'growth')
        if condition == 'source_calibrated_engagement':
            b = np.asarray(engagement_fit[cutoff]['beta'])
            q = expit(b[0] + b[1]*logit(np.clip(q, 1e-12, 1-1e-12)) +
                      b[2]*np.log1p(pos/50) + b[3]*previous_omission)
        c = np.where(action.random(n) < p, -1, 1).astype(np.int8)
        c[action.random(n) < q] = 0
        feedback = teacher.observe(c)
        if name == 'gru':
            model.update(state, x, c, feedback['feedbackType'], session_start=day)
        if absolute >= 1000:
            for j, sign in ((0, -1), (2, 1)):
                keep = x == sign
                counts[:, j] += keep
                counts[:, j+1] += keep & (c == -sign)
            counts[:, 4] += c == 0
            counts[:, 5] += c < 0
            counts[:, 6] += feedback['correct']
            omission_block += c == 0
            if (absolute+1-1000) % 50 == 0:
                omission_blocks.append(omission_block.copy())
                omission_block[:] = 0
        previous_omission = (c == 0).astype(float)
        pos += 1
        if absolute+1 in (1500, 3000):
            saved.append(counts.copy())
    return np.stack(saved, axis=1), info, np.stack(omission_blocks, axis=1)


def pretrial_input_checks(s, a, cutoff, input_fit, lab):
    c = causal_contexts(a)
    ct, st = input_tables(input_fit, lab)
    ix = np.arange(cutoff, 3000)
    cp = ct[c['stage'][ix], c['context'][ix], c['idx'][ix]]
    pl = st[c['context'][ix], c['wheelbin'][ix], 1]
    target = c['left'][ix]
    empirical = dict(n=len(ix), contrast_log_loss=float(-np.log(cp).mean()),
                     side_log_loss=float(-np.log(np.where(target, pl, 1-pl)).mean()),
                     side_brier=float(np.mean((target-pl)**2)),
                     side_bias=float(np.mean(target-pl)), contrast_support_failures=int(np.sum(cp == 0)))
    tr = VectorTrainer.from_prefix(subject(a[:cutoff]), 1, inherited.original_seed(s), 'standard')
    nllc = nlls = brier = bias = 0.
    outside = parameters = 0
    bins = np.zeros((10, 3))
    empirical_bins = np.zeros((10, 3))
    for t in ix:
        if a[t, 6]:
            tr.new_session()
        k = c['idx'][t]
        contrast = FULL_CONTRASTS[k]
        repeat = bool(tr.pending_repeat[0])
        rate = tr.response_sum_right[0] / 10
        pleft = float(ndtr((.5-rate)/.5)) if repeat else float(tr.prob_left[0])
        weights = tr.pool[0].astype(float)
        weights[-1] *= .5
        probability = float(np.isclose(contrast, tr.repeat_contrast[0])) if repeat else weights[k] / weights.sum()
        outside += probability == 0
        nllc -= np.log(max(probability, 1e-12))
        y = int(c['left'][t])
        nlls -= np.log(max(pleft if y else 1-pleft, 1e-12))
        brier += (y-pleft)**2
        bias += y-pleft
        param = 1-rate if repeat else .5
        parameters += not np.isclose(a[t, 5], param, atol=1e-7)
        bins[min(9, int(pleft*10))] += [1, y, pleft]
        ep = st[c['context'][t], c['wheelbin'][t], 1]
        empirical_bins[min(9, int(ep*10))] += [1, y, ep]
        tr._record(np.array([contrast]), np.array([-1 if y else 1]), np.array([int(a[t, 2])]),
                   np.array([a[t, 3] > 0]), np.array([repeat]), np.array([max(0, a[t, 4])]))
        tr.prob_left[:] = param
    primary = dict(n=len(ix), contrast_log_loss=nllc/len(ix), side_log_loss=nlls/len(ix),
                   side_brier=brier/len(ix), side_bias=bias/len(ix),
                   contrast_support_failures=int(outside), parameter_mismatches=int(parameters),
                   side_calibration=bins.tolist())
    empirical['side_calibration'] = empirical_bins.tolist()
    return dict(primary=primary, source_context_input=empirical)

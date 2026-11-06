"""Scoring, observed summaries and paired planning on fixed endpoint laws."""

import numpy as np
from scipy.special import ndtr
from scipy.stats import t

from calibrate import IDENTITY, MISSING, fit_weights, residual_witness


CONTRASTS = ('D', 'W', 'C', 'I')
TARGET_OWNER_SIZES = (85, 31, 14, 6, 11, 3, 24, 7, 7, 4)
TARGET_N = sum(TARGET_OWNER_SIZES)


def training_terms(laws, outcomes=None, truth_actor=None, truth_weights=None):
    gram = np.empty(laws.shape + (3, 3))
    linear = np.empty(laws.shape + (3,))
    for actor, i, sign in np.ndindex(laws.shape):
        law = laws[actor, i, sign]
        gram[actor, i, sign] = law.gram
        if outcomes is None:
            truth = laws[truth_actor, i, sign]
            values, masses = truth.outcome_law(truth_weights)
        else:
            values, masses = [outcomes[i, sign]], np.ones(1)
        linear[actor, i, sign] = law.linear_term(values) @ masses
    return gram, linear


def fit_source(terms, indices):
    gram, linear = [term[:, indices].mean(axis=(1, 2)) for term in terms]
    return np.stack([fit_weights(g, b) for g, b in zip(gram, linear)])


def fixed_profiles(weights, n):
    return np.broadcast_to(weights[:, None, :], (2, n, 3))


def feature_bank(laws, feature):
    tiers = np.empty(laws.shape + (3, feature.bins + 1))
    for index in np.ndindex(laws.shape):
        tiers[index] = feature.tier_means(laws[index])
    return tiers


class PairedEvaluation:
    def __init__(self, laws, feature, tiers, profiles, blocks):
        self.laws = laws
        self.feature = feature
        self.profiles = profiles
        self.o_mean, self.w, self.orthogonality = residual_witness(tiers, profiles, blocks)
        self.size = np.sum(self.w ** 2, axis=-1)
        self.o_dot_w = np.sum(self.o_mean * self.w, axis=-1)

    def on_outcomes(self, i, sign, values):
        ordinary, gru = self.laws[:, i, sign]
        o_raw, g_raw = [law.scores(IDENTITY, values) for law in (ordinary, gru)]
        o_cal, g_cal = [law.scores(self.profiles[a, i], values)
                        for a, law in enumerate((ordinary, gru))]
        alignment = 2 * (self.feature.dot_outcomes(values, self.w[i, sign]) - self.o_dot_w[i, sign])
        return np.column_stack((.9 * o_cal - g_cal, alignment - self.size[i, sign],
                                (o_raw - g_raw) - (o_cal - g_cal), o_raw - o_cal,
                                o_raw, g_raw, o_cal, g_cal))

    def observed(self, outcomes):
        n = self.laws.shape[1]
        return np.stack([np.mean([self.on_outcomes(i, sign, [outcomes[i, sign]])[0]
                                  for sign in range(2)], axis=0) for i in range(n)])

    def opposed_moments(self, truth_profiles, truth_actor, shift=0):
        """Exact conditional moments, scoring the same outcome against all forecasts."""
        n = self.laws.shape[1]
        means = np.empty((n, 8))
        independent = np.empty((n, 4))
        same_rank = np.empty((n, 4))
        for i in range(n):
            masses, values, sign_means = [], [], []
            for sign in range(2):
                y, p = self.laws[truth_actor, i, sign].outcome_law(truth_profiles[truth_actor, i])
                y = np.where(y == MISSING, y, np.clip(y + shift, 0, 1))
                score = self.on_outcomes(i, sign, y)
                masses.append(p)
                values.append(score)
                sign_means.append(p @ score)
            means[i] = np.mean(sign_means, axis=0)
            independent[i] = sum(p @ ((s[:, :4] - m[:4]) ** 2)
                                 for p, s, m in zip(masses, values, sign_means)) / 4
            same_rank[i] = coupled_variance(masses, values, means[i, :4])
        return means, independent, same_rank


def coupled_variance(masses, values, mean):
    cdfs = [np.cumsum(p) for p in masses]
    for cdf in cdfs:
        cdf[-1] = 1
    cuts = np.unique(np.r_[0, *cdfs])
    midpoints = (cuts[:-1] + cuts[1:]) / 2
    sign_scores = [s[np.searchsorted(cdf, midpoints, side='left'), :4]
                   for cdf, s in zip(cdfs, values)]
    paired = (sign_scores[0] + sign_scores[1]) / 2
    return np.diff(cuts) @ ((paired - mean) ** 2)


def family_critical(df):
    return float(t.ppf(1 - .05 / (2 * len(CONTRASTS)), df))


def risks_from_scores(mean):
    raw, cal = mean[4:6], mean[6:8]
    return {
        'raw_O_G': raw, 'cal_O_G': cal,
        'raw_D': .9 * raw[0] - raw[1],
        'raw_relative_GRU_gain': 1 - raw[1] / raw[0],
        'cal_relative_GRU_gain': 1 - cal[1] / cal[0],
    }


def summarize(scores, owners, roster, size):
    n = len(scores)
    four = scores[:, :4]
    mean = scores.mean(axis=0)
    labels = np.unique(owners)
    groups = [owners == label for label in labels]
    centered_sums = np.stack([(four[group] - mean[:4]).sum(axis=0) for group in groups])
    clustered = np.sqrt(len(groups) / (len(groups) - 1) * (centered_sums ** 2).sum(axis=0)) / n
    iid_se = four.std(axis=0, ddof=1) / np.sqrt(n)
    iid_hw = iid_se * family_critical(n - 1)
    cluster_hw = clustered * family_critical(len(groups) - 1)
    return {
        **risks_from_scores(mean),
        'D_W_C_I': mean[:4],
        'nominal_animal_bands': np.column_stack((mean[:4] - iid_hw, mean[:4] + iid_hw)),
        'nominal_cluster_bands': np.column_stack((mean[:4] - cluster_hw, mean[:4] + cluster_hw)),
        'witness_size': size.mean(), 'witness_alignment': mean[1] + size.mean(),
        'owners': {str(label): {'n': int(mask.sum()), 'D_W_C_I': four[mask].mean(axis=0),
                                'witness_size': size[mask].mean(),
                                'leave_out_fixed_contributions': four[~mask].mean(axis=0)}
                   for label, mask in zip(labels, groups)},
        'equal_owner_D_W_C_I': np.stack([four[mask].mean(axis=0) for mask in groups]).mean(axis=0),
        'rosters': {str(label): {'n': int(mask.sum()), 'D_W_C_I': four[mask].mean(axis=0),
                                 'raw_O_G_cal_O_G': scores[mask, 4:].mean(axis=0)}
                    for label in np.unique(roster) for mask in [roster == label]},
    }


def pass_probabilities(mean, se, df, extra_halfwidth=None):
    critical = family_critical(df)
    extra = np.zeros(4) if extra_halfwidth is None else extra_halfwidth
    directions = {'calibration': np.array([-1, -1, 1, 1]), 'individual': np.array([1, 1, 0, 1])}
    results = {}
    for label, direction in directions.items():
        headroom = direction * mean - extra
        standard = np.divide(headroom, se, out=np.zeros_like(headroom), where=se > 0)
        power = np.where(se > 0, ndtr(standard - critical), (headroom > 0).astype(float))
        results[label] = {'marginals': {name: float(p) for name, d, p in zip(CONTRASTS, direction, power) if d},
                          'joint_upper_working': float(power[direction != 0].min())}
    return results


def plan(moments, extra_halfwidth=None):
    rows, independent, same_rank = moments
    mean = rows.mean(axis=0)
    between = rows[:, :4].var(axis=0, ddof=1)
    design = {}
    for name, within in [('independent_signs', independent.mean(axis=0)),
                         ('same_rank_signs', same_rank.mean(axis=0))]:
        se_fixed = np.sqrt(within / TARGET_N)
        se_iid = np.sqrt((within + between) / TARGET_N)
        design[name] = {
            'fixed_recipient_se': se_fixed,
            'fixed_recipient_power': pass_probabilities(mean[:4], se_fixed, TARGET_N - 1, extra_halfwidth),
            'iid_learner_se': se_iid,
            'iid_learner_power': pass_probabilities(mean[:4], se_iid, TARGET_N - 1, extra_halfwidth),
            'owner_ICC_stress': {},
        }
        concentration = sum(size * size for size in TARGET_OWNER_SIZES) / TARGET_N - 1
        for rho in (.05, .10):
            effect = 1 + rho * concentration
            se = np.sqrt(effect) * se_iid
            design[name]['owner_ICC_stress'][str(rho)] = {
                'effective_n': TARGET_N / effect, 'se': se,
                'power': pass_probabilities(mean[:4], se, len(TARGET_OWNER_SIZES) - 1, extra_halfwidth),
            }
    return {**risks_from_scores(mean), 'D_W_C_I': mean[:4], 'planning': design}

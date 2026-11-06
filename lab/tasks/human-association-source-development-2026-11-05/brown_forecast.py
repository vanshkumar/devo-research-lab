"""Causal trial states and environment draws for the frozen Brown forecast."""
from collections import Counter
from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.special import expit, logsumexp


ALPHA = np.array([.16, .35, .65])
WM_TAU = np.array([2., 4., 7.])
TYPE_COUNT = len(ALPHA)
SCENARIOS = ("brown", "rescue_supported", "rescue_distractor")
ACTORS = ("ordinary", "pooled", "personal")


@dataclass(frozen=True)
class Prefix:
    person: int
    block: int
    load: int
    cue: np.ndarray
    action: np.ndarray
    feedback: np.ndarray
    rt: np.ndarray

    @property
    def tempo(self):
        valid = self.rt[self.rt > 0]
        return float(np.median(valid)) if len(valid) else .6

    @property
    def omissions(self):
        return float(np.mean(self.action < 0))


@dataclass(frozen=True)
class SourceBlock:
    prefix: Prefix
    cue: np.ndarray
    action: np.ndarray
    feedback: np.ndarray
    correct_map: np.ndarray

    @property
    def target(self):
        origin = len(self.prefix.cue)
        return np.array([np.count_nonzero(self.feedback[origin:] == 1),
                         np.count_nonzero(self.action[origin:] < 0)])


def make_prefix(raw):
    person, block, load = raw[0, :3].astype(int)
    early = raw[:2 * load]
    cue_ids = np.unique(early[:, 4])
    if len(early) != 2 * load or len(cue_ids) != load:
        raise ValueError("incomplete origin or not all cues exposed in prefix")
    prefix = Prefix(int(person), int(block), int(load), np.searchsorted(cue_ids, early[:, 4]),
                    np.where(early[:, 9] > 0, early[:, 9] - 1, -1).astype(int),
                    early[:, 11].astype(int), early[:, 13].copy())
    return prefix, cue_ids


def make_block(raw):
    prefix, cue_ids = make_prefix(raw)
    window = raw[:7 * prefix.load]
    if len(window) != 7 * prefix.load:
        raise ValueError("missing prescribed score window")
    cues = np.searchsorted(cue_ids, window[:, 4])
    if np.any(cues >= prefix.load) or np.any(cue_ids[cues] != window[:, 4]):
        raise ValueError("cue is not in prefix-defined assignment")
    if np.any(window[:, 7] >= 9):
        raise ValueError("window reaches candidate cue-level criterion")
    action = np.where(window[:, 9] > 0, window[:, 9] - 1, -1).astype(int)
    outcome = window[:, 11].astype(int)
    correct_map = np.array([window[np.flatnonzero(cues == i)[0], 8] - 1
                            for i in range(prefix.load)], dtype=int)
    if not np.array_equal(np.where(action >= 0, action == correct_map[cues], -1), outcome):
        raise ValueError("feedback does not match fixed environment")
    return SourceBlock(prefix, cues, action, outcome, correct_map)


class History:
    def __init__(self, prefix, n, types=None):
        self.load = prefix.load
        self.practice = np.log1p(prefix.block - 1) / 3
        self.tempo = prefix.tempo
        self.prefix_omission = prefix.omissions
        self.i = np.arange(n)
        self.n = n
        self.t = 0
        cue_shape = (n, self.load)
        key_shape = (*cue_shape, 3)
        self.seen = np.zeros(cue_shape, dtype=int)
        self.last_seen = np.full(cue_shape, -1, dtype=int)
        self.last_response = np.full(cue_shape, -1, dtype=int)
        self.last_feedback_at = np.full(cue_shape, -1, dtype=int)
        self.last_feedback = np.zeros(cue_shape)
        self.last_key = np.full(n, -1, dtype=int)
        self.wins = np.zeros(key_shape)
        self.errors = np.zeros(key_shape)
        self.recency_at = np.full(key_shape, -1, dtype=int)
        self.recency_sign = np.zeros(key_shape)
        self.recent_correct = np.full(n, 1 / 3)
        self.recent_omit = np.zeros(n)
        self.types = types
        if types is not None:
            self.q = np.full(key_shape, 1 / 3)
            self.habit = np.zeros(key_shape)

    def features(self, cue):
        i = self.i
        seen = self.seen[i, cue]
        lag = np.where(seen > 0, self.t - self.last_seen[i, cue], self.load)
        loglag = np.log1p(lag)[:, None] / 3
        wins = self.wins[i, cue]
        errors = self.errors[i, cue]
        known = (wins > 0).any(axis=1, keepdims=True)
        possible = np.where(known, wins > 0, errors == 0).astype(float)
        recency = self.recency_sign[i, cue] * np.exp(-(self.t - self.recency_at[i, cue]) / 4)
        last_key = np.arange(3) == self.last_key[:, None]
        cue_last_key = np.arange(3) == self.last_response[i, cue, None]
        # Truthful elimination, recall, reward/error history, recency, practice,
        # motor bias and shared adaptation all enter the ordinary rival.
        features = [possible, possible * known, np.log1p(wins), np.log1p(errors),
                    recency, possible * loglag, possible * (self.load == 6),
                    possible * (seen[:, None] / 8), possible * self.recent_correct[:, None],
                    possible * self.practice, last_key, cue_last_key,
                    np.broadcast_to([1., 0., 0.], (self.n, 3)),
                    np.broadcast_to([0., 1., 0.], (self.n, 3))]
        timing = np.column_stack([
            np.ones(self.n), np.full(self.n, self.load == 6),
            np.full(self.n, self.practice), np.full(self.n, self.t / (7 * self.load)),
            seen / 8, loglag[:, 0], self.recent_correct, self.recent_omit,
            np.full(self.n, (self.tempo - .6) / .25),
            np.full(self.n, self.prefix_omission),
        ])
        if self.types is not None:
            memory_lag = self.t - self.last_feedback_at[i, cue]
            strength = self.last_feedback[i, cue] * np.exp(-memory_lag / WM_TAU[self.types])
            wm = strength[:, None] * cue_last_key
            features.extend((self.q[i, cue] - 1 / 3, wm, wm * (self.load == 6),
                             self.habit[i, cue]))
        ranking = 2 * possible + np.log1p(wins) - np.log1p(errors) + .1 * recency
        return np.stack(features, axis=-1), timing, ranking

    def advance(self, cue, action, feedback):
        i = self.i
        self.seen[i, cue] += 1
        self.last_seen[i, cue] = self.t
        answered = action >= 0
        j = i[answered]
        c = cue[answered]
        a = action[answered]
        y = feedback[answered]
        self.wins[j, c, a] += y == 1
        self.errors[j, c, a] += y == 0
        self.recency_at[j, c, a] = self.t
        self.recency_sign[j, c, a] = 2 * y - 1
        self.last_response[j, c] = a
        self.last_feedback[j, c] = 2 * y - 1
        self.last_feedback_at[j, c] = self.t
        self.last_key[j] = a
        if self.types is not None:
            self.q[j, c, a] += ALPHA[self.types[j]] * (y - self.q[j, c, a])
            self.habit[j, c] *= .6
            self.habit[j, c, a] += .4
        self.recent_correct = .85 * self.recent_correct + .15 * (feedback == 1)
        self.recent_omit = .8 * self.recent_omit + .2 * ~answered
        self.t += 1

    def observe_prefix(self, prefix):
        for s, a, y in zip(prefix.cue, prefix.action, prefix.feedback):
            self.advance(np.full(self.n, s), np.full(self.n, a), np.full(self.n, y))


def log_key_prob(features, coef, temp=1.):
    logits = np.einsum("...kf,f->...k", features, coef, optimize=False) / temp
    return logits - logsumexp(logits, axis=-1, keepdims=True)


def prefix_weights(prefix, coef, weights, temp):
    h = History(prefix, TYPE_COUNT, np.arange(TYPE_COUNT))
    logw = np.log(weights)
    for s, a, y in zip(prefix.cue, prefix.action, prefix.feedback):
        cue = np.full(TYPE_COUNT, s)
        if a >= 0:
            features, _, _ = h.features(cue)
            logw += log_key_prob(features, coef, temp)[:, a]
        h.advance(cue, np.full(TYPE_COUNT, a), np.full(TYPE_COUNT, y))
    return np.exp(logw - logsumexp(logw))


def origin_profile(cues, load):
    counts = np.bincount(cues, minlength=load)
    last = np.array([np.flatnonzero(cues == s)[-1] for s in range(load)])
    return counts, np.lexsort((last, counts))


def donor_suffixes(prefix, donor_blocks):
    counts, order = origin_profile(prefix.cue, prefix.load)
    choices = []
    for donor in donor_blocks:
        if donor.prefix.load != prefix.load:
            continue
        donor_counts, donor_order = origin_profile(donor.prefix.cue, prefix.load)
        relabel = np.empty(prefix.load, dtype=int)
        relabel[donor_order] = order
        suffix = relabel[donor.cue[len(prefix.cue):]]
        whole = np.r_[prefix.cue, suffix]
        triple = np.any((whole[:-2] == whole[1:-1]) & (whole[1:-1] == whole[2:]))
        if triple or np.max(np.bincount(whole, minlength=prefix.load)) >= 9:
            continue
        mismatch = np.abs(counts[order] - donor_counts[donor_order]).sum()
        practice_weight = np.exp(-.12 * abs(donor.prefix.block - prefix.block))
        choices.append((mismatch, practice_weight, suffix))
    if not choices:
        raise ValueError("no source donor satisfies the recipient's legal prefix")
    best = min(x[0] for x in choices)
    weights = np.array([w for m, w, _ in choices if m == best])
    return np.stack([s for m, _, s in choices if m == best]), weights / weights.sum(), int(best)


def map_pattern(keys):
    return tuple(np.sort(np.bincount(keys, minlength=3)))


class MapBank:
    def __init__(self, blocks, load):
        all_maps = np.array(list(product(range(3), repeat=load)), dtype=int)
        patterns = [map_pattern(x) for x in all_maps]
        multiplicity = Counter(patterns)
        observed = Counter(map_pattern(b.correct_map) for b in blocks if b.prefix.load == load)
        self.maps = all_maps
        self.prior = np.array([(observed[key] + .1) / multiplicity[key] for key in patterns])

    def conditional(self, prefix):
        weights = self.prior.copy()
        for s, a, y in zip(prefix.cue, prefix.action, prefix.feedback):
            if a >= 0:
                weights *= (self.maps[:, s] == a) == (y == 1)
        if weights.sum() <= 0:
            raise ValueError("no hidden map consistent with recipient prefix")
        return weights / weights.sum()


@dataclass(frozen=True)
class Environment:
    cues: np.ndarray
    maps: np.ndarray
    types: np.ndarray
    miss: np.ndarray
    action: np.ndarray
    tie: np.ndarray
    donor_options: int
    donor_mismatch: int
    map_support: int


def environment(prefix, donors, bank, seed, particles):
    rng = np.random.default_rng(seed)
    options, w, mismatch = donor_suffixes(prefix, donors)
    cue = options[rng.choice(len(options), particles, p=w)]
    key_weights = bank.conditional(prefix)
    hidden = bank.maps[rng.choice(len(key_weights), particles, p=key_weights)]
    shape = cue.shape
    return Environment(cue, hidden, rng.random(particles), rng.random(shape),
                       rng.random(shape), rng.random((*shape, 3)), len(options), mismatch,
                       int(np.count_nonzero(key_weights)))


def sample_rows(prob, uniforms):
    # The last key stays eligible despite final-bit CDF rounding.
    return np.sum(uniforms[:, None] >= np.cumsum(prob[:, :-1], axis=1), axis=1)


def simulate(prefix, world, coef, temp, timeout_coef, timeout_shift, weights=None,
             scenario="brown"):
    n, horizon = world.cues.shape
    types = None if weights is None else np.searchsorted(np.cumsum(weights)[:-1], world.types)
    history = History(prefix, n, types)
    history.observe_prefix(prefix)
    totals = np.zeros((n, 2), dtype=np.int16)
    rescues = 0
    for j in range(horizon):
        cue = world.cues[:, j]
        x, timing, support = history.features(cue)
        omit = world.miss[:, j] < expit(np.einsum("nf,f->n", timing, timeout_coef,
                                                  optimize=False) + timeout_shift)
        prob = np.exp(log_key_prob(x, coef, temp))
        a = sample_rows(prob, world.action[:, j])
        if scenario == "brown":
            a[omit] = -1
        else:
            direction = 1 if scenario == "rescue_supported" else -1
            rank = direction * support + 1e-6 * world.tie[:, j]
            a[omit] = rank[omit].argmax(axis=1)
            rescues += int(omit.sum())
        # Only the environment consults the hidden key after the policy acts.
        y = np.where(a >= 0, a == world.maps[history.i, cue], -1)
        history.advance(cue, a, y)
        totals[:, 0] += y == 1
        totals[:, 1] += a < 0
    return totals, rescues

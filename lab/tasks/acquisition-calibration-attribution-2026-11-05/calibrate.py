"""Exact endpoint energy and the forecast-only recipient witness."""

from itertools import combinations

import numpy as np


IDENTITY = np.full(3, 1 / 3)
FLOOR = 1 / 12
PENALTY = 0.002
MISSING = -1.0


def missing_distance(ratio):
    return np.sqrt(ratio * ratio - ratio + 1)


class RankLaw:
    """Sorted conditional ratio support, three mass components, separate missing mass."""

    def __init__(self, values, masses):
        values, masses = np.asarray(values, float), np.asarray(masses, float)
        if (values.shape != masses.shape or not np.isfinite(values).all()
                or np.any((values != MISSING) & ((values < 0) | (values > 1)))
                or not np.isfinite(masses).all() or np.any(masses < 0)
                or abs(masses.sum() - 1) > 1e-12):
            raise ValueError('Invalid marginal endpoint law')
        self.missing = float(masses[values == MISSING].sum())
        keep = (values != MISSING) & (masses > 0)
        order = np.argsort(values[keep], kind='stable')
        self.ratios = values[keep][order]
        positive = masses[keep][order]
        self.positive = float(positive.sum())
        self.g = missing_distance(self.ratios)
        self.tiers = np.zeros((3, len(positive)))
        if len(positive):
            right = np.cumsum(positive / self.positive)
            right[-1] = 1
            left = np.r_[0, right[:-1]]
            for j in range(3):
                overlap = np.minimum(right, (j + 1) / 3) - np.maximum(left, j / 3)
                self.tiers[j] = (3 * self.positive) * np.maximum(0, overlap)
        tails = np.cumsum(self.tiers[:, ::-1], axis=1)[:, ::-1]
        widths = np.diff(self.ratios, prepend=0)
        self.gram = (tails * widths) @ tails.T
        self.linear_constant = self.tiers @ (self.positive * self.ratios + self.missing * self.g)

    def outcome_law(self, weights):
        values = np.r_[MISSING, self.ratios]
        masses = np.r_[self.missing, weights @ self.tiers]
        keep = masses > 0
        masses = masses[keep]
        return values[keep], masses / masses.sum()

    def linear_term(self, outcomes):
        """For fit: score(w,y) = w.T gram w + w.T linear_term(y)."""
        outcomes = np.atleast_1d(outcomes)
        missing = outcomes == MISSING
        distances = np.abs(self.ratios[:, None] - outcomes[None, :])
        distances[:, missing] = self.g[:, None]
        missing_part = np.where(missing, 0, self.missing * missing_distance(outcomes))
        return self.tiers @ distances + missing_part - self.linear_constant[:, None]

    def scores(self, weights, outcomes):
        """Exact O((J+K) log J) energy for J support atoms and K target values."""
        outcomes = np.atleast_1d(outcomes)
        positive = weights @ self.tiers
        cumulative_mass = np.r_[0, np.cumsum(positive)]
        cumulative_ratio = np.r_[0, np.cumsum(positive * self.ratios)]
        ends = np.searchsorted(self.ratios, outcomes, side='right')
        first = (outcomes * (2 * cumulative_mass[ends] - cumulative_mass[-1])
                 + cumulative_ratio[-1] - 2 * cumulative_ratio[ends]
                 + self.missing * missing_distance(outcomes))
        first[outcomes == MISSING] = positive @ self.g
        return first - weights @ self.linear_constant + weights @ self.gram @ weights


def fit_weights(gram, linear):
    """Solve the tiny strictly convex problem by enumerating simplex faces."""
    q = gram + PENALTY * np.eye(3)
    b = linear - 2 * PENALTY * IDENTITY
    best = None
    best_loss = np.inf
    lower = np.full(3, FLOOR)
    for size in range(1, 4):
        for face in combinations(range(3), size):
            free = np.array(face)
            hessian = 2 * q[np.ix_(free, free)]
            kkt = np.block([[hessian, np.ones((size, 1))], [np.ones((1, size)), np.zeros((1, 1))]])
            rhs = np.r_[-b[free] - 2 * (q @ lower)[free], 1 - lower.sum()]
            offset = np.linalg.solve(kkt, rhs)[:-1]
            if np.min(offset) < -1e-12:
                continue
            candidate = lower.copy()
            candidate[free] += offset
            loss = candidate @ q @ candidate + b @ candidate
            if loss < best_loss:
                best, best_loss = candidate, loss
    if best is None or abs(best.sum() - 1) > 1e-12:
        raise ArithmeticError('Constrained source fit did not return a probability vector')
    return best


class EndpointFeatures:
    """Projection of exact distance-induced features, with missing represented exactly."""

    def __init__(self, bins=2048):
        self.bins = bins
        self.root_step = np.sqrt(1 / bins)
        grid = np.arange(bins + 1) / bins
        self.a_grid = self.a(grid)
        missing_first = np.diff(self.a_grid) / self.root_step
        self.missing_last = np.sqrt(1 - missing_first @ missing_first)
        self.missing = np.r_[missing_first, self.missing_last]

    @staticmethod
    def a(ratio):
        return (ratio + 1 - missing_distance(ratio)) / 2

    def positions(self, ratios):
        indices = np.minimum((ratios * self.bins).astype(int), self.bins - 1)
        fractions = ratios * self.bins - indices
        a_linear = self.a_grid[indices] + fractions * (self.a_grid[indices + 1] - self.a_grid[indices])
        last = (self.a(ratios) - a_linear) / self.missing_last
        return indices, fractions, last

    def tier_means(self, law):
        indices, fractions, last = self.positions(law.ratios)
        features = []
        for mass in law.tiers:
            histogram = np.bincount(indices, weights=mass, minlength=self.bins)
            fractional = np.bincount(indices, weights=mass * fractions, minlength=self.bins)
            tail = np.cumsum(histogram[::-1])[::-1] - histogram
            positive = np.r_[(tail + fractional) * self.root_step, mass @ last]
            features.append(positive + law.missing * self.missing)
        return np.stack(features)

    def dot_outcomes(self, outcomes, direction):
        outcomes = np.atleast_1d(outcomes)
        dots = np.full(outcomes.shape, self.missing @ direction)
        present = outcomes != MISSING
        indices, fractions, last = self.positions(outcomes[present])
        prefix = np.r_[0, np.cumsum(direction[:-1])] * self.root_step
        dots[present] = (prefix[indices] + self.root_step * fractions * direction[indices]
                         + last * direction[-1])
        return dots


def residual_witness(tier_features, profiles, blocks):
    """Fixed-design residual in the stacked recipient × feature space, by sign and block."""
    means = np.einsum('anb,ansbf->ansf', profiles, tier_features)
    disagreement = means[1] - means[0]
    witness = np.zeros_like(disagreement)
    max_mean = max_ordinary_dot = 0.0
    ranks = {}
    for block in np.unique(blocks):
        idx = np.flatnonzero(blocks == block)
        ranks[str(block)] = []
        for sign in range(2):
            columns = tier_features[0, idx, sign].transpose(0, 2, 1)
            columns = (columns - columns.mean(axis=0)).reshape(-1, 3)
            delta = disagreement[idx, sign]
            centered = (delta - delta.mean(axis=0)).ravel()
            u, singular, _ = np.linalg.svd(columns, full_matrices=False)
            basis = u[:, singular > 1e-10 * singular[0]]
            vector = centered - basis @ (basis.T @ centered)
            w = vector.reshape(delta.shape)
            witness[idx, sign] = w
            max_mean = max(max_mean, float(np.max(np.abs(w.mean(axis=0)))))
            max_ordinary_dot = max(max_ordinary_dot, float(np.max(np.abs(columns.T @ vector))))
            ranks[str(block)].append(int(basis.shape[1]))
    if max_mean > 1e-10 or max_ordinary_dot > 1e-10:
        raise ArithmeticError('Recipient witness is not orthogonal to its nuisance space')
    return means[0], witness, {
        'max_group_mean_coordinate': max_mean, 'max_ordinary_dot': max_ordinary_dot,
        'within_block_ranks_by_sign': ranks,
    }

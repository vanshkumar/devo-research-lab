"""Independent float64, one-thread original-SCR learner and bounded memories.

Source equations: previous task's pinned MIT cbp/gnt/bp/ffnn.
No Torch execution, no access to scoring labels inside learner methods.
"""
from array import array
import math
import random

D, H, PERIOD = 20, 5, 10000
IN_BOUND = math.sqrt(6 / D)


def pack_input(context, fast):
    return sum(int(v) << j for j, v in enumerate(context)) | (fast << 15)


def unpack_input(key):
    return [(key >> j) & 1 for j in range(D)]


def forward(theta, key):
    active = [k for k in range(D) if (key >> k) & 1]
    pre = [theta[j * 21 + 20] + sum(theta[j * 21 + k] for k in active)
           for j in range(H)]
    hidden = [max(z, 0.0) for z in pre]
    return theta[110] + sum(theta[105+j] * hidden[j] for j in range(H)), hidden, active


class Learner:
    def __init__(self, theta, method='sgd', step=.01, replacement_rate=1e-4,
                 decay=.99, maturity=10, seed=781, weight_decay=0., perturb=0.):
        self.theta = theta[:]
        self.method, self.step, self.rate = method, step, replacement_rate
        self.decay, self.maturity = decay, maturity
        self.util, self.mean, self.butil, self.ages = [[0.] * H for _ in range(4)]
        self.accumulated = 0.
        self.rng = random.Random(seed)
        self.event_rng = random.Random(seed + 11)
        self.replacements = 0
        self.gradient_steps = 0
        self.weight_decay, self.perturb = weight_decay, perturb

    def predict(self, key):
        return forward(self.theta, key)[0]

    def learn(self, key, target):
        theta, lr = self.theta, self.step
        pred, features, active = forward(theta, key)
        residual = pred - target
        old_out = theta[105:110]
        if self.weight_decay:
            for k in range(111):
                theta[k] *= 1 - lr * self.weight_decay
        for j in range(H):
            if features[j] > 0:
                delta = 2 * lr * residual * old_out[j]
                offset = 21 * j
                for k in active:
                    theta[offset+k] -= delta
                theta[offset+20] -= delta
            theta[105+j] -= 2 * lr * residual * features[j]
        theta[110] -= 2 * lr * residual
        if self.perturb:
            for k in range(111):
                theta[k] += self.rng.gauss(0., self.perturb)
        self.gradient_steps += 1
        if self.method in ('cbp', 'random'):
            self.renew(features)
        return residual * residual

    def renew(self, features, draw=None, new_incoming=None, random_scores=None):
        if self.rate == 0:
            return []  # literal source: no ages/utility update in this case
        theta, decay = self.theta, self.decay
        for j in range(H):
            self.ages[j] += 1
            correction = 1 - decay ** self.ages[j]
            self.mean[j] = decay * self.mean[j] + (1-decay) * features[j]
            mean = self.mean[j] / correction
            if self.method == 'random':
                utility = 0.
            else:
                norm = sum(abs(theta[21*j+k]) for k in range(D)) / D
                utility = abs(theta[105+j]) * abs(features[j] - mean) / norm
            self.util[j] = decay * self.util[j] + (1-decay) * utility
            self.butil[j] = self.util[j] / correction
        if self.method == 'random':
            scores = random_scores if random_scores is not None else [self.rng.random() for _ in range(H)]
            self.butil[:] = scores
        else:
            scores = self.butil
        eligible = [j for j in range(H) if self.ages[j] > self.maturity]
        if not eligible:
            return []
        number = self.rate * len(eligible)
        self.accumulated += number  # preserved even though accumulate=False
        if number < 1:
            u = self.event_rng.random() if draw is None else draw
            number = int(u <= number)
        else:
            number = int(number)
        chosen = sorted(eligible, key=lambda j: (scores[j], j))[:number]
        for j in chosen:
            # test_features zeroes these BEFORE gen_new_features reads mean.
            self.util[j] = 0.
            self.mean[j] = 0.
        for j in chosen:
            values = (new_incoming[j] if new_incoming is not None else
                      [self.rng.uniform(-IN_BOUND, IN_BOUND) for _ in range(D)])
            for k, value in enumerate(values):
                theta[21*j+k] = value
            theta[21*j+20] = 0.
            theta[110] += theta[105+j] * self.mean[j] / (1-decay**self.ages[j])
            theta[105+j] = 0.
            self.ages[j] = 0.
        self.replacements += len(chosen)
        return chosen


class Reservoir:
    """AlgorithmR over observed examples, including repeated inputs."""
    def __init__(self, capacity=256):
        self.capacity, self.seen = capacity, 0
        self.items = []

    def insert(self, example, draw):
        self.seen += 1
        if len(self.items) < self.capacity:
            self.items.append(example)
        elif draw < self.capacity:
            self.items[draw] = example


class ExactCache:
    """Bounded observed-input LRU with online-mean fallback, no teacher access."""
    def __init__(self, capacity=677):
        self.capacity, self.count, self.total = capacity, 0, 0.
        self.keys, self.labels = array('I'), array('h')
        assert self.keys.itemsize == 4 and self.labels.itemsize == 2
        self.hits = 0

    def predict(self, key, touch=True):
        try:
            index = self.keys.index(key)
        except ValueError:
            index = None
        if index is not None:
            value = self.labels[index]
            if touch:
                self.keys.append(self.keys.pop(index))
                self.labels.append(self.labels.pop(index))
                self.hits += 1
            return value
        return self.total / self.count if self.count else 0.

    def observe(self, key, target):
        self.count += 1
        self.total += target
        try:
            index = self.keys.index(key)
        except ValueError:
            index = None
        if index is not None:
            self.keys.pop(index)
            self.labels.pop(index)
        self.keys.append(key)
        self.labels.append(int(target))
        assert int(target) == target
        if len(self.keys) > self.capacity:
            self.keys.pop(0)
            self.labels.pop(0)


def support_risk(theta, keys, labels):
    return math.fsum((forward(theta, key)[0] - y)**2 for key, y in zip(keys, labels)) / 32


def cache_risk(cache, keys, labels):
    return math.fsum((cache.predict(key, touch=False)-y)**2 for key,y in zip(keys,labels)) / 32

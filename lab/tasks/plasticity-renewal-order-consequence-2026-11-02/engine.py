"""Single-order intervention on the prior independently checked float64 engine.

No author Torch execution. Prior files stay immutable, including pycache.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
PRIOR = Path(__file__).resolve().parent.parent / 'plasticity-retention-protocol-calibration-2026-11-02'
import importlib.util
spec = importlib.util.spec_from_file_location('calibration_engine', PRIOR / 'engine.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
Learner, Reservoir, ExactCache = prior.Learner, prior.Reservoir, prior.ExactCache
forward, pack_input = prior.forward, prior.pack_input
support_risk, cache_risk = prior.support_risk, prior.cache_risk


class OrderLearner(Learner):
    def __init__(self, *args, compensate=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.compensate = compensate
        self.compensation_sum = self.compensation_abs_sum = 0.
        self.compensation_square_sum = 0.
        self.sampled_events = []  # external audit instrumentation, not learner input

    def learn(self, key, target):
        self.diagnostic_key = key
        return super().learn(key, target)

    def renew(self, features, draw=None, new_incoming=None, random_scores=None):
        if self.rate == 0:
            return []
        theta, decay = self.theta, self.decay
        for j in range(5):
            self.ages[j] += 1
            correction = 1 - decay ** self.ages[j]
            self.mean[j] = decay * self.mean[j] + (1-decay) * features[j]
            mean = self.mean[j] / correction
            if self.method == 'random':
                utility = 0.
            else:
                norm = sum(abs(theta[21*j+k]) for k in range(20)) / 20
                utility = abs(theta[105+j]) * abs(features[j] - mean) / norm
            self.util[j] = decay * self.util[j] + (1-decay) * utility
            self.butil[j] = self.util[j] / correction
        if self.method == 'random':
            scores = random_scores if random_scores is not None else [self.rng.random() for _ in range(5)]
            self.butil[:] = scores
        else:
            scores = self.butil
        eligible = [j for j in range(5) if self.ages[j] > self.maturity]
        if not eligible:
            return []
        number = self.rate * len(eligible)
        self.accumulated += number
        if number < 1:
            u = self.event_rng.random() if draw is None else draw
            number = int(u <= number)
        else:
            number = int(number)
        chosen = sorted(eligible, key=lambda j: (scores[j], j))[:number]
        event = None
        if chosen and self.replacements % 128 == 0:
            event = dict(before=theta[:], chosen=chosen[:],
                         old_means=[self.mean[j]/(1-decay**self.ages[j]) for j in chosen],
                         key=getattr(self, 'diagnostic_key', None),
                         gradient_step=self.gradient_steps)
        # The ONLY intervention: postpone resetting mean until compensation.
        for j in chosen:
            self.util[j] = 0.
            if not self.compensate:
                self.mean[j] = 0.
        for j in chosen:
            values = (new_incoming[j] if new_incoming is not None else
                      [self.rng.uniform(-prior.IN_BOUND, prior.IN_BOUND) for _ in range(20)])
            for k, value in enumerate(values):
                theta[21*j+k] = value
            theta[21*j+20] = 0.
            change = theta[105+j] * self.mean[j] / (1-decay**self.ages[j])
            theta[110] += change
            self.compensation_sum += change
            self.compensation_abs_sum += abs(change)
            self.compensation_square_sum += change*change
            self.mean[j] = 0.
            theta[105+j] = 0.
            self.ages[j] = 0.
        self.replacements += len(chosen)
        if event is not None:
            event['after'] = theta[:]
            event['compensate'] = self.compensate
            self.sampled_events.append(event)
        return chosen

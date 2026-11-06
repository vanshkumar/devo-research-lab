"""Causal IBL task generators, reconstructed from pinned historical task code.

Only prefixes may be assimilated.  Forecast calls never take real future
contrasts, choices, outcomes, reward amounts, or trainer decisions.
Choice coding throughout is raw ALF/wheel coding: +1 left decision, -1 right
decision, 0 omission.  Signed contrast is right minus left.  ``side`` is the
physical stimulus side (-1 left, +1 right), even at zero contrast.

The standard trainer's core contrast/correction methods are AST-identical in
iblrig 3.8.1,4.1.3,5.3.1,6.3.1,6.4.0,6.4.2.  Session reward adapts from its own
generated reward history, assuming 25g body weight when unavailable.  Calendar
time, RT-based stopping and operator interventions are deliberately not modeled:
the caller supplies only the number/boundaries of training opportunities.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np


FULL_CONTRASTS = np.array([1.0, 0.5, 0.25, 0.125, 0.0625, 0.0])
EXTERNAL_CONTRASTS = np.array([1.0, 0.25, 0.125, 0.0625])


class VectorTrainer:
    """Independent, vectorized trainer states for Monte Carlo learners.

    Parameters
    ----------
    protocol : ``standard`` or ``external``
    reward_policy : ``adaptive`` (default), ``fixed``
        Standard adaptive reward uses simulated preceding session water/trials
        and the source rule. External always has fixed 3uL reward.
    correction : bool
        False is a predeclared trainer-mismatch sensitivity, not the primary.
    promotion : ``source``, ``fast``, ``slow``
        Source is >40/50 at both sides; sensitivity versions use >35 or >45.
    """

    def __init__(self, n_particles=1, seed=0, protocol="standard", *,
                 reward_ul=3.0, reward_policy="adaptive", weight_g=25.0,
                 min_reward_ul=1.5, correction=True, promotion="source",
                 version="6.4.2"):
        if protocol not in ("standard", "external"):
            raise ValueError(protocol)
        self.n = int(n_particles)
        self.rng = np.random.default_rng(seed)
        self.protocol = protocol
        self.reward_policy = reward_policy
        self.weight_g = float(weight_g)
        self.min_reward_ul = float(min_reward_ul)
        self.correction = bool(correction)
        self.promotion = promotion
        self.version = str(version)
        # Earlier3.x/4.x branches omit the later3uL cap.
        try:
            self.max_reward_ul = 3.0 if int(self.version.split(".")[0]) >= 5 else np.inf
        except (ValueError, IndexError):
            self.max_reward_ul = 3.0
        self.threshold = {"source": 40, "fast": 35, "slow": 45}[promotion]
        self.pool = np.zeros((self.n, 6), dtype=bool)
        self.pool[:, :2] = True
        self.buffer = np.zeros((self.n, 2, 6, 50), dtype=np.int8)
        self.buffer_pos = np.zeros((self.n, 2, 6), dtype=np.int16)
        self.buffer_sum = np.zeros((self.n, 2, 6), dtype=np.int16)
        self.ntrials_125 = np.zeros(self.n, dtype=np.int64)
        self.response_buffer = np.zeros((self.n, 10), dtype=np.int8)
        self.response_pos = 0
        self.response_sum_right = np.zeros(self.n, dtype=np.int16)
        self.reward_ul = np.broadcast_to(reward_ul, (self.n,)).astype(float).copy()
        if protocol == "external":
            self.reward_ul[:] = 3.0
        self.gain = np.full(self.n, 8.0 if protocol == "standard" else 4.0)
        self.session_trials = np.zeros(self.n, dtype=np.int64)
        self.session_water_ul = np.zeros(self.n)
        self.session = 0
        self.pending_repeat = np.zeros(self.n, dtype=bool)
        self.repeat_contrast = np.ones(self.n)
        self.rep_num = np.zeros(self.n, dtype=np.int16)
        self.prob_left = np.full(self.n, 0.5)
        self.current = None

    def clone(self):
        return copy.deepcopy(self)

    def sample(self):
        """Generate the next stimulus from this trainer's simulated history."""
        if self.current is not None:
            raise RuntimeError("observe() is required before the next sample()")
        if self.protocol == "external":
            idx = self.rng.integers(0, 4, self.n)
            contrast = EXTERNAL_CONTRASTS[idx]
            side = np.where(self.rng.random(self.n) < .5, -1, 1)
            repeats = np.zeros(self.n, dtype=bool)
            self.rep_num[:] = 0
        else:
            # Source draws equal mass for each available nonzero contrast and
            # half mass for zero. It does not double zero as in biasedChoice.
            weights = self.pool.astype(float)
            weights[:, -1] *= .5
            cum = np.cumsum(weights, axis=1)
            u = self.rng.random(self.n) * cum[:, -1]
            idx = (u[:, None] >= cum).sum(axis=1)
            contrast = FULL_CONTRASTS[idx]
            repeats = self.pending_repeat.copy()
            contrast[repeats] = self.repeat_contrast[repeats]
            # For adaptive trials, source uses the probability saved by the
            # preceding trial (thus one carryover after correction). For
            # correction, side is decided by Normal(recent wheel-right rate,.5).
            side = np.where(self.rng.random(self.n) < self.prob_left, -1, 1)
            right_rate = self.response_sum_right / 10.0
            correction_side = np.where(self.rng.normal(right_rate, .5) < .5, -1, 1)
            side[repeats] = correction_side[repeats]
            self.prob_left[:] = .5
            self.prob_left[repeats] = 1.0 - right_rate[repeats]
            self.rep_num = np.where(repeats, self.rep_num + 1, 0).astype(np.int16)
        self.current = {"signed_contrast": contrast * side, "contrast": contrast,
                        "side": side.astype(np.int8),
                        "correct_choice": (-side).astype(np.int8),
                        "reward_ul": self.reward_ul.copy(),
                        "rep_num": self.rep_num.copy(),
                        "is_repeat": repeats,
                        "gain": self.gain.copy()}
        self.current["contrastLeft"] = np.where(side < 0, contrast, np.nan)
        self.current["contrastRight"] = np.where(side > 0, contrast, np.nan)
        return {k: v.copy() for k, v in self.current.items()}

    def observe(self, choice):
        """Compute reward from own generated stimulus/action, then update."""
        if self.current is None:
            raise RuntimeError("sample() is required before observe()")
        choice = np.broadcast_to(np.asarray(choice, dtype=np.int8), (self.n,))
        if not np.isin(choice, [-1, 0, 1]).all():
            raise ValueError("Choices must use raw ALF -1,0,+1 coding")
        correct = choice == self.current["correct_choice"]
        reward = correct.astype(float) * self.reward_ul
        feedback = np.where(correct, 1, -1).astype(np.int8)
        self._record(self.current["contrast"], self.current["side"], choice,
                     correct, self.current["is_repeat"], reward)
        self.current = None
        return {"feedbackType": feedback, "rewardVolume": reward,
                "correct": correct}

    def _record(self, contrast, side, choice, correct, repeats, reward):
        self.session_trials += 1
        self.session_water_ul += reward
        # Response buffer stores wheel sign (ALF sign), and source computes
        # wheel-right rate using exactly 10 slots including initial zeros.
        old = self.response_buffer[:, self.response_pos]
        self.response_sum_right += (choice == 1).astype(np.int16) - (old == 1)
        self.response_buffer[:, self.response_pos] = choice
        self.response_pos = (self.response_pos + 1) % 10
        if self.protocol == "external":
            return
        adaptive = ~repeats
        ii = np.flatnonzero(adaptive)
        si = (side[ii] > 0).astype(np.int64)
        ci = np.abs(contrast[ii, None] - FULL_CONTRASTS[None, :]).argmin(axis=1)
        bp = self.buffer_pos[ii, si, ci]
        old_correct = self.buffer[ii, si, ci, bp]
        self.buffer_sum[ii, si, ci] += correct[ii].astype(np.int16) - old_correct
        self.buffer[ii, si, ci, bp] = correct[ii]
        self.buffer_pos[ii, si, ci] = (bp + 1) % 50
        self.ntrials_125[ii] += self.pool[ii, 3].astype(np.int64)
        passed = (self.buffer_sum > self.threshold).all(axis=1)
        self.pool[ii, 2] |= passed[ii, 0] & passed[ii, 1]
        self.pool[ii, 3] |= passed[ii, 2]
        self.pool[ii, 4] |= self.ntrials_125[ii] >= 200
        self.pool[ii, 5] |= self.ntrials_125[ii] >= 400
        self.pool[ii, 1] &= self.ntrials_125[ii] < 600
        self.pending_repeat = (~correct) & (contrast >= .5) & self.correction
        self.repeat_contrast[:] = contrast

    def new_session(self):
        """Apply own previous-session reward/gain rules; reset correction."""
        if self.current is not None:
            raise RuntimeError("Cannot cross boundary with an unobserved trial")
        if self.protocol == "standard":
            enough = self.session_trials >= 200
            if self.reward_policy == "adaptive":
                out = self.reward_ul - .1 * enough
                out = np.maximum(out, self.min_reward_ul)
                # Source weight adjustment overrides the trial-count decrease.
                short_water = self.session_water_ul / 1000 < self.weight_g / 25
                out[short_water] = self.reward_ul[short_water] + .1
                self.reward_ul = np.minimum(out, self.max_reward_ul)
            self.gain = np.where(enough, 4.0, 8.0)
        self.session += 1
        self.session_trials[:] = 0
        self.session_water_ul[:] = 0
        self.response_buffer[:] = 0
        self.response_sum_right[:] = 0
        self.response_pos = 0
        self.pending_repeat[:] = False
        self.rep_num[:] = 0
        self.prob_left[:] = .5

    @classmethod
    def from_prefix(cls, prefix, n_particles=1, seed=0, protocol="standard", **kwargs):
        """Reconstruct only the permitted prefix, then copy state to particles.

        Accepts source-column names or data_io aliases contrast_left/right,
        feedback, reward, session_index, rep_num. If correction flags are not
        indexed, the most likely branch is reconstructed causally: a high-
        contrast error implies a next correction unless a new session begins.
        This uncertainty is tested by ``correction=False``. Missing biological
        prehistory is not invented. Observed prefix contrast pools are included
        even when their introduction predates the deposited history.
        """
        def col(*names, default=None):
            for name in names:
                if name in prefix:
                    return np.asarray(prefix[name])
            return default
        choice = col("choice")
        if choice is None:
            raise ValueError("prefix choice is required")
        n = len(choice)
        left = col("contrastLeft", "contrast_left")
        right = col("contrastRight", "contrast_right")
        x = col("signed_contrast", "x")
        if left is None or right is None:
            if x is None:
                raise ValueError("prefix contrasts or signed contrast required")
            left = np.where(x <= 0, -x, np.nan)
            right = np.where(x > 0, x, np.nan)
        feedback = col("feedbackType", "feedback", default=np.zeros(n))
        reward = col("rewardVolume", "reward", default=np.zeros(n))
        session = col("session", "session_index", default=np.zeros(n, dtype=int))
        rep = col("repNum", "rep_num", default=None)
        if rep is not None and not np.isfinite(rep).all():
            rep = None
        tr = cls(1, seed, protocol, **kwargs)
        for t in range(n):
            if t and session[t] != session[t-1]:
                tr.new_session()
            l = float(left[t]); r = float(right[t])
            side = -1 if np.isfinite(l) and (not np.isfinite(r) or l >= r) else 1
            con = max(0 if not np.isfinite(l) else l, 0 if not np.isfinite(r) else r)
            if tr.protocol == "standard":
                j = int(np.abs(FULL_CONTRASTS-con).argmin())
                tr.pool[0, :max(j+1, 2)] = True
                # .5 may disappear only after enough simulated/inferred125.
            is_repeat = bool(rep[t] > 0) if rep is not None else bool(tr.pending_repeat[0])
            pretrial_wheel_right_rate = tr.response_sum_right[0] / 10.0
            if np.isfinite(reward[t]) and reward[t] > 0:
                tr.reward_ul[:] = float(reward[t])
            raw = int(choice[t])
            corr = bool(feedback[t] > 0)
            tr._record(np.array([con]), np.array([side]), np.array([raw]),
                       np.array([corr]), np.array([is_repeat]), np.array([max(0, reward[t])]))
            # Saved probability was computed from the pretrial response
            # buffer, so retain that state for the first generated adaptive
            # trial following a correction.
            tr.prob_left[:] = 1-pretrial_wheel_right_rate if is_repeat else .5
            tr.rep_num[:] = int(rep[t]) if rep is not None else (tr.rep_num[0]+1 if is_repeat else 0)
        # Replicate single known prefix trainer state; future RNG is independent.
        for key, val in list(vars(tr).items()):
            if isinstance(val, np.ndarray) and val.shape and val.shape[0] == 1:
                setattr(tr, key, np.repeat(val, int(n_particles), axis=0))
        tr.n = int(n_particles)
        tr.rng = np.random.default_rng(seed)
        return tr

    def state_summary(self):
        return {"protocol": self.protocol, "n_particles": self.n,
                "pool": self.pool.tolist(), "ntrials_125": self.ntrials_125.tolist(),
                "reward_ul": self.reward_ul.tolist(), "gain": self.gain.tolist(),
                "session_trials": self.session_trials.tolist(),
                "session": self.session, "correction": self.correction,
                "reward_policy": self.reward_policy, "promotion": self.promotion,
                "version": self.version}


def trainer_self_test(output=None):
    """Known answers and causal/version-envelope checks without real outcomes."""
    results = {}
    a = VectorTrainer(128, 817, "standard")
    b = VectorTrainer(128, 817, "standard")
    exact = True
    introduced = []
    for t in range(2200):
        sa = a.sample(); sb = b.sample()
        exact &= all(np.array_equal(sa[k], sb[k], equal_nan=True) for k in sa)
        a.observe(sa["correct_choice"]); b.observe(sb["correct_choice"])
        if t % 200 == 0:
            introduced.append([t, a.pool.sum(axis=0).tolist()])
    assert exact
    assert a.pool[:, [0,2,3,4,5]].all() and not a.pool[:, 1].any()
    results["same_seed_exact"] = bool(exact)
    results["perfect_learner_curriculum_progression"] = introduced
    c = VectorTrainer(128, 817, "standard")
    for t in range(400):
        s = c.sample(); out = c.observe(np.zeros(128, dtype=int))
        assert (out["feedbackType"] == -1).all() and (out["rewardVolume"] == 0).all()
    assert c.pool[:, :2].all() and not c.pool[:, 2:].any()
    results["omissions_no_reward_no_promotion"] = True
    assert c.pending_repeat.all()
    c.new_session(); assert not c.pending_repeat.any()
    results["correction_resets_at_session"] = True
    d = VectorTrainer(4096, 175, "external")
    s = d.sample(); assert set(np.unique(s["contrast"])) == set(EXTERNAL_CONTRASTS)
    out = d.observe(s["correct_choice"])
    assert (out["rewardVolume"] == 3).all()
    results["external_contrasts"] = np.unique(s["contrast"]).tolist()
    results["external_p_right"] = float((s["side"] == 1).mean())
    results["external_omissions_errors_unrewarded"] = True
    # Mechanism discriminant: perfect vs omission histories change the trainer.
    results["causal_performance_changes_curriculum"] = bool(not np.array_equal(a.pool, c.pool))
    # Exercise exact original update code, extracted from pinned bytes without
    # importing its hardware package. This is a numerical recurrence audit.
    import ast
    import types
    import scipy.stats as st
    source = Path(__file__).resolve().parents[1] / "sources/trainer/6.4.2_trial_params.py"
    tree = ast.parse(source.read_text())
    node = next(v for v in tree.body if isinstance(v, ast.ClassDef) and v.name == "AdaptiveContrast")
    scope = {"np": np, "st": st}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), scope)
    sph = types.SimpleNamespace(ADAPTIVE_CONTRAST=True, CONTRAST_SET=FULL_CONTRASTS.tolist(),
          AC_INIT_CONTRASTS=[1., .5], AC_BUFFER_SIZE=50, AC_PERF_CRIT=.7,
          AC_NTRIALS_TO_SIX=200, AC_NTRIALS_TO_ZERO=400,
          AC_NTRIALS_TO_REMOVE_50=600, PREVIOUS_DATA_FILE=None, LAST_TRIAL_DATA=None)
    original = scope["AdaptiveContrast"](sph)
    ours = VectorTrainer(1, 81, "standard", correction=False)
    delta = 0
    for t in range(1800):
        s = ours.sample()
        # A known competent learner followed by stochastic correct/error data.
        raw = s["correct_choice"] if t < 800 or t % 9 else -s["correct_choice"]
        good = bool(raw[0] == s["correct_choice"][0])
        original.value = float(s["contrast"][0])
        original.trial_completed(good)
        original._update_buffer(int(s["side"][0]))
        original._update_contrast_set()
        ours.observe(raw)
        assert original.contrast_set == FULL_CONTRASTS[ours.pool[0]].tolist()
        assert original.ntrials_125 == int(ours.ntrials_125[0])
        if .5 in original.contrast_set:
            original_sum = np.asarray(original.buffer).sum(axis=1)
            delta = max(delta, int(np.abs(original_sum - ours.buffer_sum[0]).max()))
    assert delta == 0
    results["original_6_4_2_recurrence_steps"] = 1800
    results["original_recurrence_max_buffer_error"] = delta
    results["original_binomial_threshold"] = int(original.perf_crit)
    trace = {k: [] for k in ["contrastLeft", "contrastRight", "choice", "feedbackType", "rewardVolume", "session", "repNum"]}
    e = VectorTrainer(1, 377, "standard")
    rand = np.random.default_rng(954)
    for t in range(700):
        if t in [200, 430]:
            e.new_session()
        s = e.sample()
        raw = np.where(rand.random(1) < .8, s["correct_choice"], -s["correct_choice"])
        out = e.observe(raw)
        for k in ["contrastLeft", "contrastRight"]:
            trace[k].append(s[k][0])
        trace["choice"].append(raw[0]); trace["feedbackType"].append(out["feedbackType"][0])
        trace["rewardVolume"].append(out["rewardVolume"][0]); trace["session"].append(e.session)
        trace["repNum"].append(s["rep_num"][0])
    recon = VectorTrainer.from_prefix({k: np.array(v) for k,v in trace.items()}, 1, 377)
    keys = ["pool", "buffer_sum", "ntrials_125", "pending_repeat", "response_buffer", "session_trials", "session_water_ul", "reward_ul", "gain", "prob_left"]
    results["prefix_reconstruction_state_matches"] = {k: bool(np.array_equal(getattr(e,k), getattr(recon,k))) for k in keys}
    assert all(results["prefix_reconstruction_state_matches"].values())
    if output:
        Path(output).write_text(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    print(json.dumps(trainer_self_test(args.output), indent=2))

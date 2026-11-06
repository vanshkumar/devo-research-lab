"""Outcome-blind generative challenges for target-event carryover.

All angles are degrees and y is compensation-positive. c[r] is the newly
programmed clamp on trial r, j[r] is the spatial target jump. y[r] is read out
before that trial's learning update. No CSV or empirical outcomes are loaded.
See audits/recovery_design/GENERATOR_DESIGN.md for scope and truth definitions.
"""
from typing import Optional
import numpy as np

KINDS = ('gain_only', 'two_timescale', 'retention', 'perceived_error',
         'expression_current', 'expression_next', 'rebound', 'online',
         'expression_storage_equivalent')


def _ar(innovations, phi, stationary_sd):
    x = np.zeros(len(innovations), dtype=float)
    if len(x):
        x[0] = stationary_sd * innovations[0]
    innovation_sd = stationary_sd * np.sqrt(1.0 - phi * phi)
    for r in range(1, len(x)):
        x[r] = phi * x[r-1] + innovation_sd * innovations[r]
    return x


def _parameters(kind, retentions, gains):
    a = np.asarray(retentions, dtype=float).copy()
    b = np.asarray(gains, dtype=float).copy()
    if a.shape != (2,) or b.shape != (2,):
        raise ValueError('retentions and gains must each have two components')
    if not np.all((a > 0) & (a < 1)) or not np.all(b >= 0) or b[0] == 0:
        raise ValueError('Require 0<a<1, b>=0 and nonzero fast gain')
    if kind == 'gain_only':
        a[:] = a[0]
        b[:] = (float(b.sum()), 0.0)
    return a, b


def _calibration(effect, a, b):
    # The index event changes the fast state transition by additive delta.
    # One isolated preceding +4-degree/no-jump clamp produces x_fast=b[0].
    # At readout h=1..5 its jump-minus-stationary effect is
    # delta*b[0]*a[0]**(h-1). This is independent of the slow component.
    geometric_mean = float(np.mean(a[0] ** np.arange(5)))
    delta = float(effect) / (float(b[0]) * geometric_mean)
    return delta, geometric_mean


def _inputs(c, j, b, gain_jump, target_gain):
    event = (j != 0).astype(float)
    # Flexible cell gains: a target jump can change current-clamp learning;
    # signed alignment supplies additional nonseparable clamp/jump geometry.
    aligned = np.sign(c * j)
    current_multiplier = 1.0 - gain_jump * event + 0.10 * aligned
    inp = (c[:, None] / 4.0) * b[None, :] * current_multiplier[:, None]
    # Independent target-error response, including c=0 jump events.
    inp[:, 0] += target_gain * j
    return inp


def generate(c, j, seed=0, kind='two_timescale', noise_sd=2.5, effect=0.0,
             omission_rate=0.0, retentions=(0.65, 0.97), gains=(0.65, 0.20),
             gain_jump=0.40, target_gain=0.025, direct_jump=0.035,
             direct_clamp=-0.025, motor_phi=0.70, observation_phi=0.25,
             drift_scale=0.60, process_sd=0.0, person_scale=1.0,
             empirical_mask: Optional[np.ndarray]=None,
             zero_clamp_only=True):
    """Return a simulated chronological series on the supplied schedule.

    effect: signed average 1..5 impulse modulation in degrees for `retention`
      and `perceived_error`; for expression alternatives this calibrates the
      comparator retention effect so their h=1 response can be matched.
    noise_sd: stationary SD of motor+observation noise (drift is additional).
    omission_rate: independent missing readouts, never deletion of schedule.
    empirical_mask: optional mask supplied externally; False becomes NaN.
    person_scale: multiplies learning gains and target input. `effect` scales
      with person_scale, so it represents the population/reference person.
    zero_clamp_only: event modifies propagation only when c==0 by default;
      set False for a separately declared all-clamp transfer law.

    A per-event fast retention above one is allowed: a brief amplification is
    not an unstable trajectory. The realized mean log transition multiplier
    and maximum single-step multiplier are returned. Invalid sign-changing
    transition or realized noncontracting long-run sequences raise ValueError.
    """
    c, j = np.asarray(c, dtype=float), np.asarray(j, dtype=float)
    if c.ndim != 1 or c.shape != j.shape or not np.isfinite(c).all() or not np.isfinite(j).all():
        raise ValueError('c/j must be finite same-length one-dimensional inputs')
    if kind not in KINDS:
        raise ValueError('Unknown kind: ' + str(kind))
    if noise_sd < 0 or not 0 <= omission_rate < 1 or not 0 < person_scale:
        raise ValueError('Invalid noise, omissions or person scale')
    if not 0 <= motor_phi < 1 or not 0 <= observation_phi < 1:
        raise ValueError('AR coefficients must be in [0,1)')
    a, b = _parameters(kind, retentions, gains)
    delta, gm = _calibration(effect, a, b)
    n = len(c)
    event = (j != 0) & ((c == 0) if zero_clamp_only else True)
    transition = a[0] + delta * event.astype(float)
    is_change = kind in ('retention', 'perceived_error', 'expression_storage_equivalent')
    if is_change and np.any(transition < 0):
        raise ValueError('Requested negative effect creates sign-reversing retention; reduce effect or change declared parameters')
    mean_log = float(np.mean(np.log(np.maximum(transition, 1e-300)))) if n else float('nan')
    if is_change and n >= 100 and mean_log >= 0:
        raise ValueError('Requested propagation effect is not contracting on supplied schedule')
    rng = np.random.default_rng(seed)
    # Always consume the same independent streams, permitting exact coupled
    # generator comparisons under the same seed and parameter values.
    innovations = rng.standard_normal((n, 3))
    phase = float(rng.uniform(0, 2*np.pi))
    slope = float(rng.normal())
    omissions = rng.uniform(size=n)
    inp = _inputs(c, j, b * person_scale, gain_jump, target_gain * person_scale)
    state = np.zeros((n+1, 2), dtype=float)
    expression = np.zeros(n+1, dtype=float)
    clean = np.zeros(n, dtype=float)
    for r in range(n):
        x = state[r]
        online = direct_jump*j[r] + direct_clamp*c[r]
        if kind == 'online':
            online += 0.20 * (j[r] != 0) * x.sum()
            online += 0.04 * c[r] * (j[r] != 0)
        readout_expression = 0.0
        if kind == 'expression_current':
            readout_expression = delta * event[r] * x[0]
        elif kind in ('expression_next', 'rebound'):
            # Event at t changes the t+1 expression but never stored state.
            if r >= 1:
                readout_expression += delta * event[r-1] * state[r-1, 0]
            if kind == 'rebound' and r >= 2:
                readout_expression -= delta * event[r-2] * state[r-2, 0]
        elif kind == 'expression_storage_equivalent':
            readout_expression = expression[r]
        clean[r] = x.sum() + online + readout_expression
        next_x = a*x + inp[r]
        if kind == 'retention':
            next_x[0] += delta * event[r] * x[0]
        elif kind == 'perceived_error':
            # The fixed-retention account adds a state-dependent correction
            # from a fresh internally perceived error, e=-k*E*x_fast. With
            # k=-delta/b_fast, b_fast*e equals delta*E*x_fast exactly.
            k = -delta / (b[0] * person_scale)
            internal_error = -k * event[r] * x[0]
            next_x[0] += (b[0] * person_scale) * internal_error
        elif kind == 'expression_storage_equivalent':
            # Storage is fixed-retention, but a dynamic expression state is
            # sufficient to reproduce every endpoint of the retention model.
            expression[r+1] = (a[0]+delta*event[r])*expression[r] + delta*event[r]*x[0]
        next_x[0] += process_sd*innovations[r,2]
        state[r+1] = next_x
    # Independent colored motor/observation components. Their variances sum
    # to noise_sd**2, before optional independent drift and process noise.
    motor = _ar(innovations[:,0], motor_phi, noise_sd*np.sqrt(0.35))
    observation = _ar(innovations[:,1], observation_phi, noise_sd*np.sqrt(0.65))
    t = np.arange(n, dtype=float)
    drift = drift_scale * (np.sin(2*np.pi*t/260.0+phase) + slope*(t/max(n-1,1)-0.5))
    observed_mask = omissions >= omission_rate
    if empirical_mask is not None:
        mask=np.asarray(empirical_mask,dtype=bool)
        if mask.shape != c.shape:
            raise ValueError('empirical_mask must match c/j')
        observed_mask &= mask
    y = clean + motor + observation + drift
    y[~observed_mask] = np.nan
    h = np.arange(5)
    retention_curve = delta*b[0]*person_scale*a[0]**h
    if kind in ('retention','perceived_error','expression_storage_equivalent'):
        impulse_curve = retention_curve
    elif kind == 'expression_next':
        impulse_curve = np.array([retention_curve[0],0.,0.,0.,0.])
    elif kind == 'rebound':
        impulse_curve = np.array([retention_curve[0],-retention_curve[0],0.,0.,0.])
    else:
        impulse_curve = np.zeros(5)
    return dict(y=y, clean=clean, state=state[:-1], final_state=state[-1],
                latent=state[:-1].sum(axis=1), expression=expression[:-1],
                noise=motor+observation, drift=drift, observed_mask=observed_mask,
                truth=dict(kind=kind, reference_effect=float(effect),
                           impulse_curve=impulse_curve.tolist(),
                           impulse_theta=float(np.mean(impulse_curve)),
                           delta_retention=float(delta), retentions=a.tolist(),
                           gains=(b*person_scale).tolist(),
                           event_fraction=float(event.mean()) if n else None,
                           mean_log_fast_transition=mean_log,
                           max_fast_transition=float(np.max(transition)) if n else None,
                           zero_clamp_only=bool(zero_clamp_only),
                           note='Isolated impulse truth is not the finite-schedule regression projection; repeated events and nuisance projection may change that estimand.'))


def impulse_check(kind='retention', effect=0.2, **kwargs):
    """Direct four-way counterfactual isolates the preceding clamp component.

    index t=2; old input at t-1=1; future readouts t+1..t+5 are positions3..7.
    Both index/no-index trials have no later inputs; old input contrast is +4
    versus 0, at no preceding target jump. All noise/drift are disabled.
    """
    params=dict(noise_sd=0,drift_scale=0,process_sd=0,omission_rate=0)
    params.update(kwargs)
    curves=[]
    for old in (4.,0.):
        for jump in (4.,0.):
            c=np.zeros(9);j=np.zeros(9);c[1]=old;j[2]=jump
            curves.append(generate(c,j,seed=0,kind=kind,effect=effect,**params)['clean'][3:8])
    curve=curves[0]-curves[1]-curves[2]+curves[3]
    return dict(curve=curve.tolist(),theta=float(curve.mean()))


if __name__ == '__main__':
    import json
    results={k:impulse_check(k,effect=0.2) for k in KINDS}
    assert np.max(np.abs(np.array(results['retention']['curve'])-np.array(results['perceived_error']['curve'])))<1e-12
    assert abs(results['retention']['theta']-0.2)<1e-12
    assert abs(results['rebound']['theta'])<1e-12
    print(json.dumps(results,indent=2))

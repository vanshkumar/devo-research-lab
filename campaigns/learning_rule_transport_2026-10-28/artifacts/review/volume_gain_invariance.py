"""Synthetic witness: reward-amount metadata is not a behavioral input here."""
import json
from pathlib import Path
import sys
import numpy as np

C = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(C/'code'))
from learning_models import load_model
from baselines import load_bank
from rollout import autonomous
from trainer import VectorTrainer

n = 1000
side = np.where(np.arange(n) % 2, -1, 1)
prefix = dict(contrastLeft=np.where(side<0, 1., np.nan),
              contrastRight=np.where(side>0, 1., np.nan),
              choice=-side, feedbackType=np.ones(n), rewardVolume=np.full(n, 3.),
              session_index=np.arange(n)//500,
              session_start=np.arange(n)%500==0, repNum=np.zeros(n))
starts = np.arange(1000)%500==0
bank = load_bank(C/'artifacts/baselines/nested_growth_bank.npz')
results = []
for name, filename in [('dnnglm32','dnnglm32_nested_best.npz'),
                       ('reinforce','reinforce_nested_stable.npz')]:
    model = load_model(C/'artifacts/models'/filename)
    a = autonomous(model, prefix, starts, bank, n_particles=32, seed=761,
                   trainer_options=dict(version='4.1.3', reward_policy='adaptive', weight_g=25))
    b = autonomous(model, prefix, starts, bank, n_particles=32, seed=761,
                   trainer_options=dict(version='4.1.3', reward_policy='fixed', weight_g=25))
    results.append(dict(model=name,
                        sampled_curves_exactly_equal=bool(np.array_equal(a['samples'],b['samples'])),
                        learned_weights_exactly_equal=bool(np.array_equal(a['weights'],b['weights'])),
                        promotion_pools_exactly_equal=bool(np.array_equal(a['pool_fraction'],b['pool_fraction']))))

traces = {}
for policy in ['adaptive','fixed']:
    tr = VectorTrainer.from_prefix(prefix, 1, 761, version='4.1.3', reward_policy=policy)
    tr.new_session()
    traces[policy] = dict(reward_ul=tr.reward_ul.tolist(), gain=tr.gain.tolist())

out = dict(scope='synthetic1000-trialprefix and1000-trialfuture; frozen development bank/model consumed; no raw animal or external outcome reads',
           proof='Reward volume and wheel gain are emitted metadata. Actor update consumes feedbackType only; shared engagement ignores volume/gain. Trainer amounts do not drive contrast promotion.',
           first_future_session_metadata=traces, exact_behavioral_invariance=results,
           implication='This validates implementation invariance, not biological robustness to volume/gain effects.')
(Path(__file__).resolve().parent/'VOLUME_GAIN_INVARIANCE.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

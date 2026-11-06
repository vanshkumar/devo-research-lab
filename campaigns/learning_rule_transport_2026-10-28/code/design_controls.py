"""Independent known-answer checks for score/coding/causal alignment.

Uses synthetic arrays only. Never imports data_io or reads animal outcomes.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from evaluation import marginal_crps, score
from learning_models import LearningModel
from rollout import trajectory_summary


def run():
    rng=np.random.default_rng(618)
    draws=rng.normal(size=(37,6,4));observed=rng.normal(size=(6,4))
    first=np.mean(np.abs(draws-observed),axis=0)
    # Independent quadratic implementation of the ordered-pair U-statistic.
    pair=np.zeros((6,4))
    for i in range(len(draws)):
        for j in range(len(draws)):
            if i!=j:pair+=np.abs(draws[i]-draws[j])
    brute=first-pair/(2*len(draws)*(len(draws)-1))
    error=float(np.max(np.abs(marginal_crps(draws,observed)-brute)))
    assert error<1e-13

    degenerate=np.broadcast_to(observed,(19,6,4)).copy()
    scored=score(degenerate,observed)
    assert abs(scored['crps'])<1e-13 and abs(scored['mae'])<1e-13 and abs(scored['energy'])<1e-13
    nonfinite=draws.copy();nonfinite[0,0,0]=np.nan
    rejected=False
    try:score(nonfinite,observed)
    except FloatingPointError:rejected=True
    assert rejected

    # Exact count-based witness of all four observable metric definitions.
    x=np.r_[np.full(250,-1.),np.full(250,1.)]
    c=np.r_[np.full(200,1),np.zeros(50),np.full(150,-1),np.full(75,1),np.zeros(25)]
    summary,denom=trajectory_summary(x,c)
    target=np.array([.8,.6,.3,.15])
    assert np.allclose(summary[0,0],target,rtol=0,atol=1e-15)
    assert np.array_equal(denom[0,0],np.array([250,250,500,500]))

    # Current observations can alter later probabilities, never current ones.
    s=rng.choice([-1.,-.5,.5,1.],100)
    raw=rng.choice([-1,1],100)
    r=(raw==-np.sign(s)).astype(float)
    d=dict(contrastLeft=np.maximum(-s,0),contrastRight=np.maximum(s,0),choice=raw.copy(),feedbackType=r.copy())
    model=LearningModel('reinforce',dict(alpha=np.array([.02,.02,.01]),baseline=np.full(3,-.2)))
    p,ws,end=model.sequence(d,np.zeros(3))
    changed={k:v.copy() for k,v in d.items()}
    changed['choice'][31]*=-1;changed['feedbackType'][31]=1-changed['feedbackType'][31]
    q,_,_=model.sequence(changed,np.zeros(3))
    assert np.array_equal(p[:32],q[:32]) and not np.array_equal(p[32:],q[32:])
    omitted={k:v.copy() for k,v in d.items()};omitted['choice'][31]=0
    _,womit,_=model.sequence(omitted,np.zeros(3))
    assert np.array_equal(womit[31],womit[32])
    return dict(seed=618,empirical_outcomes_opened=False,crps_vs_ordered_pair_max_error=error,
                degenerate_forecast_crps=scored['crps'],degenerate_forecast_energy=scored['energy'],
                nonfinite_forecast_rejected=rejected,known_observable_summary=summary[0,0].tolist(),
                current_choice_reward_cannot_change_current_probability=True,
                omission_skips_binary_update=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output');args=p.parse_args()
    result=run();txt=json.dumps(result,indent=2)
    if args.output:Path(args.output).write_text(txt+'\n')
    print(txt)

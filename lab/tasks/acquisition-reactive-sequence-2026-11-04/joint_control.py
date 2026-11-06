"""Known-answer late trajectory effect with identical first probabilities."""
from itertools import product

import numpy as np

from screen import center, collapse, decisions, kld, serialize
from source import check, save, utc


def laws():
    x = np.array([1,-.5,-1,.5,-1,1])
    paths = np.array(list(product([1,0,-1],repeat=len(x))))
    is_correct = paths == -np.sign(x)
    out = []
    for arm_effect in (-.12,.12,0.):
        current = np.full(len(paths),1.)
        for t in range(len(x)):
            p = .65 if t==0 else .54+.19*is_correct[:,t-1]+arm_effect
            q = .015
            current *= np.where(paths[:,t]==0,q,(1-q)*np.where(is_correct[:,t],p,1-p))
        out.append(current)
    p,q = np.array(out[:2]),np.tile(out[2],(2,1))
    check(np.max(np.abs(collapse(p)-collapse(q)))<1e-14,'Planted effect must be later only')
    return p,q,is_correct


def main():
    p,q,correct = laws()
    pc,qc = center(p,q)
    effect = ((p[1]-p[0])@correct.mean(1)).item()
    d = {}
    for n in (64,240):
        # One categorical path per learner for calibration and fresh evaluation.
        d[str(n)] = dict(raw_joint=decisions(p,q,n,279662+n),centered_joint=decisions(pc,qc,n,769661+n),
                         first_null=decisions(collapse(pc),collapse(qc),n,852670+n),
                         joint_null=decisions(qc,qc,n,819822+n))
    save('JOINT_CONTROL.json',serialize(dict(utc=utc(),plant_mean_correct_arm_effect=effect,
          centered_kl_per_learner=[kld(pc,qc),kld(qc,pc)],decisions=d)))
    print('Completed planted later effect and null',effect,flush=True)


if __name__=='__main__':
    main()

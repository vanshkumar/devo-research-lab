"""Independent exact second-moment control, using a finite signed distribution."""
from fractions import Fraction as F
import itertools,json,pathlib
H=pathlib.Path(__file__).resolve().parent
checks=[]
for pi,rho,fp in itertools.product([F(1,20),F(1,5),F(1,2)],[F(-1,2),F(0),F(4,5)],[F(0),F(1,100),F(1,20),F(1,5),F(1)]):
    xy=F(0);xx=F(0);mass=F(0)
    for self_mode,o,u in itertools.product([True,False],[-1,1],[-1,1]):
        prob=(pi if self_mode else 1-pi)/4
        accept=F(9,10) if self_mode else fp
        # Noise coefficient need not be sqrt(1-rho²): independent zero-mean
        # noise cancels in E[xy]; set coefficient1 to keep exact rationals.
        own=F(o) if self_mode else rho*o+u
        xy+=prob*accept*o*own;xx+=prob*accept*o*o;mass+=prob*accept
    gain=xy/xx
    formula=(pi*F(9,10)+(1-pi)*fp*rho)/(pi*F(9,10)+(1-pi)*fp)
    assert gain==formula
    checks.append(dict(pi=float(pi),rho=float(rho),fp=float(fp),gain=float(gain)))
pi=F(1,20);tpr=F(9,10);threshold=pi*tpr*F(1,9)/(1-pi)
assert threshold==F(1,190)
result=dict(exact_moment_cases=len(checks),all_equal=True,false_update_upper_bound_for_gain_above_09_when_pi_005_rho0=float(threshold),bound_exact=str(threshold),conditions='TPR=.9, common shared scalar code, zero-mean independent context noise; no biological rates estimated.')
(H/'analytical_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

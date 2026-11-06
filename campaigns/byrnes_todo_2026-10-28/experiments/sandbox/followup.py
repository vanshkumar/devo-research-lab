"""Exploratory magnitude shift, chosen after the finite enumeration result."""
import json,pathlib,itertools
H=pathlib.Path(__file__).resolve().parent
d=json.loads((H/'summary.json').read_text())
passed=d['passing_weights']
# Independent analytic bound: minimum welfare gap is1, maximum summed proxy
# advantage is2*(p+a); with integer weights summing10 there is no boundary tie.
all_weights=[(w,p,10-w-p) for w in range(11) for p in range(11-w)]
analytic=[list(w) for w in all_weights if w[0]>2*(w[1]+w[2])]
assert analytic==passed
results=[]
for w,p,a in passed:
    first=None
    for magnitude in range(1,101):
        # Welfare action: [1,0,0]; proxy action: [0,m,m]. Strict comparison
        # excludes dependence on the original tie-break rule.
        if magnitude*(p+a)>w:
            first=magnitude;break
    if p+a:assert first==w//(p+a)+1
    else:assert first is None
    results.append(dict(weights=[w,p,a],first_strict_welfare_sacrifice_magnitude=first))
assert sum(r['first_strict_welfare_sacrifice_magnitude'] is not None for r in results)==9
result=dict(analytic_finite_bound_passed=True,shift=results,passing_before=10,passing_after=1,max_magnitude_tested=100,scope='Chosen diagnostic shift; does not test deceptive/adaptive policies, learning, biological value grounding, or general AGI safety.')
(H/'followup_summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

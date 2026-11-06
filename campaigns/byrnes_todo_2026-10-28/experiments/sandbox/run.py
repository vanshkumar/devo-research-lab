"""Exhaustive finite value-proxy sandbox example; no model API or real agents."""
import pathlib,itertools,json,csv
H=pathlib.Path(__file__).parent
weights=[(w,p,10-w-p) for w in range(11) for p in range(11-w)]
outcomes=list(itertools.product([-1,0,1],repeat=3));menus=list(itertools.combinations(outcomes,2))
def utility(w,x):return sum(a*b for a,b in zip(w,x))
def choice(w,menu):return max(range(len(menu)),key=lambda j:utility(w,menu[j]))
# Distinct maxima: deterministic tie handling is part of the observed policy.
choices=[[choice(w,m) for m in menus] for w in weights]
welfare=[choice((10,0,0),m) for m in menus]
# Harmful divergence requires strictly lower welfare, never just tie preference.
harmsets=[{i for i,m in enumerate(menus) if m[choices[k][i]][0]<max(x[0] for x in m)} for k,w in enumerate(weights)]
bad={k for k,s in enumerate(harmsets) if s};remaining=set(bad);selected=[]
while remaining:
 best=max(range(len(menus)),key=lambda i:sum(i in harmsets[k] for k in remaining));caught={k for k in remaining if best in harmsets[k]};assert caught
 selected.append(dict(menu_index=best,actions=menus[best],caught_new=len(caught)));remaining-=caught
passing=[k for k in range(len(weights)) if all(t['menu_index'] not in harmsets[k] for t in selected)]
assert all(not harmsets[k] for k in passing)
assert not harmsets[weights.index((10,0,0))]
# Shared feature training menu: strict aligned improvement, every policy helps.
training=[((-1,-1,-1),(0,0,0),(1,1,1))];assert all(choice(w,training[0])==2 for w in weights)
classes=len(set(tuple(c) for c in choices))
# Independent procedural max-W check; no reliance on computed harmsets.
for k in passing:
 for m in menus:
  picked=choice(weights[k],m);assert all(m[picked][0]>=x[0] for x in m)
result=dict(n_value_vectors=len(weights),n_menus=len(menus),n_policy_equivalence_classes=classes,n_training_compatible=len(weights),n_welfare_sacrificing=len(bad),greedy_battery=selected,passing_weights=[weights[k] for k in passing],claim='Exhaustive finite family/menu coverage only; reward magnitudes, learning, observation shifts and adaptive/deceptive policies are not identified.')
(H/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
with (H/'policies.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['welfare_weight','pleasure_weight','approval_weight','harmful_menus','passes_battery']);w.writerows([(*weights[k],len(harmsets[k]),k in passing) for k in range(len(weights))])
print(json.dumps(result,indent=2))
if __name__=='__main__':pass

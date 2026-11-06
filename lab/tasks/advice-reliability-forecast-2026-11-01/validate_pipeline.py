"""Pilot-only information-flow and geometry checks; no target or source fitting."""
import analysis as a
import copy,json,pathlib
import numpy as np
root=pathlib.Path(__file__).resolve().parent
pilot=json.loads((root/'pilot_person3.json').read_text())
mapping={'A':'sbj_code','B':'sbj_discard','C':'session','D':'block','E':'agent_type','F':'trial_BLOCK','G':'trial_ALL','H':'keep_trial_angle','I':'dot coherence','J':'dot coherence normalized','K':'sbj_angular_error','L':'sbj_confidence','M':'sbj_accurate','N':'judgment_rt','O':'agent_angular_error','P':'agent_confidence','Q':'agent_accurate','R':'final_angular_error','S':'final_accurate'}
rows=[{k:r[v] for k,v in mapping.items()} for r in pilot]
def sequence(rows):
    h=a.History();x=[]
    for r in rows:
        f,g=h.feature(r);x.append(f);h.update(r,g)
    return np.array(x)
original=sequence(rows);tests=[]
for t in [0,1,18,53,54,107,200,300,377]:
    changed=copy.deepcopy(rows)
    for j in range(t,len(rows)):
        changed[j]['R']=float(a.wrap_deg(changed[j]['R']+73))
    delta=float(np.max(abs(sequence(changed)[:t+1]-original[:t+1])))
    assert delta==0
    tests.append({'index':t,'current_plus_suffix_final_changes_current_feature_maxdiff':delta})
    changed=copy.deepcopy(rows)
    for k in ('K','O','R'):changed[t][k]=float(a.wrap_deg(changed[t][k]+137))
    delta=float(np.max(abs(sequence(changed)[t]-original[t])))
    assert delta<1e-12
    tests[-1]['current_common_reference_rotation_maxdiff']=delta
    changed=copy.deepcopy(rows)
    for j in range(t+1,len(rows)):
        changed[j]['K']=float(a.wrap_deg(changed[j]['K']-71));changed[j]['O']=float(a.wrap_deg(changed[j]['O']+49));changed[j]['L']=13;changed[j]['P']=91
    delta=float(np.max(abs(sequence(changed)[:t+1]-original[:t+1])))
    assert delta==0
    tests[-1]['future_input_changes_current_feature_maxdiff']=delta
out={'timestamp_utc':a.NOW(),'pilot':3,'feature_dimensions':a.DIMS,'checks':tests,'all_pass':True,'scope':'Pilot information-flow/rotation invariants, not hypothesis discrimination.'}
a.savej(root/'PILOT_INFORMATION_CHECK.json',out);a.resource_record(root,'PILOT_INFORMATION');print(json.dumps(out,indent=2))

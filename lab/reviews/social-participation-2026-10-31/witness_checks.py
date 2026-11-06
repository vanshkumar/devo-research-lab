"""Independent exact-arithmetic latent-channel and contrary compatibility audit."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import csv
import hashlib
import json
import math
import resource
from fractions import Fraction as Fr
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
AUTHOR=ROOT/'lab/tasks/social-participation-2026-10-31'
READS=[]
def read(p):
    p=Path(p);assert p.stat().st_size<2_000_000
    b=p.read_bytes();READS.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});return b
def load(p):return json.loads(read(p))
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=lambda o: {'exact':str(o),'value':float(o)} if isinstance(o,Fr) else None)+'\n')
def fcat(j):
    q=j//3
    return 0 if q==0 else 1 if q in (1,3) else 2
def eligible(j):return j//3>=3 and j%3>0
def pref(j):return eligible(j) and j%3==1
def masses(p):
    a=sum(v for j,v in enumerate(p) if pref(j))
    b=sum(v for j,v in enumerate(p) if eligible(j) and not pref(j))
    return a,b
def first_law(x):return [sum(v for j,v in enumerate(x) if fcat(j)==f) for f in range(3)]
def channel_summary(p,theta,u,v):
    a,b=masses(p)
    err=max(abs(theta*x+(1-theta)*y-z) for x,y,z in zip(u,v,p))
    pf=first_law(p);uf=first_law(u);vf=first_law(v)
    gates=[]
    for f in range(3):
        ar=sum(x for j,x in enumerate(u) if fcat(j)==f and eligible(j))
        br=sum(x for j,x in enumerate(v) if fcat(j)==f and eligible(j))
        gr=ar/uf[f] if uf[f] else None
        go=br/vf[f] if vf[f] else None
        gates.append({'F':f,'P_E_given_Wref_F':gr,'P_E_given_Wopp_F':go,'conditional_selection_R':gr/go if go else None,'zero_over_zero_R':gr==0 and go==0})
    return {'feasible':True,'theta':theta,'observed_15':p,'emission_Wref_15':u,'emission_Wopp_15':v,'mixture_15':[theta*x+(1-theta)*y for x,y in zip(u,v)],'max_cell_error':err,'emission_sums':[sum(u),sum(v)],'minimum_emission':min(u+v),'P_F':pf,'P_F_given_Wref':uf,'P_F_given_Wopp':vf,'max_W_F_independence_error':max(abs(x-y) for x,y in zip(uf,vf)),'aggregate_selection_R':(a/theta)/(b/(1-theta)) if a and b else None,'selection_by_F':gates}
def global_channel(p,theta):
    a,b=masses(p);e=a+b
    if not 0<theta<1 or a>theta or b>1-theta:
        return {'feasible':False,'theta':theta,'required_gates':[a/theta,b/(1-theta)] if 0<theta<1 else None}
    u=[p[j]/theta if pref(j) else 0 if eligible(j) else (1-a/theta)*p[j]/(1-e) if e!=1 else 0 for j in range(15)]
    v=[p[j]/(1-theta) if eligible(j) and not pref(j) else 0 if eligible(j) else (1-b/(1-theta))*p[j]/(1-e) if e!=1 else 0 for j in range(15)]
    return channel_summary(p,theta,u,v)
def from_ratio(p,R):
    a,b=masses(p)
    theta=a/(a+R*b)
    out=global_channel(p,theta);out['R_requested']=R
    return out
def independent_first(p,theta):
    pf=first_law(p);stats=[]
    for f in range(3):
        a=sum(v for j,v in enumerate(p) if fcat(j)==f and pref(j))/pf[f] if pf[f] else 0
        b=sum(v for j,v in enumerate(p) if fcat(j)==f and eligible(j) and not pref(j))/pf[f] if pf[f] else 0
        stats.append((a,b))
    lower=max(a for a,b in stats);upper=min(1-b for a,b in stats)
    feasible=lower<=theta<=upper and 0<theta<1
    if not feasible:
        return {'feasible':False,'theta':theta,'compatibility_interval':[lower,upper],'required_gates_by_F':[[a/theta,b/(1-theta)] for a,b in stats]}
    u=[0]*15;v=[0]*15
    for j,x in enumerate(p):
        f=fcat(j);a,b=stats[f];e=a+b
        if eligible(j):
            if pref(j):u[j]=x/theta
            else:v[j]=x/(1-theta)
        elif e!=1:
            u[j]=(1-a/theta)*x/(1-e)
            v[j]=(1-b/(1-theta))*x/(1-e)
    result=channel_summary(p,theta,u,v)
    result['compatibility_interval']=[lower,upper]
    # Within F noneligible emissions match; the global noneligible kernel need not.
    au=sum(u[j] for j in range(15) if not eligible(j));av=sum(v[j] for j in range(15) if not eligible(j))
    result['noneligible_kernel_Wref']=[u[j]/au if not eligible(j) and au else 0 for j in range(15)]
    result['noneligible_kernel_Wopp']=[v[j]/av if not eligible(j) and av else 0 for j in range(15)]
    result['global_noneligible_kernel_difference']=max(abs(x-y) for x,y in zip(result['noneligible_kernel_Wref'],result['noneligible_kernel_Wopp']))
    return result

def main():
    raw=list(csv.DictReader(read(OUT/'ROWS.csv').decode().splitlines()))
    rows=[{k:int(v) if k in ('row','z','A','F','f','D','Q','B','Y','M','eligible','copy','first_match') and v else v for k,v in r.items()} for r in raw]
    main=[r for r in rows if r['t']=='T'];n=len(main)
    counts=[0]*15
    def relative_cell(r):
        q=r['Q'];m=r['M']
        if r['z']==-1:
            q={0:0,1:2,2:1,3:4,4:3}[q];m={0:0,1:2,2:1}[m]
        return 3*q+m
    for r in main:counts[relative_cell(r)]+=1
    p=[Fr(c,n) for c in counts]
    a,b=masses(p)
    empirical=[from_ratio(p,R) for R in (Fr(1),Fr(5,4),Fr(3,2),Fr(5,3),Fr(2),Fr(5,2),Fr(3),Fr(10))]
    exact_ind=[independent_first(p,theta) for theta in (Fr(1,2),Fr(9,20),Fr(3,8))]
    for w in empirical+exact_ind:
        if w['feasible']:
            assert w['max_cell_error']==0 and w['minimum_emission']>=0 and w['emission_sums']==[1,1]
    assert exact_ind[0]['max_W_F_independence_error']==0 and exact_ind[1]['max_W_F_independence_error']==0
    assert not exact_ind[2]['feasible']
    save('EMPIRICAL_WITNESSES.json',{'state_order':'3*Q+M; Q=none,one_ref,one_opp,both_ref_first,both_opp_first; M=no,ref,opp','relative_counts':counts,'n':n,'eligible_ref_mass':a,'eligible_opp_mass':b,'common_global_noneligible_kernel_cases':empirical,'W_independent_F_cases':exact_ind})
    # Contrary compatibility is algebraic, with no fitted parameters or search.
    pf=first_law(p);e=a+b
    stratum=[];theta_for_global_h=[]
    for f in range(3):
        af=sum(v for j,v in enumerate(p) if fcat(j)==f and pref(j))
        bf=sum(v for j,v in enumerate(p) if fcat(j)==f and eligible(j) and not pref(j))
        h=(pf[f]-af-bf)/(1-e)
        den=pf[f]-h
        required=(af-a*h)/den if den else None
        theta_for_global_h.append(required)
        stratum.append({'F':f,'n':int(pf[f]*n),'eligible_ref_count':int(af*n),'eligible_opp_count':int(bf*n),'q_selected':af/(af+bf) if af+bf else None,'P_F_given_notE':h,'theta_required_for_W_F_independence_in_original_global_h_family':required})
    qref,qopp=stratum[1]['q_selected'],stratum[2]['q_selected']
    interaction=(qref/(1-qref))/(qopp/(1-qopp))
    assert interaction==Fr(69,17)
    assert len(set(theta_for_global_h))>1
    contrary={'definitions':{'aggregate_R':'P(E|W=ref)/P(E|W=opp), with F marginalized','conditional_common_R':'same P(E|W=ref,F)/P(E|W=opp,F) in each nonzero eligible F stratum','original_common_h':'one global O|notE emission law independent of W','stronger_family':'W independent of F; one noneligible kernel per F independent of W'},'first_strata':stratum,'simultaneous_aggregate_R_and_W_F_independence':{'possible':True,'theta':Fr(1,2),'aggregate_R':exact_ind[0]['aggregate_selection_R'],'every_15_cell_error':exact_ind[0]['max_cell_error']},'simultaneous_conditional_common_R_and_W_F_independence':{'possible':False,'reason':'W independent F and eligible consistency imply odds(q_F)=odds(theta)*R_F. Unequal positive q_F force unequal R_F for every interior theta. Both observed choices exclude degenerate theta0/1. No-courtship F has E=0 and R=0/0, not1.','necessary_R_ref_first_over_R_opp_first':interaction,'log_R_interaction':math.log(float(interaction))},'original_global_h_plus_W_F_independence':{'possible':False,'reason':'Each observed F marginal gives a linear equation in theta; required theta values disagree. In particular F=none requires theta=q=.625 and R=1, but the remaining first-courter marginals still disagree.','theta_equations_by_F':theta_for_global_h},'theta_half_selection_by_F':exact_ind[0]['selection_by_F'],'theta_045_selection_by_F':exact_ind[1]['selection_by_F'],'theta_half_global_noneligible_kernel_difference':exact_ind[0]['global_noneligible_kernel_difference'],'interpretation':'Common across six treatment/reference contexts is not common across F. The independent-F empirical T witness keeps aggregate R5/3 but relaxes the original global noneligible kernel. Do not combine these distinct restrictions into one mild homogeneous selection mechanism.'}
    save('CONTRARY_COMPATIBILITY.json',contrary)
    compact=load(OUT/'COMPACT_LAWS.json')
    def pref_law(ctx):
        p=ctx['models']['primacy']
        if ctx['z']==1:return p
        out=[0.0]*15
        for q in range(5):
            for m in range(3):out[3*{0:0,1:2,2:1,3:4,4:3}[q]+{0:0,1:2,2:1}[m]]=p[3*q+m]
        return out
    laws=[pref_law(c) for c in compact]
    t_indices=[i for i,c in enumerate(compact) if c['t']=='T']
    weights=[sum(r['t']==c['t'] and r['z']==c['z'] for r in rows) for c in compact]
    def unweighted_theta(R):return sum(masses(laws[i])[0]/(masses(laws[i])[0]+R*masses(laws[i])[1]) for i in t_indices)/len(t_indices)
    def mean_theta(R):return sum(weights[i]*masses(laws[i])[0]/(masses(laws[i])[0]+R*masses(laws[i])[1]) for i in t_indices)/sum(weights[i] for i in t_indices)
    lo,hi=.1,10.
    for _ in range(80):
        mid=(lo+hi)/2
        if mean_theta(mid)>.5:lo=mid
        else:hi=mid
    tipping=(lo+hi)/2
    fixed_ratios=sorted(set([1.,1.25,1.5,5/3,2.,2.5,3.,tipping,tipping*1.25]))
    fitted=[]
    for R in fixed_ratios:
        cases=[]
        for ctx,law in zip(compact,laws):
            w=from_ratio(law,R);w['context']={'t':ctx['t'],'z':ctx['z']}
            assert w['feasible'] and float(w['max_cell_error'])<1e-14
            assert abs(sum(w['emission_Wref_15'])-1)<1e-12 and abs(sum(w['emission_Wopp_15'])-1)<1e-12
            cases.append(w)
        fitted.append({'R':R,'mean_T_theta':mean_theta(R),'all_six_feasible':all(w['feasible'] for w in cases),'max_cell_error':max(w['max_cell_error'] for w in cases),'cases':cases})
    save('COMPACT_WITNESSES.json',{'mean_definition':'empirical treatment/reference-context counts, not equal reference-color weights','context_weights':weights,'common_R_tipping':tipping,'unweighted_T_theta_at_weighted_tipping':unweighted_theta(tipping),'initial_equal_context_tipping_before_target_check':1.5344523518820647,'cases':fitted})
    # Waiting model derivation: E requires declining first; completion c_F is equal
    # across W within F. Preferential early acceptance implies survival ratio <=1
    # for ref-first, >=1 for opp-first, hence q_ref<=theta<=q_opp.
    dates=sorted({r['date'] for r in rows})
    draw=np.random.default_rng(20261031).integers(len(dates),size=(5000,len(dates)))
    tally=np.zeros((len(dates),4),dtype=int)
    for r in main:
        if r['eligible']:
            f=1 if r['first_match'] else 2;column=0 if f==1 else 2
            tally[dates.index(r['date']),column]+=1
            tally[dates.index(r['date']),column+1]+=r['copy']
    totals=tally.sum(axis=0);boot=tally[draw].sum(axis=1)
    ok=(boot[:,0]>0)&(boot[:,2]>0)
    delta=boot[ok,1]/boot[ok,0]-boot[ok,3]/boot[ok,2]
    waiting={'assumptions':['W independent of F in T','eligible choice equals W','eligibility requires no early acceptance of first male','matched-preference first male accepted at least as readily as unmatched within each F','same probability of completing an eligible record after waiting for the two W types within each F'],'derivation':'odds(q_refF)=odds(theta)*(1-accept_match_refF)/(1-accept_unmatch_refF)<=odds(theta); odds(q_oppF)=odds(theta)*(1-accept_unmatch_oppF)/(1-accept_match_oppF)>=odds(theta). Equal subsequent completion cancels within each F.','required_inequality':'q_ref_first <= theta <= q_opp_first','counts_nk_ref_then_opp':totals.tolist(),'q_ref':qref,'q_opp':qopp,'difference':qref-qopp,'bootstrap_frame_dates':len(dates),'bootstrap_frame':'all15recorded dates, including dates with zero T rows, to reproduce saved author target','initial_T_only_14date_bootstrap_95':[0.13571195144724552,0.46723885864085496],'date_bootstrap_95':np.quantile(delta,[.025,.975]).tolist(),'undefined_resamples':int(sum(~ok)),'compatible_point_theta_interval':False,'selection_interaction_required_by_this_model':'R_refF/R_oppF <=1; observed69/17>1','limits':'Recorded order does not itself verify sequential early acceptance, equal completion, measurement consistency, or independence. This is a restricted-account contradiction, not a causal test, universal rejection of waiting or a calibrated population interval.'}
    save('WAITING_AUDIT.json',waiting)
    # Exact controls: MAR, complete selection, a heterogeneous-opportunity null
    # with equal selected q_F, and preferred-acceptance/null-acceptance examples.
    full=[Fr(0)]*15;full[10]=Fr(3,5);full[11]=Fr(2,5)
    full1=from_ratio(full,Fr(1));full2=from_ratio(full,Fr(2))
    assert full1['feasible'] and not full2['feasible']
    mar=from_ratio(p,Fr(1));assert masses(mar['emission_Wref_15'])[0]==e and masses(mar['emission_Wopp_15'])[1]==e
    null=[Fr(0)]*15
    null[0]=Fr(1,10);null[3]=Fr(2,5)*Fr(7,10);null[10]=Fr(2,5)*Fr(3,10)*Fr(2,3);null[11]=Fr(2,5)*Fr(3,10)*Fr(1,3)
    null[6]=Fr(1,2)*Fr(2,5);null[13]=Fr(1,2)*Fr(3,5)*Fr(2,3);null[14]=Fr(1,2)*Fr(3,5)*Fr(1,3)
    assert sum(null)==1
    nullw=independent_first(null,Fr(1,2));assert nullw['feasible'] and nullw['max_cell_error']==0 and nullw['max_W_F_independence_error']==0
    assert [s['conditional_selection_R'] for s in nullw['selection_by_F'][1:]]==[Fr(2),Fr(2)]
    def wait_example(am,au):
        theta=Fr(1,2);sr=1-am;su=1-au
        return [theta*sr/(theta*sr+(1-theta)*su),theta*su/(theta*su+(1-theta)*sr)]
    assert wait_example(Fr(4,5),Fr(1,5))==[Fr(1,5),Fr(4,5)]
    assert wait_example(Fr(1,3),Fr(1,3))==[Fr(1,2),Fr(1,2)]
    save('EXACT_CONTROLS.json',{'empirical_MAR':{'theta':mar['theta'],'eligibility_risks_equal':True},'E1_R1_feasible':full1['feasible'],'E1_R2_infeasible':not full2['feasible'],'equal_selected_q_heterogeneous_opportunities_common_R_and_W_independent_F':nullw,'preferential_accept_first_wait_qs':wait_example(Fr(4,5),Fr(1,5)),'equal_acceptance_null_qs':wait_example(Fr(1,3),Fr(1,3))})
    # Compare scalar author claims only after constructing all evidence.
    close=load(AUTHOR/'CLOSEOUT.json')
    ci=[float(x) for x in exact_ind[0]['compatibility_interval']]
    assert max(abs(x-y) for x,y in zip(ci,close['first_courter_independent_compatibility_interval']))<1e-14
    assert abs(tipping-next(c['R'] for c in close['common_R_witness_summary'] if abs(c['mean_T_latent_reference_preference']-.5)<1e-12))<1e-12
    assert max(abs(x-y) for x,y in zip(waiting['date_bootstrap_95'],close['first_courter_diagnostic']['date_bootstrap_95']))<1e-14
    save('READS_WITNESSES.json',{'reads':READS,'read_hash_bytes':sum(x['bytes'] for x in READS),'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'empirical_relative_counts':counts,'compatibility_interval':ci,'theta_cases':[(float(w['theta']),w['feasible']) for w in exact_ind],'common_compact_R_tipping':tipping,'compact_R2_T_theta':mean_theta(2),'contrary':{'marginal_R5over3_with_independence_possible':True,'common_conditional_R_with_independence_possible':False,'required_interaction':float(interaction),'original_global_h_independence_theta_equations':[str(x) for x in theta_for_global_h]},'waiting_counts':totals.tolist(),'waiting_difference':float(qref-qopp),'waiting_interval':waiting['date_bootstrap_95'],'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))

if __name__=='__main__':main()

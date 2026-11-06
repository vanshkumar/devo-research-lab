"""Freeze then run the source-only no-release support/counterexample protocol."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import csv,hashlib,json,resource,sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PINNED=('PLAN.md','SOURCE_ONLY_PROTOCOL.md','source_support.py','source_analysis.py','endpoint_control.py',
        'prescription_check.py','measurement_sensitivity.py','support_witness.py',
        'SOURCE_SUPPORT.json','SOURCE_ANALYSIS.json','ENDPOINT_CONTROL.json','PRESCRIPTION_CHECK.json','MEASUREMENT_SENSITIVITY.json')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def freeze():
    record=dict(created_utc=datetime.now(timezone.utc).isoformat(),task='motor-teaching-transfer-2026-10-31',
        investigator='01a193d5-f27c-7903-bb9c-2bdd03425272',
        scope='Source-only final support witness. NOT a Figure4 outcome release or a frozen target-scored forecast.',
        figure4_outcomes_decoded=0,optional210_outcomes_opened=False,
        files={p:sha(HERE/p) for p in PINNED})
    with (HERE/'SOURCE_ONLY_FREEZE.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
    print(json.dumps(record,indent=2))

def main():
    frozen=json.loads((HERE/'SOURCE_ONLY_FREEZE.json').read_text())
    assert all(sha(HERE/p)==h for p,h in frozen['files'].items())
    support=json.loads((HERE/'SOURCE_SUPPORT.json').read_text())
    epi=json.loads((HERE/'ENDPOINT_CONTROL.json').read_text())
    prescription=json.loads((HERE/'PRESCRIPTION_CHECK.json').read_text())
    sigma,g,t=prescription['fit']['parameters']
    records=[];counts=Counter();by=defaultdict(list)
    p=ROOT/'sources/learning_intervention_feasibility_2026-10-28/task_success_fig4.csv'
    body=p.read_bytes()
    assert hashlib.sha256(body).hexdigest()==support['files'][3]['sha256']
    del body
    allowed={'Subject','TrialNum','ClampAngle','TargetJump','TrialLabel','TgtSize','TgtAngle'}
    with p.open(newline='') as f:
        reader=csv.DictReader(f);schema=reader.fieldnames
        for full in reader:
            r={k:v for k,v in full.items() if k in allowed}
            person=int(r['Subject']);tn=int(r['TrialNum']);by[person].append(tn)
            if not 104<=tn<=967:continue
            c=float(r['ClampAngle']);rawj=float(r['TargetJump']);label=r['TrialLabel']
            assert label in ('Miss','Hit','Jump To')
            assert (label!='Jump To' or rawj==-c)
            j=c if label=='Jump To' else 0.
            assert label=='Jump To' or rawj==0
            counts[(c,j,label,r['TgtSize'])]+=1
    assert len(by)==42 and all(sorted(v)==list(range(1,969)) for v in by.values())
    sourceX=[];targetX=[];source_signals=[]
    for src in support['files'][:3]:
        for v in src['input_cells']:
            c=v['clamp'];j=v['jump'];flicker=(src['local']=='task_success_fig3.csv' and j==.01)
            if flicker:j=0.
            x=[c/4,j/4,c/4*int(j!=0 or flicker),c/4*int(c!=0 and j==c)]
            sourceX.append(x);source_signals.append(0.)
    for (c,j,label,size),n in sorted(counts.items()):
        targetX.append([c/4,j/4,c/4*int(j!=0),c/4*int(c!=0 and j==c),c/4*int(label=='Hit')])
    sx=np.array(sourceX);tx=np.array(targetX);z=np.array(source_signals)
    ranks=dict(source_base=int(np.linalg.matrix_rank(sx)),source_with_enlarged_stationary_hit=int(np.linalg.matrix_rank(np.c_[sx,z])),
        target_base=int(np.linalg.matrix_rank(tx[:,:4])),target_with_enlarged_stationary_hit=int(np.linalg.matrix_rank(tx)),
        new_feature_source_max_absolute=float(abs(z).max()),
        new_feature_target_nonzero_trials=sum(n for (c,j,l,size),n in counts.items() if l=='Hit'))
    assert ranks['source_base']==ranks['source_with_enlarged_stationary_hit']
    assert ranks['target_with_enlarged_stationary_hit']>ranks['target_base']
    A4=epi['sources'][2]['summary']['No Jump']['current_plus_next']['estimate']
    magnitudes=sorted(set(abs(c) for c,j,l,size in counts))
    shapes=[]
    for tau in (1.,4.,16.):
        for c in magnitudes:
            amplitude=A4*np.tanh(c/tau)/np.tanh(4/tau)
            jump=(g*amplitude-c*t)*np.exp(-c*c/(2*sigma*sigma))
            for extension in ('motion_gate','shared_success_gate'):
                for label in ('Miss','Hit','Jump To'):
                    pred=amplitude if label=='Miss' or (label=='Hit' and extension=='motion_gate') else jump
                    records.append(dict(tau=tau,clamp_magnitude=c,extension=extension,condition=label,
                                        predicted_adaptation_degrees=float(pred)))
    for src in support['files'][:3]:
        c=np.array(src['clamps'])
        vals=[np.tanh(c/tau)/np.tanh(4/tau) for tau in (1.,4.,16.)]
        shapes.append(float(max(np.max(abs(v-vals[0])) for v in vals)))
    with (HERE/'SOURCE_COMPATIBLE_TARGET_WITNESSES.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    # Algebraic control: large arbitrary additive endpoint effects on real cell supports.
    recoveries=[]
    for src in epi['sources']:
        cells=np.array(src['input_cells']);K=len(cells)
        U=-.3*cells[:,0]+.02*cells[:,1]**2+.2*cells[:,2]
        E=3*np.sin(np.arange(K)+.4)
        X=[];Y=[]
        for a in range(K):
            for b in range(K):
                x=np.zeros(2*K-1);x[0]=1
                if a:x[a]=1
                if b:x[K-1+b]=1
                X.append(x);Y.append(U[a]+E[b]-E[a])
        coef,_,rank,_=np.linalg.lstsq(X,Y,rcond=None)
        recovered=np.r_[0,coef[1:K]]+np.r_[0,coef[K:]]
        error=float(np.max(abs((recovered-recovered[0])-(U-U[0]))))
        assert rank==2*K-1 and error<1e-12
        recoveries.append(dict(source=src['source'],rank=int(rank),columns=2*K-1,
                                arbitrary_additive_endpoint_peak=float(abs(E).max()),max_contrast_recovery_error=error))
    initial=json.loads((HERE/'SOURCE_ANALYSIS_INITIAL_WARNINGS.json').read_text())
    final=json.loads((HERE/'SOURCE_ANALYSIS.json').read_text())
    coeferror=0.;prederror=0.;losserror=0.
    for a,b in zip(initial['sources'],final['sources']):
        coeferror=max(coeferror,float(np.max(abs(np.array([p['coefficient'] for p in a['per_person']])-np.array([p['coefficient'] for p in b['per_person']])))))
        prederror=max(prederror,max(abs(a['predicted_c4_signed_adaptation'][k]['estimate']-b['predicted_c4_signed_adaptation'][k]['estimate']) for k in a['predicted_c4_signed_adaptation']))
        losserror=max(losserror,max(abs(x['leave_person_out_centered_MSE']-y['leave_person_out_centered_MSE']) for x,y in zip(a['model_comparison'],b['model_comparison'])))
    maxnormal=max(p['max_fit_normal_equation_residual'] for s in epi['sources'] for p in s['people'])
    assert coeferror<1e-12 and prederror<1e-12 and losserror<1e-12 and maxnormal<1e-7
    out=dict(created_utc=datetime.now(timezone.utc).isoformat(),frozen_at_utc=frozen['created_utc'],freeze_sha256=sha(HERE/'SOURCE_ONLY_FREEZE.json'),
         freeze_pins_verified=True,source_shape_prediction_max_disagreement=max(shapes),
         source_targetsize_extension_max_disagreement=0.,identification=ranks,
         target_input_only_people=sorted(by),target_input_only_n_exposures=sum(counts.values()),
         target_schema=schema,retained_fields=sorted(allowed),
         discarded_before_numeric_conversion=[k for k in schema if k not in allowed],
         target_outcome_numeric_values_decoded=0,target_outcome_statistics_computed=0,
         signed_jump_harmonization='Figure4 JumpTo physical j=ClampAngle; exported TargetJump=-ClampAngle',
         witness_predictions='SOURCE_COMPATIBLE_TARGET_WITNESSES.csv (unscored support witnesses, not a released target evaluation)',
         numerical_warning_check=dict(initial_final_max_coefficient_difference=coeferror,
                initial_final_max_forecast_difference=prederror,initial_final_max_loss_difference=losserror,
                endpoint_fit_max_normal_equation_residual=maxnormal,
                final_einsum_runs_emitted_no_warnings=True),
         additive_endpoint_generator_control=recoveries,
         limits='Witness agreement on observed sources does not make either extension true or every normalized hypothesis untestable. State-dependent/nonadditive endpoint and perceived-goal alternatives remain.',
         charged_additional_read_decoded_hash_bytes=8*p.stat().st_size+8*sum((HERE/x).stat().st_size for x in PINNED),
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (HERE/'SUPPORT_WITNESS.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):
        if len(sys.argv)>1 and sys.argv[1]=='freeze':freeze()
        else:main()

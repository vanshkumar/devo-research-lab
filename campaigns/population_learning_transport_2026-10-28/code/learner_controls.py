"""Known-answer exact-endpoint control of the frozen generative learner.

Consumed-source contexts only. Independent future action/trainer random seeds
generate a known-law reference ensemble. No new animal or external data is read.
The expected-law check is distinct from acceptance in one noisy cohort.
"""
import json,sys,time
import numpy as np
from campaign import C,OLD,MODEL,BANK,load_rnn,load_bank,make_initial,simulate,seed_for,digest,summarize
from score_campaign import gate_summary

def run(n=256):
    out=C/'artifacts/learner_controls';out.mkdir(parents=True,exist_ok=True)
    config=dict(minimum_animals=15,minimum_bin_fraction=.8,scalar_margin=.05,
                curve_mae_max=.05,bin_error_max=.075,lab_bias_max=.10,
                leave_one_lab_out_bias_max=.05,require_cluster90=True)
    model=load_rnn(MODEL);bank=load_bank(BANK)
    allocation={r['subject']:r for r in json.loads((OLD/'protocols/SPLIT.json').read_text())['standard']}
    ids=json.loads((OLD/'artifacts/results/SUBJECT_ORDER.json').read_text())
    ids=sorted(ids,key=lambda s:__import__('hashlib').sha256(s.encode()).hexdigest())[:24]
    # Lab labels/counts match the metadata-certified new test design. Contexts
    # themselves are already consumed; these labels are synthetic cluster tags.
    labs=np.repeat(np.arange(5),[5,2,1,10,6]).tolist()
    pred={k:[] for k in ('standard','external')}; truth={k:[] for k in pred}
    for subject in ids:
        t=time.monotonic();a=allocation[subject]
        with np.load(OLD/'data/processed'/a['split']/(subject+'.npz'),allow_pickle=False) as z:
            prefix={k:z[k][:1000] for k in z.files if k!='metadata_json' and z[k].ndim and len(z[k])==len(z['choice'])}
            starts=z['session_start'][1000:4000]
        seed=seed_for(subject)
        common,initial,persist,cal=make_initial(prefix,subject,n,seed,model,bank)
        # Same prefix calibration defines the known conditional learner, while
        # independent streams generate all future stimuli/actions/rewards.
        for policy in pred:
            p=simulate(model,prefix,starts,common,initial,persist,'rnn',policy,seed)
            q=simulate(model,prefix,starts,common,initial,persist,'rnn',policy,seed+93017)
            pred[policy].append(p['samples'][:,:,:2].mean(2))
            truth[policy].append(q['samples'][:,:,:2].mean(2))
        print(json.dumps(dict(subject=subject,seconds=time.monotonic()-t)),flush=True)
    results={};rng=np.random.default_rng(102826113)
    for policy in pred:
        p=np.asarray(pred[policy]);q=np.asarray(truth[policy]);mean=p.mean(1);known=q.mean(1)
        good=gate_summary(known,mean,labs,config)
        wrong=gate_summary(known+.10,mean,labs,config)
        cancelled=gate_summary(known+np.array([.12,.12,.12,-.12,-.12,-.12]),mean,labs,config)
        # Full heterogeneous single-cohort variation: each animal contributes
        # one independently generated trajectory, exactly as the intended data.
        import gate_audit
        ix=rng.integers(n,size=(10000,24))
        actual=q[np.arange(24)[None,:],ix,:]
        accept,_,_,_,_,_=gate_audit.repeated_gate(actual-mean[None,:,:],labs)
        results[policy]=dict(expected_law_correct=good,wrong10pp=wrong,cancelling12pp=cancelled,
                             single_cohort_gate_acceptance=float(accept.mean()),n_cohort_controls=10000,
                             note='Expected-law control uses two independent ensembles; one-cohort gate is deliberately more demanding')
        np.savez_compressed(out/(policy+'.npz'),prediction=p,independent_truth=q,subjects=np.array(ids),synthetic_lab=np.array(labs))
    final=dict(scope='Known frozen RNN generative law in consumed prefix contexts, independent future streams, no new real outcomes',
               n_animals=24,n_particles=n,model_sha256=digest(MODEL),bank_sha256=digest(BANK),results=results,
               valid=all(r['expected_law_correct']['pass_gate'] and not r['wrong10pp']['pass_gate'] and not r['cancelling12pp']['pass_gate'] for r in results.values()))
    (out/'RESULT.json').write_text(json.dumps(final,indent=2)+'\n');print(json.dumps(final,indent=2),flush=True)
    return final

if __name__=='__main__':run()

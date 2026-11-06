"""Development-only conditional generators on fixed real input designs.

Whole-person residual ranks supply a source-derived noise copula. Randomized
within-rank uniforms preserve the specified marginal conditional means.
No real evaluation outcome is read by this script.
"""
import copy
import datetime as dt
import json
import resource
import numpy as np
from analysis import ROOT, CUES, source_data, fit, predict, losses, boot_summary, save, scaled

SEED=202611010231
REPLICATES=100

def wilson(k,n):
    z=1.959963984540054
    p=k/n
    center=(p+z*z/(2*n))/(1+z*z/n)
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(center-half),float(center+half)]

def cube(units, values):
    out=np.zeros((len(units),3,6))
    for i,u in enumerate(units):
        out[i,u['cue'],u['ordinal']]=values[i]
    return out

def noise_description(units,model):
    a,p=predict(units,model)
    residual=cube(units,a['y']-p)
    # Stable deterministic tie handling; randomized within-rank bins below.
    order=np.argsort(residual,axis=0,kind='stable')
    ranks=np.empty_like(order)
    for c in range(3):
        for n in range(6):
            ranks[order[:,c,n],c,n]=np.arange(len(units))
    positive=np.mean(cube(units,a['y'])>0,axis=0)
    return ranks,positive

def uniforms(rng,ranks,size):
    donor=rng.integers(0,len(ranks),size=size)
    return (ranks[donor]+rng.random((size,3,6)))/len(ranks)

def design_test(cert,donors,rng):
    out=[]
    for participant in cert['evaluation_ids']:
        donor=donors[int(rng.integers(len(donors)))]
        u=dict(donor)
        rows=[r for r in cert['inputs'][str(participant)] if r['blocknum']=='4' and r['trialcode'].startswith('CS')]
        seen={0:0,1:0,2:0}
        cue=[]
        ordinal=[]
        for r in rows:
            c={'CS1':0,'CS2':1,'CSm':2}[r['trialcode'].split('_')[0]]
            cue.append(c)
            ordinal.append(seen[c])
            seen[c]+=1
        donor_cube=np.zeros((3,6))
        donor_cube[donor['cue'],donor['ordinal']]=donor['y']
        u['cue']=np.array(cue)
        u['ordinal']=np.array(ordinal)
        u['first']=np.array([cue.index(c) for c in range(3)])
        u['prefix_end']=int(max(u['first'])+1)
        u['future']=np.arange(18)>=u['prefix_end']
        u['y']=donor_cube[u['cue'],u['ordinal']].copy()
        u['id']=participant
        out.append(u)
    return out

def generate(units,model,ranks,positive,rng):
    a,mean=predict(units,model)
    shape=len(units)
    channel=units[0]['channel']
    values=np.zeros_like(mean)
    if channel=='expectancy':
        for _ in range(8):
            uniform=uniforms(rng,ranks,shape)
            uc=np.array([uniform[i,u['cue'],u['ordinal']] for i,u in enumerate(units)])
            values += (uc<mean)/8
    else:
        u1,u2=uniforms(rng,ranks,shape),uniforms(rng,ranks,shape)
        u1=np.array([u1[i,u['cue'],u['ordinal']] for i,u in enumerate(units)])
        u2=np.array([u2[i,u['cue'],u['ordinal']] for i,u in enumerate(units)])
        fraction=np.array([positive[u['cue'],u['ordinal']] for u in units])
        threshold=np.sqrt(.02)
        probability=np.minimum(np.clip(fraction,.05,.95),.99*mean/threshold)
        active_mean=np.divide(mean,probability,out=np.full_like(mean,threshold),where=probability>0)
        amplitude=threshold+(active_mean-threshold)*(-np.log1p(-u2))
        values=np.where(u1<probability,amplitude,0.)
    out=[]
    for i,u in enumerate(units):
        s=dict(u)
        s['y']=np.where(u['future'],values[i],u['y'])
        out.append(s)
    return out,mean

def main():
    assert (ROOT/'FREEZE.json').exists()
    assert not (ROOT/'CONTROLS.json').exists()
    cert=json.loads((ROOT/'SOURCE_CERTIFICATION.json').read_text())
    data,_=source_data('development')
    models=json.loads((ROOT/'FROZEN_MODELS.json').read_text())
    recipes=json.loads((ROOT/'SELECTED_RECIPES.json').read_text())
    rng=np.random.default_rng(SEED)
    result={'seed':SEED,'replicates':REPLICATES,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'real_evaluation_outcomes_read':False,'channels':{}}
    for channel,train in data.items():
        model=models[channel+'/primary']['common']
        ranks,positive=noise_description(train,model)
        result['channels'][channel]={}
        for effect,alpha in [('null',0.),('known_alpha1',1.)]:
            generator=copy.deepcopy(model)
            generator['augmented']=alpha>0
            generator['parameters']['alpha']=alpha
            records=[]
            for rep in range(REPLICATES):
                test=design_test(cert,train,rng)
                simulated_train,_=generate(train,generator,ranks,positive,rng)
                simulated_test,oracle=predict_test=generate(test,generator,ranks,positive,rng)
                common=fit(simulated_train,False,recipes[channel]['shrink_family'])
                update=fit(simulated_train,True,recipes[channel]['shrink_family'])
                a,p,l=losses(simulated_train,simulated_test,common,update)
                summary=boot_summary(l,reps=500,seed=SEED+rep)
                # Mean separation from the BEST refitted common family, no noise.
                oracle_units=[]
                for i,u in enumerate(test):
                    s=dict(u)
                    s['y']=np.where(u['future'],oracle[i],u['y'])
                    oracle_units.append(s)
                oracle_common=fit(oracle_units,False,recipes[channel]['shrink_family'])
                ao,po=predict(oracle_units,oracle_common)
                separation=float(np.mean(np.sum(np.where(ao['mask'],(oracle-po)**2,0),axis=1)/ao['mask'].sum(axis=1)))
                records.append({'replicate':rep,'gain_mse':summary['gain_mse'],
                                'fractional_reduction':summary['fractional_reduction'],
                                'positive_bootstrap_lower':summary['gain_mse_bootstrap95'][0]>0,
                                'passes_full_rule':summary['passes_five_percent_positive_lower_and_baselines'],
                                'selected_alpha':update['parameters']['alpha'],
                                'oracle_best_common_mean_separation_mse':separation})
            count=sum(r['passes_full_rule'] for r in records)
            result['channels'][channel][effect]={'generator':generator,'full_rule_count':count,
                'full_rule_rate':count/REPLICATES,'wilson95':wilson(count,REPLICATES),
                'mean_oracle_common_separation_mse':float(np.mean([r['oracle_best_common_mean_separation_mse'] for r in records])),
                'records':records}
            print(channel,effect,'full_rule',count,'/',REPLICATES,'wilson95',wilson(count,REPLICATES),
                  'mean_oracle_separation',result['channels'][channel][effect]['mean_oracle_common_separation_mse'],flush=True)
    result['observation_generator']='Whole-person residual-rank copula; randomized rank-bin uniforms. Physiology: mean-preserving hurdle/exponential above sqrt(.02), zero otherwise. Expectancy: mean of8Bernoulli draws for9valid rating levels. Conditional means exactly generator forecast in expectation. Prefixes fixed; designs fixed; development-derived noise, not universal acquisition power.'
    result['read_charge_bytes']=15000000
    result['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save('CONTROLS.json',result)
    print('RESOURCE',result['read_charge_bytes'],result['peak_rss_bytes'])

if __name__=='__main__':
    main()

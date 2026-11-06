"""Independent raw-byte feature, probability and scoring reconstruction.

Run ONLY after the lead authorizes validation inspection. Requires a saved
VALIDATION_OPENED marker. Does not import model.py or analysis.py.
"""
from pathlib import Path
import argparse,csv,hashlib,json,math
import numpy as np
from numpy.polynomial.hermite import hermgauss

ROOT=Path(__file__).resolve().parents[2]


def digest(path,kind='sha256'):
    h=hashlib.new(kind)
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def number(value):
    try:return float(value)
    except (ValueError,TypeError):return float('nan')


def sigmoid(x):
    if x>=0:return 1/(1+math.exp(-x))
    ex=math.exp(x);return ex/(1+ex)


def reconstruct(rows,fit):
    config=fit['config'];names=fit['feature_names'];beta=fit['beta']
    center=fit['calibration_transform']['center'];scale=fit['calibration_transform']['scale']
    values=[]
    for lo,hi in [(0,100),(100,200)]:
        products=[r['choice']*np.sign(r['sideContrast']) for r in rows[lo:hi] if r['choice'] in [-1,1] and r['sideContrast']!=0]
        values.append(sum(products)/len(products) if products else 0.)
    early=[r['choice'] for r in rows[:200] if r['choice'] in [-1,1]]
    values.extend([sum(early)/len(early) if early else 0.,1-len(early)/200])
    calibration={name:(v-c)/s for name,v,c,s in zip(fit['calibration_transform']['names'],values,center,scale)}
    ghx,ghw=hermgauss(config['gh_nodes']);history=[0.,0.,0.];previous=0.;predictions=[]
    decay=[math.exp(-1/tau) for tau in config['taus']]
    for r in rows:
        c=r['sideContrast'];sign=1 if c>0 else -1 if c<0 else 0
        time=(r['trial']-399.5)/200;group=r['instructions']-.5
        base={'intercept':1.,'previous_choice':previous,'later_time':time,'sensory_time':sign*time,
              'history_tau2':history[0],'history_tau8':history[1],'history_tau32':history[2]}
        for label,level in [('0.1',.1),('0.25',.25),('0.5',.5),('1',1.)]:
            base['contrast_'+label]=sign if math.isclose(abs(c),level,rel_tol=0,abs_tol=1e-8) else 0.
        design=[]
        for name in names:
            if ':' not in name:design.append(base[name])
            else:
                left,right=name.split(':')
                design.append((group if left=='condition' else calibration[left])*base[right])
        eta=sum(a*b for a,b in zip(design,beta))
        z=[1.,sign]+(history if fit['variant']!='no_history' else [])
        variance=config['random_sd']**2*sum(a*a for a in z)
        p=sum(w*sigmoid(eta+math.sqrt(2*variance)*x) for x,w in zip(ghx,ghw))/math.sqrt(math.pi)
        predictions.append(p)
        valid=r['choice'] in [-1,1] and r['feedbackType'] in [-1,1]
        e=r['choice']*r['feedbackType'] if valid else 0.
        history=[a*b+(1-a)*e for a,b in zip(decay,history)]
        previous=r['choice'] if r['choice'] in [-1,1] else 0.
    return predictions


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--predictions',default='outputs/primary');ap.add_argument('--output',default='independent_validation_audit.json');args=ap.parse_args()
    assert (ROOT/'protocol/VALIDATION_OPENED.json').exists(),'Validation remains protected: no opened marker'
    predroot=ROOT/args.predictions
    assert (predroot/'summary.json').exists(),'Wait for completed primary results before auditing'
    with (ROOT/'protocol/split_manifest.csv').open() as f:split={r['subject']:r for r in csv.DictReader(f)}
    ids={s for s,r in split.items() if r['partition']!='development'}
    raw=ROOT/'inputs/processed_data_2026.csv'
    assert digest(raw,'md5')=='5bc8ccf8bdca2e89fc21d20ffb7c1695'
    rows={s:[] for s in ids}
    fields=['trial','instructions','probabilityLeft','contrastLeft','contrastRight','stimSide','sideContrast','stimContrast','choice','feedbackType']
    with raw.open(newline='') as f:
        for r in csv.DictReader(f):
            if r['subject'] in ids:
                row={k:number(r[k]) for k in fields};row['trial']=int(row['trial']);rows[r['subject']].append(row)
    for sid,rr in rows.items():
        rr.sort(key=lambda r:r['trial']);assert [r['trial'] for r in rr]==list(range(600))
        schedules=np.asarray([[r[k] for k in ['probabilityLeft','contrastLeft','contrastRight','stimSide']] for r in rr],dtype='<f8')
        assert hashlib.sha256(schedules.tobytes()).hexdigest()==split[sid]['schedule_sha256']
        for r in rr:
            assert r['choice'] in [-1,0,1] or math.isnan(r['choice'])
            if r['choice'] in [-1,1]:assert r['choice']*r['feedbackType']==r['stimSide']
    with (predroot/'trial_predictions.csv').open() as f:export={(r['subject'],int(r['trial'])):r for r in csv.DictReader(f)}
    with (predroot/'participant_scores.csv').open() as f:person_export={r['subject']:r for r in csv.DictReader(f)}
    fits={v:json.loads((predroot/(v+'_fit.json')).read_text()) for v in ['no_history','shared','condition']}
    maximum={v:0. for v in fits};score_errors=[];n_primary=0;data_mismatches=0;people=[]
    for sid,rr in sorted(rows.items()):
        probs={v:reconstruct(rr,fit) for v,fit in fits.items()};last_switch=None;values=[];briers=[];history_gains=[]
        for t,r in enumerate(rr):
            er=export[(sid,t)]
            assert number(er['choice'])==r['choice'] or (math.isnan(number(er['choice'])) and math.isnan(r['choice']))
            if t and r['probabilityLeft']!=rr[t-1]['probabilityLeft'] and r['probabilityLeft']!=.5 and rr[t-1]['probabilityLeft']!=.5 and t>=200:last_switch=t
            offset=t-last_switch if last_switch is not None else 999
            primary=200<=t<600 and offset<30 and r['stimContrast']<=.1 and r['choice'] in [-1,1]
            assert primary==(er['primary_responded']=='True')
            for v in fits:maximum[v]=max(maximum[v],abs(probs[v][t]-number(er['p_'+v])))
            if primary:
                y=int(r['choice']==1);log={}
                for v in fits:
                    p=min(max(probs[v][t],1e-12),1-1e-12);log[v]=math.log(p if y else 1-p)
                values.append(log['condition']-log['shared'])
                briers.append((probs['shared'][t]-y)**2-(probs['condition'][t]-y)**2)
                history_gains.append(log['shared']-log['no_history'])
        n_primary+=len(values);mean=sum(values)/len(values)
        score_errors.append(abs(mean-number(person_export[sid]['delta_log'])))
        assert len(values)==int(person_export[sid]['n'])
        assert abs(sum(briers)/len(briers)-number(person_export[sid]['delta_brier']))<1e-12
        assert abs(sum(history_gains)/len(history_gains)-number(person_export[sid]['history_gain']))<1e-12
        people.append(dict(subject=sid,n=len(values),delta_log=mean,delta_brier=sum(briers)/len(briers)))
    assert max(maximum.values())<1e-12,maximum
    assert max(score_errors)<1e-12,score_errors
    summary=json.loads((predroot/'summary.json').read_text())
    aggregate=sum(r['delta_log'] for r in people)/len(people)
    assert abs(aggregate-summary['delta_log']['mean'])<1e-12
    result=dict(passed=True,scope='Independent original-byte reconstruction after validation was opened; no imports from primary implementation',
        participants=len(ids),validation_trials=sum(map(len,rows.values())),primary_responses=n_primary,
        maximum_probability_errors=maximum,maximum_participant_logscore_error=max(score_errors),
        reconstructed_mean_delta_log=aggregate,
        checks=['full original MD5','all validation schedule hashes','feedback-side identity','raw choices match exported predictions',
                'independent first200 calibration','independent causal history and design construction','independent Gaussian integration',
                'independent switch and omission masks','all participant log/Brier/history scores','equal-person mean score'],
        hashes={str(p.relative_to(ROOT)):digest(p) for p in [raw,predroot/'trial_predictions.csv',predroot/'participant_scores.csv',predroot/'summary.json']})
    (Path(__file__).parent/args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

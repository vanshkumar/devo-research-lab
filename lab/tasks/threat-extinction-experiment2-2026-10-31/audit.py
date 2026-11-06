"""Author checks; independent scientific review remains a distinct assignment."""
import argparse
import datetime as dt
import hashlib
import json
import resource
import zipfile
import numpy as np
from analysis import ROOT,CUES,source_data,fit,predict,arrays,forecast,save,scaled
from first_data_check import first_sav

def main(stage):
    cert=json.loads((ROOT/'SOURCE_CERTIFICATION.json').read_text())
    assert not set(cert['development_ids']) & set(cert['evaluation_ids'])
    assert {1,109,110} <= set(cert['development_ids'])
    groups=['development']+(['evaluation'] if stage=='post' else [])
    result={'stage':stage,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'groups':{},
            'distinct_independent_review':False}
    for group in groups:
        data,_=source_data(group)
        z=zipfile.ZipFile(ROOT/'sources/experiment2.zip')
        emeta=cert['metadata']['US expectancy_SE_exp2.sav']
        smeta=cert['metadata']['SCR data_SE_exp2.sav']
        indices={i for i,m in enumerate(emeta) if int(m['PP_number']) in cert[group+'_ids']}
        n=next(n for n in z.namelist() if n.endswith('/US expectancy_SE_exp2.sav'))
        ex={int(r['PP_number']):r for r in first_sav(z.read(n),60,case_indices=indices)['cases'] if r}
        n=next(n for n in z.namelist() if n.endswith('/Secondary extinction exp2.dat'))
        occurrences={}
        rating_checks=0
        with z.open(n) as f:
            f.readline()
            for line in f:
                fields=line.rstrip(b'\r\n').split(b'\t')
                participant=int(fields[2])
                if participant not in ex or fields[4] not in [b'3',b'4'] or not fields[5].startswith(b'CS'):
                    continue
                phase='Acq' if fields[4]==b'3' else 'Ext'
                c={b'CS1':0,b'CS2':1,b'CSm':2}[fields[5].split(b'_')[0]]
                k=(participant,phase,c)
                occurrences[k]=occurrences.get(k,0)+1
                key=f'{phase}_{CUES[c]}_{occurrences[k]}'
                assert float(fields[8])==ex[participant][key],(participant,key,float(fields[8]),ex[participant][key])
                rating_checks+=1
        n=next(n for n in z.namelist() if n.endswith('/SCR data_SE_exp2.sav'))
        si={i for i,m in enumerate(smeta) if int(m['PP_number']) in cert[group+'_ids']}
        sc=[r for r in first_sav(z.read(n),60,case_indices=si)['cases'] if r]
        scoring_checks=0
        max_error=0.
        for row in sc:
            for c in CUES:
                upper=13 if c=='CSplus1' else 14
                for occurrence in range(1,upper+1):
                    key=f'{c}_{occurrence}'
                    raw,val,sqrtval=row['GSR1'+key],row[key],row['SQRT_'+key]
                    if raw is None or val is None:
                        continue
                    corrected=raw/1000 if raw/1000>.02 else 0.
                    assert abs(val-corrected)<1e-12
                    scoring_checks+=1
                    if row['SCR_max'] is not None and row['SCR_max']>0 and sqrtval is not None:
                        error=abs(np.sqrt(val/row['SCR_max'])-sqrtval)
                        max_error=max(max_error,float(error))
                        assert error<1e-12
                        scoring_checks+=1
        invariance={}
        for channel,units in data.items():
            model=fit(units,False,False)
            a,p=predict(units,model)
            altered=[]
            for u in units:
                v=dict(u)
                v['y']=u['y'].copy()
                v['y'][u['future']]=99.25
                altered.append(v)
            _,changed=predict(altered,model)
            assert np.array_equal(p,changed),'forecast depends on future outcomes'
            params=dict(model['parameters'])
            params['alpha']=0.
            nested=forecast(a,params,True)
            nonnested=forecast(a,params,False)
            nested_error=float(np.max(np.abs(nested-nonnested)))
            assert nested_error<1e-14
            params.update(q=0.,k=0.,w=1.,alpha=0.)
            init=forecast(a,params,False)
            assert np.array_equal(init,np.take_along_axis(a['initial'],a['cue'],axis=1))
            invariance[channel]={'future_suffix_bit_exact':True,'alpha0_nesting_max_abs_error':nested_error,
                                 'initial_cue_discrimination_preserved':True,'participants':len(units),
                                 'prefix_lengths':sorted(set(u['prefix_end'] for u in units))}
        result['groups'][group]={'raw_to_sav_rating_checks':rating_checks,
            'supplied_scoring_checks':scoring_checks,'published_sqrt_max_abs_error':max_error,
            'functional_checks':invariance}
    if (ROOT/'FREEZE.json').exists():
        frozen=json.loads((ROOT/'FREEZE.json').read_text())
        pins={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in frozen['pins'].items()}
        assert all(pins.values())
        result['frozen_pins']=pins
    result['read_charge_bytes']=8000000 if stage=='pre' else 12000000
    result['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save('AUTHOR_AUDIT_'+stage.upper()+'.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=['pre','post'])
    main(ap.parse_args().stage)

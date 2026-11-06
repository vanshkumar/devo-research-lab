"""Self-audit from original CSVs without importing author feature/score helpers.

This is not the separate independent review commissioned by the PI.
"""
import collections,csv,datetime,hashlib,io,json,math,pathlib,platform,resource,sys
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    charge=0;f=json.loads((ROOT/'FREEZE.json').read_text());rf=json.loads((ROOT/'REVISION_FREEZE.json').read_text())
    pins=0
    for pin in f['pins']+rf['pins']:
        b=(ROOT/pin['path']).read_bytes();charge+=len(b)
        assert hashlib.sha256(b).hexdigest()==pin['sha256'];pins+=1
    support=json.loads((ROOT/'SOURCE_SUPPORT.json').read_text());wv={x['name']:x for x in support['wav']}
    files={};features={};labels={};quantum=0;rows_total=0;paired=0;source_all_bytes=0
    for p in sorted((ROOT/'sources/annotations').glob('*.csv')):
        b=p.read_bytes();charge+=3*len(b);source_all_bytes+=len(b)
        rows=list(csv.DictReader(io.StringIO(b.decode())));files[p.name]=[]
        for j,r in enumerate(rows):
            on=float(r['onset_s']);off=float(r['offset_s']);lab=r['label']
            assert math.isfinite(on) and math.isfinite(off) and 0<=on<off<=wv[p.name[:-4]]['seconds']
            if j:assert on>=float(rows[j-1]['offset_s'])
            quantum=max(quantum,abs(on*32000-round(on*32000)),abs(off*32000-round(off*32000)))
        rows_total+=len(rows);paired+=1;j=0
        while j<=len(rows)-3:
            r=rows[j:j+3];labs=[x['label'] for x in r]
            if labs==['a','b','c']:
                v=[]
                for k,x in enumerate(r):
                    v.append(float(x['offset_s'])-float(x['onset_s']))
                    if k<2:v.append(float(r[k+1]['onset_s'])-float(x['offset_s']))
                assert min(v)>0
                key=p.name+':'+str(j);features[key]=np.array([math.log(a) for a in v]);labels[key]=labs
                files[p.name].append(key);j+=3
            else:j+=1
    trainkeys=[k for name in f['teaching'] for k in files[name]];train=np.array([features[k] for k in trainkeys])
    # Independently aggregate equally weighted recording means, then scalar products.
    w=np.array([1/19/len(files[k.rsplit(':',1)[0]]) for k in trainkeys])
    mu=np.array([sum(float(wi*xi[j]) for wi,xi in zip(w,train)) for j in range(5)])
    c=np.array([[sum(float(wi*(xi[j]-mu[j])*(xi[k]-mu[k])) for wi,xi in zip(w,train))/(1-float(np.sum(w*w))) for k in range(5)] for j in range(5)])
    c=.8*c+.2*np.diag(np.diag(c))+np.eye(5)*.002**2;prec=np.linalg.inv(c)
    shuffled=[]
    for x,key in zip(train,trainkeys):
        seed=int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],'big');shuffled.append(x[np.random.default_rng(seed).permutation(5)])
    sx=np.array(shuffled);smu=np.sum(w[:,None]*sx,axis=0);sr=sx-smu
    sc=np.einsum('n,ni,nj->ij',w,sr,sr)/(1-np.dot(w,w));sc=.8*sc+.2*np.diag(np.diag(sc))+np.eye(5)*.002**2
    sp=np.linalg.inv(sc);lo=min((train-mu).mean(axis=1));hi=max((train-mu).mean(axis=1))
    def calc(x,m):
        d=x-mu
        if m=='prototype':return math.sqrt(sum(z*z for z in d)/5)
        if m=='nearest':return min(math.sqrt(sum((a-b)**2 for a,b in zip(x,t))/5) for t in train)
        if m in ['covariance','shuffled_covariance']:
            z=d if m=='covariance' else x-smu;p=prec if m=='covariance' else sp
            return math.sqrt(max(0,sum(z[j]*p[j,k]*z[k] for j in range(5) for k in range(5))/5))
        if m=='absent':return 0.
        u=sum(d)/5;v=sum((z-u)**2 for z in d)/5
        if m=='bounded_tempo':v+=max(lo-u,u-hi,0)**2
        return math.sqrt(v)
    maxima={};checked=0;seqn=0;diagnostic={};decompositions=[]
    for prefix in ['MAIN','REVISION']:
        npzpath=ROOT/(prefix+'_SCORES.npz');charge+=npzpath.stat().st_size
        with np.load(npzpath) as z:
            arr={k:z[k].copy() for k in z.files};charge+=sum(x.nbytes for x in arr.values())
        summary=json.loads((ROOT/(prefix+'_SUMMARY.json')).read_text())
        keys=arr['eval_keys'].tolist();x=np.array([features[k] for k in keys]);seqn+=len(keys)
        assert all(labels[k]==['a','b','c'] for k in keys)
        maxima[prefix+'_source_features']=float(np.max(np.abs(x-arr['eval_x'])))
        maxima[prefix+'_source_training']=float(np.max(np.abs(train-arr['train_x'])))
        diffs=[];orig=[]
        for j,m in enumerate(arr['methods'].tolist()):
            oo=np.array([calc(v,m) for v in x]);diffs.extend(abs(oo-arr['original'][j]));checked+=len(x)
            for k,(loc,factor) in enumerate(zip(arr['challenge_locations'],arr['challenge_factors'])):
                idx={'global':[0,1,2,3,4],'duration_b':[2],'gap_ab':[1],'duration_c':[4]}[str(loc)]
                altered=x.copy();altered[:,idx]+=math.log(float(factor))
                cc=np.array([calc(v,m) for v in altered]);diffs.extend(abs(cc-arr['edits'][j,k]));checked+=len(x)
                if m=='covariance' and loc=='duration_b' and factor in [.8,1.2]:
                    delta=np.zeros(5);delta[2]=math.log(float(factor))
                    for key,v,cost0,cost1 in zip(keys,x,oo,cc):
                        cross=2*float((v-mu)@prec@delta)/5;positive=float(delta@prec@delta)/5
                        assert abs((cost1**2-cost0**2)-(cross+positive))<1e-10
                        if cost1<cost0-1e-12:
                            decompositions.append({'phase':prefix,'key':key,'factor':float(factor),
                               'cross':cross,'positive':positive,'delta_squared_cost':float(cost1**2-cost0**2)})
        maxima[prefix+'_all_scalar_costs']=float(max(diffs));assert maxima[prefix+'_all_scalar_costs']<1e-10
        # Postvalidation score-separation diagnostic; no threshold is adopted.
        groups=arr['eval_groups'];uw=np.unique(groups);ew=np.array([1/len(uw)/sum(groups==g) for g in groups])
        diagnostic[prefix]={}
        for m in ['prototype','nearest','covariance']:
            j=arr['methods'].tolist().index(m);natural=arr['original'][j];cut=summary['methods'][m]['threshold']
            vals={}
            for factor in [.8,1.2]:
                k=next(i for i,(loc,ff) in enumerate(zip(arr['challenge_locations'],arr['challenge_factors'])) if loc=='duration_b' and ff==factor)
                altered=arr['edits'][j,k]
                # Empirical probability altered cost exceeds a separately drawn natural cost.
                auc=sum(float(ew[a]*ew[b]*(float(altered[a]>natural[b])+0.5*float(altered[a]==natural[b]))) for a in range(len(x)) for b in range(len(x)))
                vals[str(factor)]={'weighted_score_AUC':auc,'frozen_rejection':float(np.dot(ew,altered>cut+1e-12))}
            diagnostic[prefix][m]=vals
    stats={}
    for name,idx in [('duration_b',2),('duration_c',4)]:
        v=np.exp(train[:,idx]);stats[name]={'teaching_mean_ms':float(np.dot(w,v)*1000),
            'pooled_teaching_5_50_95_ms':(np.quantile(v,[.05,.5,.95])*1000).tolist(),
            'teaching_range_ms':[float(v.min()*1000),float(v.max()*1000)],
            'teaching_log_sd_equal_recording':float(np.sqrt(np.dot(w,(train[:,idx]-mu[idx])**2)))}
    labels_original=['a','b','c'];altered=[list(reversed(labels_original)),labels_original[1:]+labels_original[:1]]
    gate={'original_accepts':seqn*int(labels_original==['a','b','c']),
       'altered_rejects':seqn*sum(q!=['a','b','c'] for q in altered),
       'altered_total':2*seqn,'bag_gate_altered_accepts':seqn*sum(sorted(q)==sorted(labels_original) for q in altered),
       'scope':'executed symbolic equality control; not acoustic recognition, main-summary booleans were declarative'}
    report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'self-audit, not external independent review',
      'frozen_pins_checked':pins,'source_wav_csv_pairs':paired,'source_annotation_rows':rows_total,
      'abc_renditions_all39':sum(len(x) for x in files.values()),'source_csv_bytes':source_all_bytes,
      'max_32000Hz_grid_residual_samples':quantum,'checks':maxima,'scalar_costs_reconstructed':checked,
      'sequence_control':gate,'timing_support':stats,
      'postvalidation_score_separation':diagnostic,'b_edit_decrease_witnesses':decompositions,
      'decrease_witness_count':len(decompositions),
      'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'environment':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform()},
      'scientific_read_decoded_hash_bytes_this_pass':charge}
    (ROOT/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text());ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'source and scalar self-audit','kind':'pins+CSV read/decode/hash+NPZ decoded arrays','bytes':charge})
    ledger['peak_rss_bytes_measured_max']=max(ledger['peak_rss_bytes_measured_max'],report['peak_rss_bytes'])
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['b_edit_decrease_witnesses','postvalidation_score_separation']},indent=2))
if __name__=='__main__':main()

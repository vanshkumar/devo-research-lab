"""Direct arithmetic on the first downloaded animal; no model fitting."""
import argparse, datetime, json, math, pathlib, resource, statistics, sys, zipfile, re
P=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=pathlib.Path,default=P/'FIRST_DATA_CHECK.json')
args=parser.parse_args()
def load(name):
    return [[float(x) for x in line.split()] for line in (P/name).open() if line.strip()]
def avg(x):
    y=[a for a in x if math.isfinite(a)]
    return sum(y)/len(y) if y else None
y=load('0_gcamp.txt'); t=[r[0] for r in load('0_t.txt')]
lab=(P/'0_labels.txt').read_text().splitlines()
st=[int(x) for x in (P/'0_stim_volume_i.txt').read_text().split()]
sn=[int(x) for x in (P/'0_stim_neurons.txt').read_text().split()]
assert len(y)==len(t) and all(len(r)==len(lab) for r in y)
assert len(st)==len(sn) and all(0<=i<len(t) for i in st)
assert all(a<b for a,b in zip(t,t[1:]))
records=[]
for k,(i,j) in enumerate(zip(st,sn)):
    if j<0: continue
    pre=[q for q,v in enumerate(t) if -10<=v-t[i]<-1]
    post=[q for q,v in enumerate(t) if 2<=v-t[i]<12]
    vals=[]
    for c,label in enumerate(lab):
        if not label.strip() or c==j: continue
        a=avg([y[q][c] for q in pre]); b=avg([y[q][c] for q in post])
        if a is not None and b is not None:
            vals.append({'neuron_index':c,'label':label,'pre_mean':a,'post_mean':b,'post_minus_pre':b-a,
                         'pre_finite':sum(math.isfinite(y[q][c]) for q in pre),'post_finite':sum(math.isfinite(y[q][c]) for q in post)})
    records.append({'event':k,'zero_based_frame':i,'timestamp':t[i],'target_index':j,'target_label':lab[j],
                    'pre_frames':len(pre),'post_frames':len(post),'downstream_available':len(vals),
                    'median_absolute_post_minus_pre':statistics.median(abs(v['post_minus_pre']) for v in vals),
                    'example_downstream':vals[:5]})
    if len(records)==3: break
out={'executed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'real event alignment arithmetic executed; source gate NOT yet passed',
     'record_name':(P/'0_ds_name.txt').read_text().strip(),'shape':[len(y),len(y[0])],
     'labeled_columns':sum(bool(x.strip()) for x in lab),'finite_values':sum(math.isfinite(v) for r in y for v in r),
     'total_values':len(y)*len(y[0]),'duration':t[-1]-t[0],
     'dt_median':statistics.median(b-a for a,b in zip(t,t[1:])),
     'dt_min':min(b-a for a,b in zip(t,t[1:])), 'dt_max':max(b-a for a,b in zip(t,t[1:])),
     'event_count':len(st),'target_status_counts':{str(j):sn.count(j) for j in sorted(set(sn)) if j<0},
     'event_spacing_seconds_min':min(t[b]-t[a] for a,b in zip(st,st[1:])),
     'real_event_checks':records,'scientific_claim':'available measured pre/post fluorescence, no forecast utility or causal contrast tested',
     'unresolved':['animal identity versus session identity','stimulus duration per event','raw-export preprocessing provenance','license of external OSF files'],
     'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'this_pass_source_read_bytes':sum((P/n).stat().st_size for n in ['0_gcamp.txt','0_t.txt','0_labels.txt','0_stim_volume_i.txt','0_stim_neurons.txt','0_ds_name.txt']),
     'this_pass_decoded_values_byte_charge':len(y)*len(y[0])*8+len(t)*8}
args.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
paper=(P/'paper_text.txt').read_text()
for term in ['113','animal','recordings','control','photobleach','preprocess','smoothing','stimulus-locked']:
    print('\nTERM',term)
    for m in list(re.finditer(re.escape(term),paper,re.I))[:10]: print(paper[max(0,m.start()-150):m.end()+250])
z=zipfile.ZipFile(P/'code_v1.1.zip')
print('DATASET FILES', [n for n in z.namelist() if any(x in n.lower() for x in ['list.txt','dataset','funatlas_list'])])
code=z.read('pumpprobe-1.1/pumpprobe/Funatlas.py').decode().splitlines()
print('EXPORT CODE lines 275-320\n'+'\n'.join(code[274:320]))

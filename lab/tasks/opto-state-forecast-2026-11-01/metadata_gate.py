import json, pathlib, collections, zipfile, re, resource, datetime
P=pathlib.Path(__file__).resolve().parent
rows=[]
for a in range(3):
    labels=(P/f'{a}_labels.txt').read_text().splitlines()
    st=[int(x) for x in (P/f'{a}_stim_volume_i.txt').read_text().split()]
    sn=[int(x) for x in (P/f'{a}_stim_neurons.txt').read_text().split()]
    t=[float(x) for x in (P/f'{a}_t.txt').read_text().split()]
    counts=collections.Counter(labels[j].strip() for j in sn if 0<=j<len(labels))
    rows.append({'record':a,'record_name':(P/f'{a}_ds_name.txt').read_text().strip(),
                 'frames':len(t),'neurons':len(labels),'events':len(sn),'source_counts':dict(counts),
                 'valid_named_events':sum(v for k,v in counts.items() if k and not k[0].isdigit()),
                 'timestep':t[1]-t[0], 'max_timestep_error':max(abs(b-a-0.5) for a,b in zip(t,t[1:])),
                 'duration':t[-1]-t[0],'duplicate_nonempty_labels':dict((k,v) for k,v in collections.Counter(x.strip() for x in labels if x.strip()).items() if v>1)})
z=zipfile.ZipFile(P/'code_v1.1.zip')
hits=[]
for name in ['pumpprobe-1.1/pumpprobe/Funatlas.py','pumpprobe-1.1/pumpprobe/Fconn.py','pumpprobe-1.1/scripts/fconnectivity/make_data_archive.py','pumpprobe-1.1/scripts/fconnectivity/funatlas_plot_intensity_map.py']:
    lines=z.read(name).decode().splitlines()
    for i,l in enumerate(lines):
        if any(w in l for w in ['-2','-3','photobl','smooth','remove_spikes','nan_th','signal_kwargs','exclude_tags','stim_crosscheck','from_datasets']):
            if '-2' in l and not any(w in l for w in ['stim','target']): continue
            hits.append(name+':'+str(i+1)+'\n'+'\n'.join(lines[max(0,i-2):i+4]))
(P/'METADATA_CHECK.json').write_text(json.dumps({'executed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':rows,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2)+'\n')
(P/'PREPROCESSING_CODE.txt').write_text('\n\n'.join(hits))
print(json.dumps(rows,indent=2)); print('\n'.join(hits)[:19000])
print('CODE_LICENSE',z.read('pumpprobe-1.1/LICENSE').decode()[:500])

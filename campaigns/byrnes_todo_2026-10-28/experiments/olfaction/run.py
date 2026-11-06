"""Analyze frozen public unionizes; pixels are measurements, experiments are units."""
import csv, hashlib, json, math, pathlib, statistics

H=pathlib.Path(__file__).resolve().parent
D=H.parents[1]/'data/olfaction'
TARGETS={961:'PIR',1097:'HY',38:'PVH',390:'SO',223:'ARH',512:'CB'}

def main():
    for m in json.loads((D/'manifest.json').read_text()):
        assert hashlib.sha256((D/m['file']).read_bytes()).hexdigest()==m['sha256']
    metadata=json.loads((D/'experiments.json').read_text())['msg']
    chosen=[m for m in metadata if m.get('structure_id')==507 or m.get('primary_injection_structure_id')==507]
    rows=json.loads((D/'unionizes.json').read_text())['msg']
    index={(r['section_data_set_id'],r['structure_id'],r['is_injection']):r for r in rows}
    assert len(index)==len(rows), 'Duplicate experiment/structure/compartment'
    assert all(r['hemisphere_id']==3 for r in rows)
    errors=[abs(r['projection_density']-r['sum_projection_pixels']/r['sum_pixels']) for r in rows if r['sum_pixels']]
    assert max(errors)<1e-10
    out=[]
    for m in chosen:
        eid=m['data_set_id'];root=index[eid,997,True];bulb=index[eid,507,True]
        purity=bulb['sum_projection_pixels']/root['sum_projection_pixels']
        assert 0<=purity<=1+1e-10
        record=dict(experiment_id=eid,cre_line=(m.get('transgenic_line') or {}).get('name','wildtype'),injection_structures=m['injection_structures'],mob_signal_fraction=purity)
        for sid,label in TARGETS.items():
            r=index[eid,sid,False]  # Missing is not silently converted to zero.
            record[label+'_density']=r['projection_density']
            record[label+'_normalized_volume']=r['normalized_projection_volume']
            assert math.isclose(r['normalized_projection_volume'],r['projection_volume']/root['projection_volume'],rel_tol=1e-7,abs_tol=1e-12)
        out.append(record)
    with (H/'per_experiment.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
    groups={}
    for name,cut in [('all',0),('clean90',.9),('clean80',.8)]:
        subset=[r for r in out if r['mob_signal_fraction']>=cut]
        stats={}
        for label in TARGETS.values():
            x=[r[label+'_density'] for r in subset]
            stats[label]=dict(n=len(x),median=statistics.median(x) if x else None,min=min(x) if x else None,max=max(x) if x else None,greater_than_CB=sum(r[label+'_density']>r['CB_density'] for r in subset),median_normalized_volume=statistics.median([r[label+'_normalized_volume'] for r in subset]) if x else None)
        groups[name]=dict(n=len(subset),ids=[r['experiment_id'] for r in subset],stats=stats)
    # PIR is an assay recovery control, not a p-value or a universal signal threshold.
    assert all(r['PIR_density']>r['CB_density'] for r in out)
    result=dict(experiments=len(out),rows=len(rows),max_density_identity_error=max(errors),positive_control_PIR_above_CB_all=True,groups=groups,interpretation='Summary fluorescence only; no proof of terminals, monosynaptic route, innate function or OR37 coverage.')
    (H/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

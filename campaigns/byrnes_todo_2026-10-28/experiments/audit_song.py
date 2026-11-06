"""Root independent extraction using openpyxl, not the worker's XML extractor."""
import csv,json,pathlib,statistics,math,xml.dom.minidom as dom
import openpyxl
H=pathlib.Path(__file__).resolve().parent;D=H.parent/'data/song_learning';S=H/'song_learning'
w=openpyxl.load_workbook(D/'fig3.xlsx',read_only=True,data_only=True)
rows=[list(r) for r in w['e.syllable_traces'].iter_rows(values_only=True)]
mean=list(next(w['f.population_mean'].iter_rows(values_only=True)))
assert len(rows)==25 and all(len(r)==600 for r in rows)
reconstructed=[statistics.mean(r[j] for r in rows) for j in range(600)]
assert max(abs(a-b) for a,b in zip(mean,reconstructed))<1e-12
stored=json.loads((S/'summary.json').read_text())['source']
assert math.isclose(reconstructed[-1],stored['endpoint_mean'],abs_tol=1e-12)
assert sum(r[-1]>0 for r in rows)==25
# Robustness of the selected endpoint to worst-case removal of up to half the
# syllable rows; descriptive, not a confidence statement about six birds.
endpoints=sorted(r[-1] for r in rows)
worst_remaining=statistics.mean(endpoints[:13])
assert worst_remaining>0
zero_origin=all(r[0]==0 for r in rows)
null=list(next(w['f.shuffle_mean'].iter_rows(values_only=True)))
upper=[r[0] for r in w['f.shuffle_pvalue_upper'].iter_rows(values_only=True)]
assert len(null)==len(upper)==600
result=dict(independent_reader='openpyxl',n_rows=25,n_columns=600,mean_max_difference=max(abs(a-b) for a,b in zip(mean,reconstructed)),endpoint_mean=reconstructed[-1],worst_remaining_13_syllables_mean=worst_remaining,all_zero_origin=zero_origin,endpoint_exceeds_supplied_null_envelope=reconstructed[-1]>upper[-1],limitations=['No independent bird identifiers; worst-case syllable deletion is not bird-held-out validation.','Origin zero is definitional, not absence of learning.','Published shuffled envelope is supplied, not re-created from per-rendition data.','No novelty or causal template-acquisition inference from Fig3 association.'])
members=D/'fig2_members';mapping=json.loads((members/'sheet_map.json').read_text())
def scalar_values(sheet):
    tree=dom.parse(str(members/mapping[sheet].replace('/','__')))
    cells=tree.getElementsByTagName('c')
    values={c.getAttribute('r'):float(c.getElementsByTagName('v')[0].firstChild.data) for c in cells}
    assert set(values)=={'A'+str(i) for i in range(1,26)}
    return [values['A'+str(i)] for i in range(1,26)]
closer=scalar_values('g.Closer_vals');farther=scalar_values('g.Farther_vals')
differences=[a-b for a,b in zip(closer,farther)]
followup=json.loads((S/'followup_summary.json').read_text())
assert min(differences)>0 and math.isclose(statistics.mean(differences),followup['paired_difference_mean'],abs_tol=1e-14)
result['independent_promoted_panel']=dict(reader='stdlib minidom, explicit cell coordinates, statistics.mean',n_pairs=25,mean=statistics.mean(differences),min=min(differences),max=max(differences),all_positive=True)
(H/'song_independent_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

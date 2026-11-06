"""Independent metadata-only reconciliation; never reads expression outcomes."""
from pathlib import Path
import hashlib, json
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
obs_path = OUT.parents[1] / 'inputs/obs.csv'
old_path = ROOT / 'campaigns/byrnes_todo_2026-10-28/data/atlas/cluster_annotations_and_statistics.txt'
o = pd.read_csv(obs_path)
a = pd.read_csv(old_path, sep='\t')
o['cluster_id'] = o.C4_named.str.split().str[0]
old = a[a.clusterlevel == 'C4'][['cluster_id','cluster_name','ncells']]
new = o[o.cluster_id.str.startswith('C4-')].groupby('cluster_id').size().rename('current_n')
r = old.merge(new, on='cluster_id', how='outer')
r['delta'] = r.current_n-r.ncells
r.to_csv(OUT/'cluster_reconciliation.csv',index=False)
donors = o[o.cluster_id.isin(['C4-313','C4-296','C4-312','C4-315'])].groupby(['cluster_id','Dataset','donor_id']).size().rename('n').reset_index()
donors.to_csv(OUT/'candidate_comparison_donors.csv',index=False)
summary = {'obs_sha256': hashlib.sha256(obs_path.read_bytes()).hexdigest(), 'old_table_sha256':hashlib.sha256(old_path.read_bytes()).hexdigest(), 'current_cells':len(o), 'current_neuronal_cells':int((o.C0_named == 'C0-3 Neuron').sum()), 'current_C4_categories_including_inherited_non_neuronal_C3':int(o.C4_named.nunique()), 'current_neuronal_C4_categories':int(o.loc[o.C0_named == 'C0-3 Neuron','C4_named'].nunique()), 'old_C4_rows':len(old), 'changed_or_unmatched_C4_counts':r.loc[r.delta != 0].to_dict('records'), 'all_named_C4_match':bool(set(o.loc[o.cluster_id.str.startswith('C4-'),'C4_named']) == set(old.cluster_name)), 'candidate_donors':donors[donors.cluster_id == 'C4-313'].to_dict('records'), 'interpretation':'Same aggregate C4 sizes and names support snapshot correspondence, but old barcode roster was not available; exact old/current cell identity is not established.'}
(OUT/'metadata_reconciliation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))

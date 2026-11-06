"""Independently check exported depth/QC against the acquired sparse matrix."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import sparse

OUT = Path(__file__).resolve().parent
CAMPAIGN = OUT.parents[1]
o = pd.read_csv(CAMPAIGN/'inputs/peptide_obs.csv')
v = pd.read_csv(CAMPAIGN/'inputs/raw_var.csv')
x = sparse.load_npz(CAMPAIGN/'inputs/peptide_counts.npz')
mt = v.feature_name.str.startswith('MT-').to_numpy()
o['direct_total'] = np.asarray(x.sum(axis=1)).ravel()
o['direct_nfeature'] = np.diff(x.indptr)
o['mitochondrial_count'] = np.asarray(x[:,mt].sum(axis=1)).ravel()
o['mt_fraction_raw_denominator'] = o.mitochondrial_count/o.direct_total
o['mt_fraction_metadata_denominator'] = o.mitochondrial_count/o.nCount_RNA
o['mt_fraction_exported_harmonized'] = o.percent_mt / np.where(o.Dataset == 'Tadross',100,1)
assert np.array_equal(o.raw_total,o.direct_total)
assert np.array_equal(o.raw_nfeature,o.direct_nfeature)
summary = {'matrix_shape':x.shape,'mitochondrial_genes':v.loc[mt,'feature_name'].tolist(),'groups':[]}
for study,z in o.groupby('Dataset'):
    diff = z.nCount_RNA-z.direct_total
    summary['groups'].append({'study':study,'n':len(z),'raw_total_greater_than_metadata':int((diff<0).sum()),'raw_nfeature_greater_than_metadata':int((z.direct_nfeature>z.nFeature_RNA).sum()),'count_deficit_min_median_max':np.quantile(diff,[0,.5,1]).tolist(),'count_deficit_fraction_min_median_max':np.quantile(diff/z.nCount_RNA,[0,.5,1]).tolist(),'mt_harmonized_vs_metadata_denominator_max_absolute_error':float(np.abs(z.mt_fraction_exported_harmonized-z.mt_fraction_metadata_denominator).max()),'mt_exported_over_raw_fraction_quantiles':(z.percent_mt/z.mt_fraction_raw_denominator).quantile([0,.1,.5,.9,1]).to_dict()})
cols=['row_index','Dataset','donor_id','Sample_ID','C4_named','nCount_RNA','nFeature_RNA','percent_mt','direct_total','direct_nfeature','mitochondrial_count','mt_fraction_raw_denominator','mt_fraction_metadata_denominator','mt_fraction_exported_harmonized']
o[cols].to_csv(OUT/'depth_mt_reconciliation.csv',index=False)
(OUT/'depth_mt_reconciliation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))

"""Empirical pilot from pinned HYPOMAP summary tables; no cell-level biological inference."""
import pathlib,json,hashlib,csv,math
import numpy as np,pandas as pd
BASE=pathlib.Path(__file__).resolve().parents[2];D=BASE/'data/atlas';H=pathlib.Path(__file__).parent
TARGETS=['OXT','AVP','OXTR','AVPR1A','ESR1','GAL','PRLR','TAC1','TAC2'];CONTROLS=['POMC','AGRP','HCRT']

def main():
 manifest=json.loads((D/'manifest.json').read_text())
 for f in manifest['files']:
  p=BASE/f['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
 a=pd.read_csv(D/'cluster_annotations_and_statistics.txt',sep='\t');m=pd.read_csv(D/'marker_genes_all.txt',sep='\t');e=pd.read_csv(D/'matched_clusters_scviCorPruned.tsv',sep='\t');c=pd.read_csv(D/'human_mouse_corresponding_clusters.txt',sep='\t');s=pd.read_csv(D/'sup_sample_statistics.txt',sep='\t')
 a4=a[a.clusterlevel=='C4'].copy();assert a4.cluster_id.is_unique
 assert set(e['from']).issubset(set(a4.cluster_name))
 assert set(zip(e['from'],e.to))==set(zip(c.human_cluster,c.mouse_cluster))
 assert np.allclose(e.similarity,c.similarity)
 assert e.groupby('from').size().to_dict()==e.groupby('from').from_occ.first().astype(int).to_dict()
 assert e.groupby('to').size().to_dict()==e.groupby('to').to_occ.first().astype(int).to_dict()
 donors=s.Donor_ID.unique().tolist();assert all(d in a.columns for d in donors)
 donor_pct=a4[donors].values/100
 a4['donor_max_pct']=a4[donors].max(1);a4['donors_detected']=(a4[donors]>0).sum(1);a4['donor_effective_n']=1/(donor_pct**2).sum(1)
 a4['human_partners']=a4.cluster_name.map(e.groupby('from').size()).fillna(0).astype(int)
 def cat(name):
  q=e[e['from']==name]
  if not len(q):return 'unmatched'
  if len(q)>1:return '1:N'
  return '1:1' if q.to_occ.iloc[0]==1 else 'M:1'
 a4['match_type']=a4.cluster_name.map(cat)
 mc=m[m.cluster.str.startswith('C4-')].copy();mc['rank']=mc.groupby('cluster').specificity.rank(method='min',ascending=False)
 selected=mc[mc.gene.isin(TARGETS+CONTROLS+['TAC3'])].copy()
 selected=selected.merge(a4[['cluster_id','ncells','donor_max_pct','donors_detected','donor_effective_n','human_partners','match_type']],left_on='cluster',right_on='cluster_id',how='left',validate='many_to_one')
 assert selected.ncells.notna().all()
 selected.to_csv(H/'target_marker_rows.csv',index=False)
 expanded=selected.merge(e[['from','to','similarity','from_occ','to_occ']],left_on='name',right_on='from',how='left')
 expanded.to_csv(H/'target_correspondence.csv',index=False)
 a4.to_csv(H/'cluster_mapping_summary.csv',index=False)
 summary=[]
 for gene in TARGETS+CONTROLS+['TAC3']:
  q=selected[selected.gene==gene]
  for top in [None,5,20]:
   z=q if top is None else q[q['rank']<=top]
   summary.append(dict(gene=gene,selection='all_exported_markers' if top is None else 'top'+str(top),n_clusters=len(z),n_unmatched=int((z.match_type=='unmatched').sum()),n_1to1=int((z.match_type=='1:1').sum()),n_1toN=int((z.match_type=='1:N').sum()),n_Mto1=int((z.match_type=='M:1').sum()),median_donor_max_pct=float(z.donor_max_pct.median()) if len(z) else None))
 pd.DataFrame(summary).to_csv(H/'gene_summary.csv',index=False)
 # Known marker identity/control mappings are specified from source before these outcomes.
 def partners(cid):return e.loc[e['from'].str.startswith(cid+' '),'to'].tolist()
 controls=dict(pomc373_two_anxa2=len(partners('C4-373'))==2 and all('Anxa2.Pomc' in p for p in partners('C4-373')),pomc374_ttr=len(partners('C4-374'))==1 and 'Ttr.Pomc' in partners('C4-374')[0],agrp355_five=len(partners('C4-355'))==5 and all('Agrp' in p for p in partners('C4-355')),hcrt331_includes_hcrt=any('Hcrt' in p for p in partners('C4-331')),join_coverage=True)
 assert all(controls.values()),controls
 # Pooled marginal detection probabilities force a co-detection bound; not joint release/function.
 bounds=[]
 for cid in ['C4-296','C4-312','C4-313','C4-315']:
  q=mc[mc.cluster==cid].set_index('gene')
  if 'OXT' not in q.index or 'AVP' not in q.index:continue
  p=float(q.loc['OXT','pct.1']);v=float(q.loc['AVP','pct.1']);n=int(a4.set_index('cluster_id').loc[cid,'ncells'])
  bounds.append(dict(cluster=cid,n_nuclei=n,pct_OXT=p,pct_AVP=v,frechet_lower=max(0,p+v-1),frechet_upper=min(p,v),conservative_lower_with_3decimal_rounding=max(0,p+v-1-.001),caveat='pooled detected transcript marginals; assumes same cluster universe; no donor-level, release or functional coexpression claim'))
 pd.DataFrame(bounds).to_csv(H/'co_detection_bounds.csv',index=False)
 # Independent standard-library reconstruction of a target/control row and sharp bound.
 with (D/'marker_genes_all.txt').open() as f:raw=[r for r in csv.DictReader(f,delimiter='\t') if r['cluster']=='C4-313' and r['gene'] in ['OXT','AVP']]
 assert len(raw)==2 and max(0,sum(float(r['pct.1']) for r in raw)-1)>.64
 n=100;ka=73;kb=64;A=set(range(ka));B=set(range(n-kb,n));assert len(A&B)==ka+kb-n==37
 B=set(range(kb));assert len(A&B)==min(ka,kb)==64
 result=dict(commit=manifest['commit'],data_kind='author-derived filtered cluster summaries',n_annotation_C4=len(a4),n_C4_nuclei=int(a4.ncells.sum()),n_matched_human=e['from'].nunique(),n_matched_mouse=e.to.nunique(),n_edges=len(e),n_unmatched_human=int((a4.human_partners==0).sum()),global_match_types=a4.match_type.value_counts().to_dict(),target_and_control_summary=summary,positive_controls=controls,co_detection_bounds=bounds,filter='exported rows: adjusted P<0.0001 and specificity>1; not an expression matrix',independent_unit='descriptive cluster summaries; donors/cells not treated as replicate statistical tests',source_scope_discrepancy='Repo summary415 human C4,284 matched; paper reports413 integrated neuronal clusters,282 matched; both131 unmatched. Do not silently treat repository version as exact final supplementary tables.',symbol_correction='Predeclared mouse Tac2 symbol has human ortholog TAC3; TAC3 rows are exploratory addition. Missing AVPR1A is not absent expression.')
 (H/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

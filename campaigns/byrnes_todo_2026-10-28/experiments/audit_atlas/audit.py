"""Independent standard-library reconstruction of pooled/donor bounds, no atlas imports."""
import csv,pathlib,json,hashlib,itertools
from decimal import Decimal,ROUND_HALF_EVEN
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;D=R/'data/atlas';S=R/'sources/atlas'
manifest=json.loads((D/'manifest.json').read_text());lookup={r['file']:r for r in manifest['files']}
used=['data/atlas/cluster_annotations_and_statistics.txt','data/atlas/marker_genes_all.txt','data/atlas/sup_sample_statistics.txt','sources/atlas/supplementary_tables.R','sources/atlas/12_markers_mrtree.R','sources/atlas/stratified_wilcoxon_functions.R','data/atlas/parameters_human_hypo_v2.json']
for name in used:
 b=(R/name).read_bytes();assert hashlib.sha256(b).hexdigest()==lookup[name]['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==lookup[name]['git_blob']

def read(name):
 with (D/name).open() as f:return list(csv.DictReader(f,delimiter='\t'))
ann=read('cluster_annotations_and_statistics.txt');markers=read('marker_genes_all.txt');sample=read('sup_sample_statistics.txt');donors=sorted({r['Donor_ID'] for r in sample})
# Enumerate counts whose rounded proportions match displayed values. Independent of
# the main followup's Decimal ceil/floor interval implementation.
def exact_rounded_counts(n,value,places,scale):
 quantum=Decimal(10)**(-places);target=Decimal(value).quantize(quantum)
 return [k for k in range(n+1) if (Decimal(k)*scale/Decimal(n)).quantize(quantum,rounding=ROUND_HALF_EVEN)==target]
def inclusive_counts(n,value,places,scale,half_multiplier=1):
 eps=Decimal(5)*Decimal(10)**(-places-1)*half_multiplier;v=Decimal(value)
 return [k for k in range(n+1) if abs(Decimal(k)*scale/Decimal(n)-v)<=eps]

def witness(caps,a,b,avoid=None):
 n=sum(caps.values());joint=max(0,a+b-n);other=sorted(caps,key=lambda d:(d==avoid,-caps[d],d));remaining=joint;counts={d:[0,0,0,0] for d in caps} # both,Aonly,Bonly,neither
 for d in other:
  if d==avoid:continue
  take=min(remaining,caps[d]);counts[d][0]=take;remaining-=take
 assert remaining==0
 for category,need in [(1,a-joint),(2,b-joint),(3,n-a-b+joint)]:
  for d in sorted(caps):
   take=min(need,caps[d]-sum(counts[d]));counts[d][category]+=take;need-=take
  assert need==0
 assert all(sum(counts[d])==caps[d] for d in caps)
 assert sum(x[0]+x[1] for x in counts.values())==a and sum(x[0]+x[2] for x in counts.values())==b
 if avoid is not None:assert counts[avoid][0]==0
 return counts
results=[];witnesses=[]
for cid in ['C4-296','C4-312','C4-313','C4-315']:
 row=next(r for r in ann if r['cluster_id']==cid);n=int(row['ncells']);mr={r['gene']:r for r in markers if r['cluster']==cid and r['gene'] in ['OXT','AVP']};assert len(mr)==2
 gene={g:exact_rounded_counts(n,mr[g]['pct.1'],3,Decimal(1)) for g in ['OXT','AVP']};assert all(len(x)==1 for x in gene.values())
 caps_possible={d:exact_rounded_counts(n,row[d],2,Decimal(100)) for d in donors};assert all(len(x)==1 for x in caps_possible.values());caps={d:x[0] for d,x in caps_possible.items()};assert sum(caps.values())==n
 a=gene['OXT'][0];b=gene['AVP'][0];lo=max(0,a+b-n);hi=min(a,b);sortedcaps=sorted(caps.values(),reverse=True);mindon=next(k for k in range(len(donors)+1) if sum(sortedcaps[:k])>=lo);largest=max(caps,key=caps.get);outside=max(0,lo-caps[largest]);per={d:max(0,lo-(n-cap)) for d,cap in caps.items()}
 # Check inclusive-half ties and even a doubled rounding uncertainty envelope.
 alternatives={}
 for multiplier in [1,2]:
  gg={g:inclusive_counts(n,mr[g]['pct.1'],3,Decimal(1),multiplier) for g in ['OXT','AVP']};cc={d:inclusive_counts(n,row[d],2,Decimal(100),multiplier) for d in donors}
  alternatives[str(multiplier)]=dict(gene_feasible_counts=gg,donor_feasible_counts=cc,joint_min=max(0,min(gg['OXT'])+min(gg['AVP'])-n))
 base=witness(caps,a,b);assert sum(x[0]>0 for x in base.values())==mindon
 for d in donors:
  if per[d]==0:
   w=witness(caps,a,b,avoid=d)
   if cid=='C4-313':
    for dd,vals in w.items():witnesses.append(dict(cluster=cid,objective='zero_overlap_in_'+d,donor=dd,both=vals[0],OXT_only=vals[1],AVP_only=vals[2],neither=vals[3],donor_capacity=caps[dd]))
 # Specificity of each marker row: comparisonAll and same cluster/name as annotation.
 assert all(mr[g]['comparison']=='All' for g in mr)
 results.append(dict(cluster=cid,cluster_name=row['cluster_name'],n=n,pct_OXT=mr['OXT']['pct.1'],pct_AVP=mr['AVP']['pct.1'],OXT=a,AVP=b,joint_min=lo,joint_max=hi,donor_capacities=caps,largest_donor=largest,largest_capacity=caps[largest],outside_largest_min=outside,min_donor_contributors=mindon,per_donor_unavoidable_joint=per,rounding_alternatives=alternatives,min_false_binary_calls_for_zero_joint=lo,min_false_calls_over_observed_positive_gene_calls=lo/(a+b)))
# Independent exhaustive all-subset known-answer constraints, not the main optimizer.
checks=0
for n in range(1,7):
 ss=[set(i for i in range(n) if mask&(1<<i)) for mask in range(1<<n)]
 for a in range(n+1):
  for b in range(n+1):
   vals=[len(A&B) for A in ss if len(A)==a for B in ss if len(B)==b]
   assert min(vals)==max(0,a+b-n) and max(vals)==min(a,b);checks+=1
source_checks={}
for name,terms in [('stratified_wilcoxon_functions.R',['pct.1 <- round','rowSums(x = data_for_cells1 > thresh.min)','length(x = cells.1)','digits = 3','Subset to max.cells.per.ident']),('supplementary_tables.R',['dplyr::add_count(name="ncells")','round(cells_cluster_target / ncells *100,2)','p_val_adj < 0.0001 & specificity > 1']),('12_markers_mrtree.R',['neuron_seurat_object = readRDS','labelmat = mrtree_result$labelmat','all_markers_mrtree_list = findMarkers_tree2'])]:
 lines=(S/name).read_text().splitlines();source_checks[name]={t:[i+1 for i,l in enumerate(lines) if t in l] for t in terms};assert all(source_checks[name].values())
main=next(r for r in results if r['cluster']=='C4-313');assert (main['OXT'],main['AVP'],main['joint_min'],main['outside_largest_min'],main['min_donor_contributors'])==(303,205,199,125,3);assert set(main['per_donor_unavoidable_joint'].values())=={0}
with (H/'donor_zero_witnesses.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(witnesses[0]));w.writeheader();w.writerows(witnesses)
out=dict(commit=manifest['commit'],independent_results=results,exhaustive_marginal_controls=checks,source_line_checks=source_checks,interpretation='Conditional pooled observed-data bounds. Same barcode universe is supported by source metric definitions, not verified from individual barcodes. No claim of biological coexpression or contamination-read fraction.')
(H/'audit_result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(C4_313=main,exhaustive_marginal_controls=checks,source_line_checks=source_checks),indent=2))

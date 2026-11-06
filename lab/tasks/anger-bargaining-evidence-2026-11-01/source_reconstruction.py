import csv,io,json,math,statistics,hashlib,datetime,resource
from pathlib import Path
P=Path(__file__).resolve().parent
def load(name,skip=0):
 b=(P/'sources'/name).read_bytes()
 return b,list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))[skip:]
br,raw=load('Study1_rawdata.csv',2);bc,clean=load('Study1_cleandata.csv')
codes={'H':'1','A':'2'};conds=['H/H','H/A','A/H','A/A']
def branch(r):
 c=[c for c in conds if r['demand_'+c].strip()]
 assert len(c)==1
 return c[0]
def passed(r,c):return r['check_'+c+'_feel']==codes[c[0]] and r['check_'+c+'_communi']==codes[c[2]]
pair_checks=[]
for c in clean:
 i=int(c['id']);r=raw[i-1];z=branch(r)
 checks={'branch':(c['experience']+'/'+c['expression'])==z,
  'demand':float(c['demand'])==float(r['demand_'+z]),
  'limit_accept':float(c['limit_accept'])==float(r['limit_'+z+'_percent_a']),
  'limit_reject':float(c['limit_reject'])==float(r['limit_'+z+'_percent_r']),
  'age':float(c['age'])==float(r['age']),
  'gender':c['gender']==r['gender'], 'passed_checks':passed(r,z)}
 pair_checks.append({'source_position_id':i,**checks})
kept={int(c['id']) for c in clean}
excluded=[{'source_position_id':i,'condition':branch(r),'demand':float(r['demand_'+branch(r)]),
 'passed_checks':passed(r,branch(r)),
 'limit_accept':float(r['limit_'+branch(r)+'_percent_a']),
 'limit_reject':float(r['limit_'+branch(r)+'_percent_r'])} for i,r in enumerate(raw,1) if i not in kept]
cells={}
for z in conds:
 v=[float(r['demand']) for r in clean if r['experience']+'/'+r['expression']==z]
 cells[z]={'n':len(v),'mean_demand':statistics.mean(v),'sd_demand':statistics.stdev(v)}
# Reproduce factorial tests from the released clean table with simple four-cell algebra.
# Contrast estimates use equal cell weights; conventional homoskedastic residual MS.
resid=sum((float(r['demand'])-cells[r['experience']+'/'+r['expression']]['mean_demand'])**2 for r in clean)
mse=resid/(len(clean)-4)
vectors={'experienced_A_minus_H':[-.5,-.5,.5,.5],
 'communicated_A_minus_H':[-.5,.5,-.5,.5],
 'interaction_difference_of_differences':[1,-1,-1,1]}
contrasts={}
for k,w in vectors.items():
 est=sum(a*cells[z]['mean_demand'] for a,z in zip(w,conds))
 se=math.sqrt(mse*sum(a*a/cells[z]['n'] for a,z in zip(w,conds)))
 contrasts[k]={'estimate_percentage_points':est,'conventional_SE':se,'F1_140':(est/se)**2}
out={'calculated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'stage':'source-support reconstruction only, all Study1 exposed; not a main comparison',
 'raw_n':len(raw),'clean_n':len(clean),'clean_ids_unique':len(kept)==len(clean),
 'candidate_link':'clean numeric id = one-based raw participant row position (excluding two Qualtrics export header rows)',
 'checked_pairs':len(pair_checks),'all_checked_fields_exact':all(all(v for k,v in r.items() if k!='source_position_id') for r in pair_checks),
 'field_failure_counts':{k:sum(not r[k] for r in pair_checks) for k in pair_checks[0] if k!='source_position_id'},
 'raw_passed_check_n':sum(passed(r,branch(r)) for r in raw),
 'clean_cells':cells,'clean_factorial_contrasts':contrasts,
 'excluded_from_clean':excluded,
 'raw_sha256':hashlib.sha256(br).hexdigest(),'clean_sha256':hashlib.sha256(bc).hexdigest(),
 'payload_read_decode_hash_allowance_bytes':4*(len(br)+len(bc)),
 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(P/'SOURCE_RECONSTRUCTION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

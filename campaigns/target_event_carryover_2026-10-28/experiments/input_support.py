from analysis import *
from collections import Counter

def main():
 people=load('all_inputs',inputs_only=True);rows=[];totals=Counter()
 for p in people:
  c,j=p['c'],p['j'];part='development' if p['sn'] in SPLIT[p['file']]['development'] else 'validation'
  counts=Counter()
  for b in range(4):
   for loc in range(20,175):
    t=100+b*181+loc
    if c[t]!=0:continue
    old=bool(j[t-1]==0 and abs(c[t-1])==4);event=int(j[t]!=0)
    counts['all_index']+=1
    if old:counts['primary_precursor_support']+=1
    for h in range(1,6):
     if j[t+h]==0:
      counts[f'stationary_h{h}']+=1
      if old:counts[f'primary_precursor_stationary_h{h}']+=1
    counts[f'index_jump{event}']+=1
    if old:counts[f'primary_index_jump{event}']+=1
  row={'person':p['key'],'set':p['set'],'partition':part,**dict(counts)};rows.append(row)
  for k,v in counts.items():totals[(part,p['set'],k)]+=v
 with (ROOT/'outputs/input_support_person.csv').open('w') as f:
  fields=['person','set','partition']+sorted(set(k for r in rows for k in r)-{'person','set','partition'});w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 summary=[{'partition':part,'set':s,'counts':{k:v for (pa,ss,k),v in totals.items() if pa==part and ss==s}} for part in ['development','validation'] for s in ['A','B']]
 (ROOT/'outputs/input_support_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

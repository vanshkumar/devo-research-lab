from analysis import *

def run_loo(part='validation'):
 people=load(part);out=[]
 # Sets can be cached independently because omission in one leaves the other unchanged.
 full={}
 def setfit(pp):
  return curve_summary([fit(prepare(make_design(pp,h))) for h in range(1,6)])
 for f in FILES:full[f]=setfit([p for p in people if p['file']==f])
 for p in people:
  ss=setfit([q for q in people if q['file']==p['file'] and q['key']!=p['key']])
  summaries=[ss if f==p['file'] else full[f] for f in FILES];r=pooled_summary(summaries);out.append({'omitted':p['key'],**r})
 result={'part':part,'diagnostic_only':True,'rows':out,'min_estimate':min(r['estimate'] for r in out),'max_estimate':max(r['estimate'] for r in out)}
 (ROOT/'outputs'/f'{part}_leave_one_out.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='rows'})
if __name__=='__main__':run_loo()

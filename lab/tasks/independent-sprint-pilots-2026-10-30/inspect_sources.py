import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='2'
import json,re
from html.parser import HTMLParser
from common import ROOT,HERE,SOURCE,read,save,now,digest
import numpy, scipy, numba
class Text(HTMLParser):
    def __init__(self): super().__init__();self.parts=[]
    def handle_data(self,s): self.parts.append(s)

def main():
    source=ROOT/'sources/sensory_evaluator_feasibility_2026-10-28/primary.html'
    b=read(source,'saved_primary_article'); parser=Text();parser.feed(b.decode())
    text=re.sub(r'\s+',' ',' '.join(parser.parts))
    excerpts=[]
    for pattern in ('irregular','premotor timing','temporal','HVC'):
        matches=list(re.finditer(re.escape(pattern),text,re.I))
        for m in matches[:2]: excerpts.append({'term':pattern,'text':text[max(0,m.start()-200):m.end()+550]})
    states=[]
    for i in (100,101,102):
        p=ROOT/('campaigns/evaluator_optimization_2026-10-28/primary_snapshots/plant_%03d/state.pkl'%i)
        states.append({'plant':i,'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size})
    out={'time':now(),'environment':{'python':sys.version,'numpy':numpy.__version__,'scipy':scipy.__version__,'numba':numba.__version__},'source_article_sha256':digest(b),'timing_excerpts_for_source_inspection':excerpts,'admitted_saved_states':states,'license_note':'Existing source audit has no downloaded LICENSE; no redistribution/novelty permission is inferred. Public paper is used as scholarly evidence; only local generated outputs are delivered.'}
    save('SOURCE_INSPECTION.json',out); print(json.dumps(out,indent=2))
if __name__=='__main__':main()

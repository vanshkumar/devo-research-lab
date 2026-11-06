"""One-process sequential batch; no successor or parallel actors."""
import sys,json,time,datetime as dt
sys.dont_write_bytecode=True
from common import HERE,load_json,save,now
import teaching_pilot as p

def run(args):
    sys.argv=['teaching_pilot.py']+args;p.main()
def main():
    gates=[];started=now()
    for plant in (100,101,102):
        run(['--plant',str(plant),'--stage','learning','--search','per_order','--rounds','20','--only-oracle'])
        result=load_json(HERE/('outputs/teaching_learning_%03d_per_order_20.json'%plant),'derived_result')['results'][0]
        gates.append(result);save('outputs/oracle_gates.json',{'started':started,'gates':gates})
        if result['improvement']<.8:raise RuntimeError('Revised oracle gate failed: no further actor repair')
    for plant in (100,101,102):
        if not (HERE/('outputs/teaching_diagnostics_%03d.json'%plant)).exists():run(['--plant',str(plant),'--stage','diagnostics'])
        run(['--plant',str(plant),'--stage','learning','--search','per_order','--rounds','20'])
    save('outputs/teaching_batch_complete.json',{'started':started,'finished':now(),'plants':[100,101,102],'oracle_gates_passed':True,'jobs':0})
if __name__=='__main__':main()

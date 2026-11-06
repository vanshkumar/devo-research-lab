"""Offline reproduction into a NEW child directory; primary artifacts stay intact."""
import argparse,contextlib,datetime,io,json,pathlib,resource,runpy,sys,traceback
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='replay');a=p.parse_args()
    dest=(ROOT/a.output).resolve();assert ROOT in dest.parents and not dest.exists()
    parent=json.loads((ROOT/'ACQUISITION.json').read_text())
    assert parent['scientific_read_decoded_hash_bytes']+5000000<250000000
    dest.mkdir();(dest/'sources/annotations').mkdir(parents=True);charge=0
    for name in ['PROTOCOL.md','REVISION.md','development.py','evaluate.py','freeze.py','revise.py','audit.py','SOURCE_SUPPORT.json']:
        b=(ROOT/name).read_bytes();charge+=len(b);(dest/name).write_bytes(b)
    for p in (ROOT/'sources/annotations').glob('*.csv'):
        b=p.read_bytes();charge+=len(b);(dest/'sources/annotations'/p.name).write_bytes(b)
    (dest/'ACQUISITION.json').write_text(json.dumps({'web_operations':0,'web_charged_bytes':0,
       'direct_operations':[],'direct_ingress_bytes':0,'scientific_byte_passes':[],
       'scientific_read_decoded_hash_bytes':0,'peak_rss_bytes_measured_max':0,'offline_replay':True}))
    log=io.StringIO();report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'output':str(dest.relative_to(ROOT)),'network_operations':0,'status':'failed'}
    sys.path.insert(0,str(dest))
    try:
        with contextlib.redirect_stdout(log):
            for script,args in [('development.py',[]),('freeze.py',[]),('evaluate.py',['main']),
                                ('revise.py',['freeze']),('revise.py',['evaluate']),('audit.py',[])]:
                sys.argv=[str(dest/script)]+args;runpy.run_path(str(dest/script),run_name='__main__')
        checks={}
        for stage in ['MAIN','REVISION']:
            left=ROOT/(stage+'_SCORES.npz');right=dest/(stage+'_SCORES.npz')
            charge+=left.stat().st_size+right.stat().st_size
            with np.load(left) as aa,np.load(right) as bb:
                checks[stage]={}
                for key in aa.files:
                    x=aa[key];y=bb[key];charge+=x.nbytes+y.nbytes
                    checks[stage][key]=bool(np.array_equal(x,y));assert checks[stage][key]
        report.update(status='complete',all_saved_arrays_bit_exact=True,checks=checks)
    except Exception:
        report['error']=traceback.format_exc();log.write(report['error'])
    finally:
        child=json.loads((dest/'ACQUISITION.json').read_text());charge+=child['scientific_read_decoded_hash_bytes']
        child.update(web_operations=0,web_charged_bytes=0,direct_operations=[],direct_ingress_bytes=0,
          accounting_note='Entire replay was offline; frozen evaluation code historical web fields are removed here.')
        (dest/'ACQUISITION.json').write_text(json.dumps(child,indent=2)+'\n')
        report['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        report['scientific_read_decoded_hash_bytes_this_pass']=charge
        (ROOT/'REPLAY_CHECK.json').write_text(json.dumps(report,indent=2)+'\n');(dest/'REPLAY.log').write_text(log.getvalue())
        parent['scientific_read_decoded_hash_bytes']+=charge
        parent['scientific_byte_passes'].append({'operation':'full offline reproduction','kind':'scoped input copies+replayed CSV decode/pins+array comparisons','bytes':charge})
        parent['peak_rss_bytes_measured_max']=max(parent['peak_rss_bytes_measured_max'],report['peak_rss_bytes'])
        (ROOT/'ACQUISITION.json').write_text(json.dumps(parent,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
    if report['status']!='complete':raise SystemExit(1)
if __name__=='__main__':main()

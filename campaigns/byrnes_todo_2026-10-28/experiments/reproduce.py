"""Offline campaign reproduction from pinned local evidence, using this interpreter.

Run from anywhere: python /absolute/path/to/this/file.py
Acquisition is separate and opt-in; this script never downloads anything.
"""
import hashlib,json,os,pathlib,platform,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent;C=H.parent;ROOT=C.parents[1]

def main():
    manifest=json.loads((C/'INPUTS.json').read_text())
    for row in manifest['files']:
        p=C/row['path']
        assert p.is_file(),p
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],f'Changed input: {p}'
    scripts=['atlas/run.py','atlas/followup.py','imprinting/analyze_predispositions.py',
             'imprinting/analyze_learning.py','imprinting/audit_learning.py','imprinting/audit_archive.py',
             'song_learning/extract.py','song_learning/run.py','song_learning/followup.py',
             'olfaction/run.py','concept_finder/run.py','concept_finder/check.py',
             'sandbox/run.py','sandbox/followup.py','audit_song.py','audit_atlas/audit.py','figures.py']
    logs=C/'reproduction';logs.mkdir(exist_ok=True)
    env=dict(os.environ,MPLCONFIGDIR=str(C/'.mplconfig'),PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    rows=[]
    for s in scripts:
        p=H/s;assert p.is_file(),p
        name=s.replace('/','_').removesuffix('.py');t=time.monotonic()
        with (logs/(name+'.stdout')).open('w') as out,(logs/(name+'.stderr')).open('w') as err:
            r=subprocess.run([sys.executable,str(p)],cwd=ROOT,env=env,stdout=out,stderr=err)
        rows.append(dict(script=s,returncode=r.returncode,seconds=round(time.monotonic()-t,3),stderr_bytes=(logs/(name+'.stderr')).stat().st_size))
        result=dict(status='running' if r.returncode==0 else 'failed',python=sys.version,platform=platform.platform(),verified_inputs=len(manifest['files']),runs=rows)
        (C/'REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n')
        print(s,r.returncode,flush=True)
        if r.returncode:raise SystemExit(r.returncode)
    result['status']='passed'
    (C/'REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Offline reproduction passed; inspect REPRODUCTION.json and reproduction/ logs.')

if __name__=='__main__':main()

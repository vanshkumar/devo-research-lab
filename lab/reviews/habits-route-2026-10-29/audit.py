"""Independent metadata/source checks. Never opens a biological ZIP member.

Run with any Python >=3.9 from repo root. Only generated synthetic ZIP data is
passed to codecs; C++ teacher functions are copied from the pinned source.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import subprocess
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / 'sources/intervention_evidence_2026-10-29'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def directory():
    eocd = (SRC / 'habits_zip_eocd.bin').read_bytes()
    fields = struct.unpack('<4s4H2LH', eocd)
    sig, disk, startdisk, ndisk, n, size, start, comment = fields
    assert (sig, disk, startdisk, ndisk, n, comment) == (b'PK\x05\x06', 0, 0, 1095, 1095, 0)
    raw = (SRC / 'habits_zip_central.bin').read_bytes()
    assert len(raw) == size == 217903
    rows = []
    p = 0
    while p < len(raw):
        x = struct.unpack_from('<4s6H3L5H2L', raw, p)
        assert x[0] == b'PK\x01\x02'
        name = raw[p+46:p+46+x[10]].decode('utf-8' if x[3] & 2048 else 'cp437')
        rows.append(dict(path=name, compression_method=x[4], flags=x[3],
                         compressed_bytes=x[8], uncompressed_bytes=x[9],
                         crc32=f'{x[7]:08x}', local_header_offset=x[16]))
        p += 46 + x[10] + x[11] + x[12]
    assert len(rows) == n and p == size
    # Indexing every directory entry adds no trial exposure; all labels were
    # already read by the source task. Do not open the archive URL or a member.
    saved = json.loads((SRC / 'HABITS_ZIP_INDEX.json').read_text())
    assert rows == saved
    wm = [r for r in rows if '/Machine teaching-based tasks/Working memory task,' in r['path'] and r['path'].endswith('/Trial.txt')]
    assert wm == json.loads((SRC / 'HABITS_WM_INDEX.json').read_text())
    assert len(wm) == 15 and all(r['compression_method'] == 9 for r in wm)
    cohort = {k: sum('/'+k+'/' in r['path'] for r in wm) for k in ('MT/trained', 'Random/trained', 'Random/failed')}
    companions = [r['path'] for r in rows if '/Machine teaching-based tasks/Working memory task,' in r['path'] and not r['path'].endswith('/') and not r['path'].endswith('/Trial.txt')]
    return dict(entries=n, directory_bytes=size, directory_offset=start,
                archive_end=start+size+len(eocd), cohort=cohort,
                compressed_total=sum(r['compressed_bytes'] for r in wm),
                compressed_over_10MB=sum(r['compressed_bytes'] > 10_000_000 for r in wm),
                expanded_range=[min(r['uncompressed_bytes'] for r in wm), max(r['uncompressed_bytes'] for r in wm)],
                other_working_memory_files=companions,
                metadata_sha256={n:sha(SRC/n) for n in ('habits_zip_eocd.bin','habits_zip_central.bin')})


def synthetic_codec():
    # A stored DEFLATE block is also valid in Deflate64. This only tests this
    # shared subset, not extended-distance/length or dynamic-Huffman support.
    payload = b'SYNTHETIC prefix row 1\n' + b'SYNTHETIC later row\n' * 1000
    c = zlib.compressobj(level=0, wbits=-15)
    body = c.compress(payload) + c.flush()
    name = b'synthetic.txt'
    crc = zlib.crc32(payload)
    local = struct.pack('<4s5H3L2H', b'PK\x03\x04', 21, 0, 9, 0, 0, crc, len(body), len(payload), len(name), 0)+name
    cd = struct.pack('<4s6H3L5H2L', b'PK\x01\x02', 21, 21, 0, 9, 0, 0, crc, len(body), len(payload), len(name), 0, 0, 0, 0, 0, 0)+name
    eo = struct.pack('<4s4H2LH', b'PK\x05\x06', 0, 0, 1, 1, len(cd), len(local)+len(body), 0)
    path = HERE/'synthetic_method9.zip'
    path.write_bytes(local+body+cd+eo)
    try:
        with zipfile.ZipFile(path) as z:
            z.read('synthetic.txt')
        py = 'decoded'
    except Exception as e:
        py = f'{type(e).__name__}: {e}'
    r = subprocess.run(['/usr/bin/bsdtar', '-xOf', str(path), 'synthetic.txt'], capture_output=True)
    assert not r.stdout or r.stdout == payload
    return dict(synthetic_zip_bytes=path.stat().st_size, payload_bytes=len(payload),
                python_zipfile=py, bsdtar_exit=r.returncode, bsdtar_stderr=r.stderr.decode(),
                bsdtar_output_bytes=len(r.stdout), bsdtar_output_matches=r.stdout==payload,
                limitation='Method-9 stored-block subset only; no biological codec validation and no streaming output-cap proof.')


def teacher():
    src = (SRC/'habits_wm_MT_MT_Contrast.ino').read_text()
    structs = src[src.index('struct DATAModel{'):src.index('LOGISTIC actionmodel;')+len('LOGISTIC actionmodel;')]
    funcs = src[src.index('float sigmoid(float z)'):src.index('int exponent(float beta')]
    prefix = r'''
#include <cmath>
#include <cstdio>
using byte = unsigned char;
struct FakeSerial { void print(const char*) {} } Serial;
long random(long a, long b) { return a; }
float sgn(float);
byte TrialType = 1;
byte TrialTypeContrast[2] = {};
float W_star[7] = {0,10,-10,0,0,0,0};
'''
    main = r'''
void init(bool file) {
  model=LOGISTIC(); actionmodel=LOGISTIC();
  if(file) model.S0[1]=-.5f;
}
DATAModel datum(int i, int j, int y, int h=0) {
  DATAModel d; d.x[0]=1; d.x[1]=model.S0[i]; d.x[2]=model.S0[j];
  d.x[3]=h; d.x[4]=h; d.x[5]=(h==0)?0:1; d.x[6]=h; d.y=y; return d;
}
int select_after(DATAModel d, int i, int j) {
  UpdateMiceParams(&d,1);
  if(model.t%2==0) deepcopymodel();
  DATAModel next; int s=i>j?1:-1; int a=(2*d.y-1); int r=a*s;
  next.x[0]=1; next.x[3]=s; next.x[4]=a; next.x[5]=r; next.x[6]=a*r;
  SelectTrialType(&next,1,0);
  return 10*TrialTypeContrast[0]+TrialTypeContrast[1];
}
int main() {
  bool f=false;
  for(int i=0;i<5 && !f;i++) for(int j=0;j<5 && !f;j++) if(i!=j)
    for(int y=0;y<2 && !f;y++) for(int h=-1;h<=1 && !f;h++) {
      init(true); auto a=datum(i,j,y,h); int p=select_after(a,i,j);
      init(false); auto b=datum(i,j,y,h); int q=select_after(b,i,j);
      if(p!=q) {printf("{\"initial_file_witness\":{\"trial_indices\":[%d,%d],\"choice_right\":%d,\"synthetic_history\":%d,\"config_next\":[%d,%d],\"fallback_next\":[%d,%d]},",i,j,y,h,p/10,p%10,q/10,q%10); f=true;}
    }
  if(!f) printf("{\"initial_file_witness\":null,");
  bool found=false;
  // Each input sequence is artificial. This is a teacher/source witness,
  // not a fitted biological learning model or forecast.
  for(int n=2;n<=200 && !found;n+=2) {
    init(true);
    for(int t=0;t<n;t++) {
      int i=t%5, j=(t*3+1)%5; if(i==j) j=(j+1)%5;
      auto d=datum(i,j,(t%3==0)?0:1,(t%3)-1);
      UpdateMiceParams(&d,1); if(model.t%2==0) deepcopymodel();
    }
    LOGISTIC before=model, cached=actionmodel;
    for(int i=0;i<5 && !found;i++) for(int j=0;j<5 && !found;j++) if(i!=j)
      for(int y=0;y<2 && !found;y++) {
        model=before; actionmodel=cached; auto d=datum(i,j,y);
        int p=select_after(d,i,j);
        model=before; actionmodel=LOGISTIC();
        // The persisted teacher theta/m use four decimal places on reload.
        for(int k=0;k<7;k++) {
          model.theta[k]=std::round(model.theta[k]*10000)/10000;
          model.m[k]=std::round(model.m[k]*10000)/10000;
        }
        auto e=datum(i,j,y); int q=select_after(e,i,j);
        if(p!=q) {printf("\"cache_restart_witness\":{\"prior_synthetic_updates\":%d,\"next_update_t\":%d,\"trial_indices\":[%d,%d],\"choice_right\":%d,\"uninterrupted_next\":[%d,%d],\"reboot_reload_next\":[%d,%d]}",n,n+1,i,j,y,p/10,p%10,q/10,q%10);found=true;}
      }
  }
  if(!found) printf("\"cache_restart_witness\":null");
  printf(",");
  bool statefound=false;
  const float weights[]={2,3,4,5,6,8,10,.5f,1};
  for(float w:weights) for(int bias=-2;bias<=2 && !statefound;bias++)
    for(int i=0;i<5 && !statefound;i++) for(int j=0;j<5 && !statefound;j++) if(i!=j)
      for(int y=0;y<2 && !statefound;y++) {
        init(true); model.theta[0]=bias; model.theta[1]=w; model.theta[2]=-w; model.t=100;
        deepcopymodel(); LOGISTIC before=model, cached=actionmodel;
        auto d=datum(i,j,y); int p=select_after(d,i,j);
        model=before; actionmodel=LOGISTIC(); auto e=datum(i,j,y); int q=select_after(e,i,j);
        if(p!=q) {printf("\"admissible_state_cache_witness\":{\"initial_theta\":[%g,%g,%g,0,0,0,0],\"prior_t\":100,\"trial_indices\":[%d,%d],\"choice_right\":%d,\"cached_next\":[%d,%d],\"reset_next\":[%d,%d]}",float(bias),w,-w,i,j,y,p/10,p%10,q/10,q%10);statefound=true;}
      }
  if(!statefound) printf("\"admissible_state_cache_witness\":null");
  printf("}\n");
}
'''
    cpp = HERE/'teacher_synthetic.cpp'
    cpp.write_text(prefix+structs+'\n'+funcs+'\n'+main)
    subprocess.run(['/usr/bin/clang++','-std=c++17','-O0',str(cpp),'-o',str(HERE/'teacher_synthetic')], check=True, capture_output=True)
    r = subprocess.run([str(HERE/'teacher_synthetic')],check=True,capture_output=True,text=True)
    witnesses = json.loads(r.stdout)
    assert witnesses['admissible_state_cache_witness']
    # Independently reduce the source witness using Python doubles and sorted
    # candidate scores. The C++ path uses source float and strict row-order ties.
    witness = witnesses['admissible_state_cache_witness']
    theta = witness['initial_theta']
    i, j = witness['trial_indices']
    s0 = [-1, -.5, 0, .5, 1]
    x = [1, s0[i], s0[j], 0, 0, 0, 0]
    y = witness['choice_right']
    p = 1/(1+math.exp(-sum(a*b for a,b in zip(theta,x))))
    updated = [a-.01*(p-y)*b for a,b in zip(theta,x)]
    a = 2*y-1
    side = 1 if i>j else -1
    reward = a*side
    reduction = {}
    for mode, cache, codes in [('cached',theta,s0), ('reset',[0]*7,[-1,.5,0,.5,1]), ('reset_theta_same_encoding',[0]*7,s0)]:
        scores=[]
        for ii in range(5):
            for jj in range(5):
                if ii==jj: continue
                q=[1,codes[ii],codes[jj],side,a,reward,a*reward]
                py=1/(1+math.exp(-sum(v*w for v,w in zip(updated,q))))
                grad=[(py-int(ii>jj))*v for v in q]
                dw=[v-w for v,w in zip(cache,[0,10,-10,0,0,0,0])]
                score=.03**2*sum(v*v for v in grad)-2*.03*sum(v*w for v,w in zip(grad,dw))
                scores.append((score,ii,jj))
        scores.sort()
        reduction[mode]=dict(next_pair=list(scores[0][1:]),best_score=scores[0][0],runner_up_margin=scores[1][0]-scores[0][0])
        if mode in ('cached','reset'):
            assert reduction[mode]['next_pair']==witness[mode+'_next']
    return dict(extracted_functions_sha256=hashlib.sha256(funcs.encode()).hexdigest(),
                exact_source_functions=True, numeric_type='C++ source float; Apple clang, -O0; not a Teensy hardware match',
                witnesses=witnesses,
                independent_double_reduction=reduction,
                scope='Conditional hidden-state/initialization witnesses only; no claim both occurred in the deployed mice.')


def main():
    inputs = [SRC/n for n in ('habits_zip_eocd.bin','habits_zip_central.bin','HABITS_WM_INDEX.json','HABITS_ZIP_INDEX.json','habits_paper.xml')]
    plan=json.loads((SRC/'code_plan.json').read_text())
    for p in plan:
        raw=(SRC/p['name']).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==p['git_blob_sha1']
        inputs.append(SRC/p['name'])
    before={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    results=dict(directory=directory(), synthetic_codec=synthetic_codec(), teacher=teacher(),
                 original_input_sha256=before, new_biological_payload_bytes=0, new_biological_rows=0)
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    results['original_inputs_unchanged']=True
    (HERE/'CHECKS.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v for k,v in results.items() if k!='original_input_sha256'},indent=2))


if __name__=='__main__':
    main()

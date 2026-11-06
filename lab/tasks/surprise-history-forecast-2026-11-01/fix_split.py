"""Outcome-blind participant split, keeping the already viewed subject in development."""
import datetime, hashlib, json, pathlib, re, zipfile
p=pathlib.Path(__file__).resolve().parent
with zipfile.ZipFile(p/'behavior_zip.source') as z:
    rows=[]
    for x in z.infolist():
        if x.filename.endswith('.mat') and not x.filename.startswith('__MACOSX'):
            sid=str(int(re.search(r'_(\d+)\.mat$',x.filename).group(1)))
            rows.append(dict(id=sid,member=x.filename,size=x.file_size,compressed=x.compress_size))
assert len(rows)==39 and len({x['id'] for x in rows})==39
ranked=sorted((x for x in rows if x['id']!='342'),key=lambda x:hashlib.sha256(('surprise-history-20261101:'+x['id']).encode()).hexdigest())
dev={'342'}|{x['id'] for x in ranked[:19]}
for x in rows: x['split']='development' if x['id'] in dev else 'evaluation'
out=dict(fixed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),rule='Participant342 already viewed; 19 other development people by SHA256(surprise-history-20261101:ID), remaining19 evaluation. No participant performance used.',n_development=20,n_evaluation=19,participants=sorted(rows,key=lambda x:int(x['id'])),evaluation_exposure='Archive compressed bytes/hash and ZIP directory acquired, no evaluation member decompressed or values read; published group summaries exposed. Not an unacquired holdout.')
f=p/'SPLIT.json'
assert not f.exists()
f.write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))

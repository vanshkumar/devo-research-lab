import csv, datetime, json, pathlib, resource
p=pathlib.Path(__file__).resolve().parent
with (p/'source/Final_probes_20200816.csv').open(newline='',encoding='utf-8-sig') as f:
    r=csv.reader(f); rows=[]
    for i,row in enumerate(r):
        rows.append(row)
        if i==5:break
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,
     'note':'Schema and first five rows only; not the required original-observation calculation.',
     'process_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(p/'SCHEMA.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

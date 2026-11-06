import csv,json,sys,resource
from pathlib import Path
p=Path(__file__).resolve().parent/'sources'/sys.argv[1]
rows=list(csv.reader(p.open(encoding='utf-8-sig',newline='')))
print(json.dumps({'file':p.name,'data_rows_including_export_headers':len(rows)-1,
 'header':rows[0], 'first_two_rows':rows[1:3],
 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))

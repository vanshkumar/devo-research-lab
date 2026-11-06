"""Document which measurements are actually inside the pinned archive."""
import pathlib,json,zipfile,hashlib
import pandas as pd
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent
meta=json.loads((R/'sources/imprinting/zenodo10869154.json').read_text());checks={x['key']:x['checksum'] for x in meta['files']}
z=zipfile.ZipFile(R/'data/imprinting/Experiment1.zip');out=[]
for name in z.namelist():
 d=pd.read_excel(z.open(name));vals=sorted(float(v) for v in d.unfamiliar_object.unique() if v!='none')
 out.append(dict(member=name,rows=len(d),columns=d.columns.tolist(),unfamiliar_color_values=vals))
result=dict(metadata_exp1_checksum=checks['Experiment 1.zip'],metadata_exp2_checksum=checks['Experiment 2.zip'],checksums_identical=checks['Experiment 1.zip']==checks['Experiment 2.zip'],downloaded_md5=hashlib.md5((R/'data/imprinting/Experiment1.zip').read_bytes()).hexdigest(),actual_members=out,interpretation='Retrieved Exp1 archive contains Exp2 blue-green450–514 codes. Short red-yellow580–645 condition is not present in this pinned archive as retrieved, not claimed globally unavailable.')
assert result['checksums_identical'];assert all(max(m['unfamiliar_color_values'])<580 for m in out)
(H/'archive_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

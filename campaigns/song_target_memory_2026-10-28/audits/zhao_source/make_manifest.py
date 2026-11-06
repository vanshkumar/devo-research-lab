from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parents[2]/'inputs/zhao'
urls={
'pmc.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC7688245/',
'supplement_verified.pdf':'https://pmc.ncbi.nlm.nih.gov/articles/instance/7688245/bin/NIHMS1646797-supplement-Supp_Material_and_Figures.pdf',
'supplement_download_preparation.html':'https://pmc.ncbi.nlm.nih.gov/articles/instance/7688245/bin/NIHMS1646797-supplement-Supp_Material_and_Figures.pdf',
'manuscript_download_preparation.html':'https://pmc.ncbi.nlm.nih.gov/articles/PMC7688245/pdf/nihms-1646797.pdf',
'oa.xml':'https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC7688245',
'oa_current.xml':'https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC7688245',
'europepmc.xml':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7688245/fullTextXML',
'europepmc_supp_response.html':'https://europepmc.org/articles/PMC7688245/bin/NIHMS1646797-supplement-Supp_Material_and_Figures.pdf',
'europepmc_suppfiles_response.xml':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7688245/supplementaryFiles',
'publisher_supplement_blocked.html':'https://www.science.org/doi/suppl/10.1126/science.aaw4226/suppl_file/aaw4226_zhao_sm.pdf',
'figure3.jpg':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9c19/7688245/78a427713cd3/nihms-1646797-f0003.jpg',
'figure4.jpg':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9c19/7688245/78c3541e86bc/nihms-1646797-f0004.jpg',
'figure5.jpg':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9c19/7688245/caa0d5a100eb/nihms-1646797-f0005.jpg',
'figure6.jpg':'https://cdn.ncbi.nlm.nih.gov/pmc/blobs/9c19/7688245/7a148b372190/nihms-1646797-f0006.jpg'}
records=[]
for f in sorted(p.iterdir()):
 if f.name=='MANIFEST.json':continue
 b=f.read_bytes();r={'file':f.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'url':urls.get(f.name),'acquired_date':'2026-10-28'}
 if f.name=='supplement_verified.txt':r['derived_from']='supplement_verified.pdf; bundled pypdf text extraction'
 if 'preparation' in f.name or 'blocked' in f.name or 'response' in f.name or f.name in ['oa.xml','oa_current.xml','europepmc.xml']:r['usable_primary_source']=False
 else:r['usable_primary_source']=True
 records.append(r)
(p/'MANIFEST.json').write_text(json.dumps({'records':records,'retained_download_bytes_excluding_derived_text':sum(r['bytes'] for r in records if r.get('url')),'resource_limit':'Individual direct-download caps3–20MB; total actual retainedpublic responses~6.4MB. Browser normal supplement download1.6MB. Web search transfer overhead unknown, not asserted zero.','no_access_control_bypass':True},indent=2)+'\n')
print(p/'MANIFEST.json')

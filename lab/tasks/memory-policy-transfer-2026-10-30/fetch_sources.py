"""At most three specific code/primary-document requests, with byte accounting."""
import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
OUT = ROOT / 'sources/memory_policy_transfer_2026-10-30'
LEDGER = OUT / 'DOCUMENT_REQUESTS.json'
if LEDGER.exists():
    raise SystemExit('Refusing repeated document acquisition')
records = [{'number': 3, 'url': 'https://www.nature.com/articles/s41539-021-00105-8',
            'tool': 'web_run.open', 'status': 'failed_identity_redirect',
            'body_bytes': None, 'conservative_charge': 65536}]

def fetch(number, url, name, cap):
    item = {'number':number, 'url':url, 'cap':cap, 'body_bytes':0}
    records.append(item)
    LEDGER.write_text(json.dumps(records,indent=2)+'\n')
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=35) as response:
            item['status'] = response.status
            item['final_url'] = response.geturl()
            data = response.read(cap+1)
        item['body_bytes'] = len(data)
        if len(data) > cap:
            raise RuntimeError('Document cap exceeded')
        (OUT/name).write_bytes(data)
        item['sha256'] = hashlib.sha256(data).hexdigest()
        item['git_blob'] = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        return data
    except Exception as exc:
        item['error'] = str(exc)
        return None
    finally:
        LEDGER.write_text(json.dumps(records,indent=2)+'\n')

code = fetch(4, 'https://raw.githubusercontent.com/Human-Centric-Machine-Learning/spaced-selection/fb197043c287a3d4f76787a19c023b964e823c7d/notebooks/Plots.ipynb', 'Plots.ipynb', 500000)
if code:
    if records[-1]['git_blob'] != '4a578ef357d45908c8717204ef78ed212adff7db':
        raise RuntimeError('Notebook does not match pinned tree')
    notebook = json.loads(code)
    text = '\n\n'.join(''.join(c.get('source',[])) for c in notebook['cells'])
    (OUT/'NOTEBOOK_SOURCE.txt').write_text(text)
    # Notebook outputs are not rendered or used as observations.
metadata = fetch(5, 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI%3A10.1038%2Fs41539-021-00105-8&format=json', 'paper_metadata.json', 200000)
if metadata:
    result = json.loads(metadata).get('resultList',{}).get('result',[])
    pmc = next((r['pmcid'] for r in result if r.get('doi') == '10.1038/s41539-021-00105-8' and r.get('pmcid')), None)
    if pmc:
        paper = fetch(6, 'https://www.ebi.ac.uk/europepmc/webservices/rest/'+pmc+'/fullTextXML', 'paper.xml', 3000000)
        if paper:
            root = ET.fromstring(paper)
            sections = []
            for sec in root.findall('.//sec'):
                title = sec.findtext('title','')
                if sec.get('sec-type') == 'methods' or title.lower() in ('methods','data availability','code availability'):
                    sections.append('\n'.join(''.join(x.itertext()) for x in sec if x.tag != 'fig'))
            (OUT/'PAPER_METHODS.txt').write_text('\n\n'.join(sections))
print(json.dumps(records,indent=2))

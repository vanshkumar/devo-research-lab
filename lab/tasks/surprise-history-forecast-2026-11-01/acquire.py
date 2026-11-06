"""Bounded fixed public object acquisition for this assignment, no retries."""
import datetime, hashlib, json, pathlib, resource, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
URLS = {
    'task_generate': ('https://raw.githubusercontent.com/rasmusbruckner/AdaptiveLearning/a0b782e788f4bbf99d08a31b691556c475f7e041/Task/Functions/GenerateOutcomes.m', 20_000),
    'task_config': ('https://raw.githubusercontent.com/rasmusbruckner/AdaptiveLearning/a0b782e788f4bbf99d08a31b691556c475f7e041/Task/AdaptiveLearning.m', 50_000),
    'task_main': ('https://raw.githubusercontent.com/rasmusbruckner/AdaptiveLearning/a0b782e788f4bbf99d08a31b691556c475f7e041/Task/Functions/Main.m', 30_000),
    'task_odd': ('https://raw.githubusercontent.com/rasmusbruckner/AdaptiveLearning/a0b782e788f4bbf99d08a31b691556c475f7e041/Task/Functions/Oddball.m', 20_000),
    'task_export': ('https://raw.githubusercontent.com/rasmusbruckner/AdaptiveLearning/a0b782e788f4bbf99d08a31b691556c475f7e041/DataScripts/ExportData.m', 10_000),
    'task_tree': ('https://api.github.com/repos/rasmusbruckner/AdaptiveLearning/git/trees/a0b782e?recursive=1', 1_000_000),
    'source_license': ('https://raw.githubusercontent.com/learning-memory-and-decision-lab/NassarBrucknerFrank_eLife_2019/ed500ff28129c7d9a021fe167782bc07ebf7c23d/LICENSE', 50_000),
    'zenodo_meta': ('https://zenodo.org/api/records/5034463', 200_000),
    'behavior_zip': ('https://zenodo.org/api/records/5034463/files/cannonBehavData_forDryad.zip/content', 1_500_000),
    'behavior_public': ('https://datadryad.org/stash/downloads/file_stream/154749', 1_500_000),
    'behavior_api_failed': ('https://datadryad.org/api/v2/files/154749/download', 1_500_000),
    'dryad_files2': ('https://datadryad.org/api/v2/versions/43267/files?page=2', 100_000),
    'dryad_files3': ('https://datadryad.org/api/v2/versions/43267/files?page=3', 100_000),
    'dryad_files': ('https://datadryad.org/api/v2/versions/43267/files', 1_000_000),
    'dryad_encoded': ('https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.570pf8n', 1_000_000),
    'source_analysis': ('https://raw.githubusercontent.com/learning-memory-and-decision-lab/NassarBrucknerFrank_eLife_2019/ed500ff28129c7d9a021fe167782bc07ebf7c23d/nassarBrucknerFrank2019_analysis.m', 150_000),
    'source_model': ('https://raw.githubusercontent.com/learning-memory-and-decision-lab/NassarBrucknerFrank_eLife_2019/ed500ff28129c7d9a021fe167782bc07ebf7c23d/helperFunctions/getTrialVarsFromPEs_cannon.m', 20_000),
    'source_readme': ('https://raw.githubusercontent.com/learning-memory-and-decision-lab/NassarBrucknerFrank_eLife_2019/ed500ff28129c7d9a021fe167782bc07ebf7c23d/README.md', 10_000),
    'dryad_meta': ('https://datadryad.org/api/v2/datasets/doi:10.5061/dryad.570pf8n', 2_000_000),
    'code_tree': ('https://api.github.com/repos/learning-memory-and-decision-lab/NassarBrucknerFrank_eLife_2019/git/trees/master?recursive=1', 1_000_000),
    'article': ('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6716947/fullTextXML', 2_000_000),
}

def fetch(name, url, cap):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry = dict(name=name, url=url, cap=cap, started=started)
    payload = bytearray()
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'bounded-academic-reanalysis/1.0'})
        with urllib.request.urlopen(req, timeout=30) as res:
            entry.update(status=res.status, final_url=res.url, headers=dict(res.headers))
            while True:
                chunk = res.read(min(65536, cap + 1 - len(payload)))
                if not chunk:
                    break
                payload.extend(chunk)
                if len(payload) > cap:
                    raise RuntimeError('body cap exceeded')
        path = ROOT / (name + '.source')
        path.write_bytes(payload)
        entry.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), path=path.name)
    except Exception as exc:
        entry.update(error=repr(exc), bytes_received=len(payload))
    entry['rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    log = ROOT / 'ACQUISITIONS.json'
    existing = json.loads(log.read_text()) if log.exists() else []
    existing.append(entry)
    log.write_text(json.dumps(existing, indent=2))
    print(json.dumps({k:v for k,v in entry.items() if k != 'headers'}))

if __name__ == '__main__':
    for name in sys.argv[1:]:
        fetch(name, *URLS[name])

"""Save exact retrieved code and source pins; does not repeat measured analyses."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import resource

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'sources'
def response(name):
    value = json.loads((SRC / (name + '.json')).read_text())
    return value['value'] if value.get('status') == 'fulfilled' else value

sources = {
    'bci_git_source_0': 'README.md',
    'bci_git_source_1': 'run.m',
    'bci_s2_0': 'simulate/helper/extractSpikesToFactorsMapping.m',
    'bci_s2_1': 'behavior/computeControlPlaneActivity.m',
    'bci_s2_2': 'LICENSE',
    'bci_factor_directions': 'behavior/computeFactorPushingDirections.m',
    'bci_progress': 'behavior/computeProgressOfProjection.m',
    'bci_prelearning_source': 'simulate/helper/generatePreLearningActivity.m'
}
tree = json.loads(response('bci_github_tree')['structuredContent']['content'])
blobs = {row['path']: row for row in tree['tree'] if row['type'] == 'blob'}
pins = []
for saved, repo_path in sources.items():
    text = response(saved)['structuredContent']['content']
    encoded = text.encode('utf8')
    target = SRC / 'golub_code' / repo_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encoded)
    actual = hashlib.sha1(('blob %d\0' % len(encoded)).encode() + encoded).hexdigest()
    expected = blobs[repo_path]
    assert len(encoded) == expected['size'], repo_path
    assert actual == expected['sha'], repo_path
    pins.append({'path': str(target.relative_to(ROOT)), 'repo_path': repo_path,
                 'bytes': len(encoded), 'sha256': hashlib.sha256(encoded).hexdigest(),
                 'git_blob_sha1': actual, 'matches_remote_git_blob': True,
                 'url': 'https://raw.githubusercontent.com/mattgolub/bci_learning/3e6f00c959096189dd77df57ceb9eb540da83f76/' + repo_path})

acquire = json.loads((ROOT / 'ACQUIRE_EXAMPLE.json').read_text())
pins.append({'path': 'sources/exampleData.mat', 'bytes': acquire['file_bytes'],
             'sha256': acquire['sha256'], 'git_blob_sha1': acquire['git_blob_sha1'],
             'matches_remote_git_blob': acquire['git_blob_sha1'] == blobs['exampleData.mat']['sha'],
             'url': acquire['url'], 'verified_in': 'inspect_example.py'})
captures = []
for path in sorted(SRC.glob('*.json')):
    body = path.read_bytes()
    captures.append({'path': str(path.relative_to(ROOT)), 'bytes': len(body),
                     'sha256': hashlib.sha256(body).hexdigest()})

manifest = {
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'golub_repository': 'https://github.com/mattgolub/bci_learning',
    'commit': '3e6f00c959096189dd77df57ceb9eb540da83f76',
    'tree_from_commit': '09da19ee751cf96264eb4259a23d377e09cabf5f',
    'codepack_version': '1.1', 'pins': pins, 'captured_tool_responses': captures,
    'license': {
        'golub_repository': 'BSD-3-Clause; exact LICENSE saved and Git-blob verified. Example data is bundled in this repository; no separate data-specific license was found in the complete tree.',
        'golub_paper': 'Nature America rights/PMC academic research conditions; paper reports full data available on reasonable request. No outside contact authorized or attempted.',
        'athalye_dandi_000404': 'CC-BY-4.0, OpenAccess, 13 files, 2 subjects, approximately 1 GB per retrieved DANDI page. No NWB assets acquired.',
        'athalye_zenodo_8006653': '341.9 MB software ZIP listing only; no legible license value in retrieved page; no ZIP acquired.'
    },
    'primary_references': [
        {'family': 1, 'title': 'Learning by neural reassociation', 'doi': '10.1038/s41593-018-0095-3', 'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC5876156/'},
        {'family': 2, 'title': 'Invariant neural dynamics drive commands to control different movements', 'doi': '10.1016/j.cub.2023.06.027', 'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC10527529/', 'access_note': 'Indexed primary text retrieved in search; direct PMC open returned recaptcha. Do not treat that direct request as full-text acquisition.'},
        {'family': 2, 'title': 'Monkey 2D cursor BMI', 'doi': '10.48324/dandi.000404/0.230605.2024', 'url': 'https://dandiarchive.org/dandiset/000404/draft'}
    ],
    'source_gate': 'FAILED for intended initial-error-adjusted adaptation forecast; measured decoder reconstruction passed.',
    'local_finalizer_peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
}
(ROOT / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'exact_source_pins': len(pins), 'captured_responses': len(captures),
                  'source_capture_serialized_bytes': sum(row['bytes'] for row in captures),
                  'all_text_git_blobs_match': True, 'peak_rss_bytes': manifest['local_finalizer_peak_rss_bytes']}, indent=2))

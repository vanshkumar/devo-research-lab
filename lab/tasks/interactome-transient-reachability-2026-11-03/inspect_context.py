"""Bounded ordinary-source inspection, no observations or simulation."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'connectome-persistence-contrast-2026-11-03' / 'sources'
tree = json.loads((BASE / 'interactome-tree.json').read_text())
tree = json.loads(tree['value']['structuredContent']['content'])
print('SOURCE_TREE_SELECTED')
for item in tree['tree']:
    if item['path'].startswith(('static/', 'templates/')) and item['path'].endswith(('.js', '.html')):
        print(item['path'], item['sha'], item.get('size'))
print('PUBLISHED_REFERENCE')
for name in ['interactome-paper.json', 'interactome-results.json']:
    print(name)
    obj = json.loads((BASE / name).read_text())
    if 'value' in obj:
        obj = obj['value']
    for block in obj.get('content', []):
        if block.get('type') == 'text':
            for line in block['text'].splitlines():
                label = line.split(':', 1)[0]
                if label.startswith('L') and label[1:].isdigit() and (255 <= int(label[1:]) <= 274 or 348 <= int(label[1:]) <= 369):
                    print(line)

import json, pathlib
p=pathlib.Path(__file__).resolve().parent
print((p/'source_model.source').read_text())
t=json.loads((p/'task_tree.source').read_text())
print('TASK_TREE',t['sha'])
for x in t['tree']:
    print(x['path'],x.get('size',''),x['sha'])

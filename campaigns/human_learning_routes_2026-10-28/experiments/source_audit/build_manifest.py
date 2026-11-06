from pathlib import Path
import hashlib,json
B=Path(__file__).resolve().parent/'sources'
T='47ac8356432972c7e6e5a887f15a7dd2d6c686ad';A='1283c6ddd61fc17d9065a5b017d0e3cfd17535cb'
paths={'preprocess_fetch.py':('analysis','preprocessing/1_fetch_human_data.py'),'preprocess_process.py':('analysis','preprocessing/2_process_data.py'),'transform_data.py':('analysis','utils/transform_data.py'),'figure2.py':('analysis','src/figure2_psychometric_blocks_by_instruction.py'),'figure3.py':('analysis','src/figure3.py'),'figure4.py':('analysis','src/figure4.py'),'WIN_cursor_ibl_lastrun.py':('task','WIN_cursor_ibl_lastrun.py')}
for i in range(10):paths[f'pregen_sequence_{i}.xlsx']=('task',f'pregen_sequence_{i}.xlsx')
records=[]
for name,(kind,path) in paths.items():
 p=B/name
 if not p.exists():continue
 repo='cocosys-lab/human_IBL_cursor' if kind=='task' else 'cocosys-lab/2026-human-ibl-analyses';commit=T if kind=='task' else A
 tree=json.loads((B/f'{kind}_tree.json').read_text())['tree'];expected=next(x['sha'] for x in tree if x['path']==path)
 data=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 records.append(dict(file=name,url=f'https://raw.githubusercontent.com/{repo}/{commit}/{path}',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob_sha1=blob,expected_git_blob_sha1=expected,git_blob_verified=blob==expected))
 assert blob==expected,(name,blob,expected)
for name,url in [('builder_commit_history.json','https://api.github.com/repos/cocosys-lab/human_IBL_cursor/commits?path=WIN_cursor_ibl.psyexp&per_page=100'),('hoxha_api.json','https://api.biorxiv.org/details/biorxiv/10.64898/2026.10.01.755923'),('december2024_commit.json','https://api.github.com/repos/cocosys-lab/human_IBL_cursor/commits/681e1f39e916b2e3922fdd7779b6936eba0f8101')]:
 p=B/name;data=p.read_bytes();records.append(dict(file=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(B/'manifest.json').write_text(json.dumps(records,indent=2))
print('Saved',len(records),'source records;',sum(r.get('git_blob_verified',False) for r in records),'pinned blob matches')

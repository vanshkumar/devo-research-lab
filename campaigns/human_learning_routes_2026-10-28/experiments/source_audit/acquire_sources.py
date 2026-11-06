from pathlib import Path
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parent/'sources'
MAN=[]
repos=[('task','cocosys-lab/human_IBL_cursor','47ac8356432972c7e6e5a887f15a7dd2d6c686ad',['README.md','WIN_cursor_ibl_lastrun.py','WIN_cursor_ibl_legacy.psyexp']+[f'pregen_sequence_{i}.xlsx' for i in range(10)]),('analysis','cocosys-lab/2026-human-ibl-analyses','1283c6ddd61fc17d9065a5b017d0e3cfd17535cb',['README.md','preprocessing/1_fetch_human_data.py','preprocessing/2_process_data.py','src/figure2_psychometric_blocks_by_instruction.py','src/figure4.py','utils/transform_data.py'])]
for label,repo,commit,files in repos:
 for f in files:
  out=ROOT/label/f;out.parent.mkdir(parents=True,exist_ok=True)
  url=f'https://raw.githubusercontent.com/{repo}/{commit}/{f}'
  p=subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','60',url,'-o',str(out)],capture_output=True,text=True)
  if p.returncode:print(p.stderr);continue
  data=out.read_bytes();MAN.append(dict(file=str(out.relative_to(ROOT)),url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(ROOT/'manifest.json').write_text(json.dumps(MAN,indent=2))
print('Acquired',len(MAN),'source files')

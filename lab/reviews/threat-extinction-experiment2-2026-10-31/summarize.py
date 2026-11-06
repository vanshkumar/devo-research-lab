"""Read saved independent outputs; verify pins and emit compact closeout evidence."""
import datetime as dt
import hashlib
import json
import pathlib
import resource
import io
import zipfile

HERE=pathlib.Path(__file__).resolve().parent
AUTHOR=HERE.parents[1]/'tasks/threat-extinction-experiment2-2026-10-31'
readbytes=0
def read(path):
    global readbytes
    b=path.read_bytes()
    readbytes+=len(b)
    return b
def load(name):
    return json.loads(read(HERE/name))
def pins(path,root):
    f=json.loads(read(path))
    result={n:hashlib.sha256(read(root/n)).hexdigest()==h for n,h in f['pins'].items()}
    assert all(result.values())
    return result

own=pins(HERE/'CONTRARY_FREEZE.json',HERE)
author_main=pins(AUTHOR/'FREEZE.json',AUTHOR)
author_contrary=pins(AUTHOR/'CONTRARY_FREEZE.json',AUTHOR)
first=load('FIRST_CALCULATION.json')
main=load('RECONSTRUCTION.json')
controls=load('CONTROL_RECONSTRUCTION.json')
new=load('CONTRARY.json')
syntax=load('SOURCE_SYNTAX.json')
archive=zipfile.ZipFile(io.BytesIO(read(AUTHOR/'sources/experiment2.zip')))
readme_name=next(n for n in archive.namelist() if n.endswith('/READ ME.txt'))
readme=archive.read(readme_name)
readbytes+=len(readme)
(HERE/'SOURCE_README.txt').write_bytes(readme)
out={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'independent_freeze_pins':own,
     'author_main_pins':author_main,'author_contrary_pins':author_contrary,
     'independent_control_reconstruction':{'replicates':controls['checked_replicates'],
        'maximum_scalar_difference':controls['maximum_scalar_difference']},'channels':{},
     'exact_source_syntax_matches':{},'source_readme':{'member':readme_name,
        'sha256':hashlib.sha256(readme).hexdigest(),'text':readme.decode('utf8','replace')}}
for name,text in syntax.items():
    lines=text.splitlines()
    if name.endswith('syntax_SCR.sps'):
        out['exact_source_syntax_matches'][name]=[line for i,line in enumerate(lines) if
            ('*Rescale' in line or 'COMPUTE CSplus1_6=' in line or 'Lowest thru' in line or
             'GLM SQRT_CSplus1_6' in line or 'COMPUTE SCR_max=' in line)]
    else:
        out['exact_source_syntax_matches'][name]=[line for line in lines if 'GLM Ext_CSplus1_1' in line]
for channel,details in new['channels'].items():
    cells={}
    for condition,cell in details['cells'].items():
        assert len(cell['records'])==100
        assert cell['full_rule_count']==sum(r['passes_full_rule'] for r in cell['records'])
        cellkey=['generator','full_rule_count','wilson95','exact_source_design_oracles',
                 'mean_oracle_best_common_separation_mse','mean_conditional_noise_mse',
                 'mean_ideal_expected_fractional_gain']
        cells[condition]={k:cell[k] for k in cellkey}
    out['channels'][channel]={'cells':cells,'paired_known_effect_detection':details['paired_known_effect_detection']}
    for a in ['development','actual_evaluation_prefix_design']:
        original=cells['source_k_alpha1']['exact_source_design_oracles'][a]
        zero=cells['k0_alpha1']['exact_source_design_oracles'][a]
        out['channels'][channel][a+'_separation_ratio_k0_to_source']=zero['best_common_separation_mse']/original['best_common_separation_mse']
# Member names and the source's own README remain visible without opening
# workbook, questionnaire or any other source payload.
out['source_archive_members']=main['source']['archive']
out['resources']={'saved_source_artifact_hash_bytes_read':readbytes,
                  'conservative_stage_charge_bytes':5000000,
                  'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'public_operations':0,'ingress_bytes':0,'jobs_after_command':0}
(HERE/'CONTRARY_SUMMARY.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps(out,indent=2,allow_nan=False))

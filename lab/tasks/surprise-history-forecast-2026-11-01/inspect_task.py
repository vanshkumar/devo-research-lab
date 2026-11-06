import pathlib,re
p=pathlib.Path(__file__).resolve().parent
for name in ['task_generate','task_config','task_main','task_odd','task_export']:
    lines=(p/(name+'.source')).read_text(encoding='latin-1').splitlines()
    print('\nFILE',name)
    indexes=set()
    for i,line in enumerate(lines):
        if re.search(r'hazard|vola|oddballProb|timestamp|sigma|drift|pred\(|pred=|outcome\(|outcome=|DataCP|DataOdd|counter|cBal|conc|rand',line,re.I):
            indexes.update(range(max(0,i-1),min(len(lines),i+3)))
    for i in sorted(indexes):print(i+1,lines[i])

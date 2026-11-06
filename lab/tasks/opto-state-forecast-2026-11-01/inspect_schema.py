import pathlib, zipfile, re, html, resource, json
P=pathlib.Path(__file__).resolve().parent
z=zipfile.ZipFile(P/'code_v1.1.zip')
out=[]
for n in z.namelist():
    if not n.endswith(('.py','.txt','.md')) or '/build/' in n: continue
    b=z.read(n)
    if len(b)>500000: continue
    s=b.decode(errors='replace')
    if any(x in s for x in ['stim_volume_i','gcamp.txt','exported_data','stim_indices']):
        lines=s.splitlines()
        for i,line in enumerate(lines):
            if any(x in line for x in ['stim_volume_i','gcamp.txt','exported_data','stim_indices']):
                out.append(n+':'+str(i+1)+'\n'+'\n'.join(lines[max(0,i-3):i+5]))
(P/'SCHEMA_CODE.txt').write_text('\n\n'.join(out))
print('\n\n'.join(out)[:24000])
paper=(P/'paper.html').read_text()
paper=re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '',paper,flags=re.S)
text=html.unescape(re.sub('<[^>]*>',' ',paper))
text=re.sub(r'\s+',' ',text)
(P/'paper_text.txt').write_text(text)
print('\nPRIMARY METHODS EXCERPT LOCATIONS:')
for term in ['500 ms','500-ms','0.5 s','retinal','artifact','artefact','different animals','per animal','Data availability','license','neurons were stimulated','immobiliz','pre-stimulation']:
    hits=list(re.finditer(re.escape(term),text,re.I))
    print(term,len(hits))
    for m in hits[:3]: print(text[max(0,m.start()-250):m.end()+450])
print('gcamp_first_line', (P/'0_gcamp.txt').open().readline()[:500])
print('RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

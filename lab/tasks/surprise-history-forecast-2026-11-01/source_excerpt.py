import pathlib, re, xml.etree.ElementTree as E
import sys
p=pathlib.Path(__file__).resolve().parent
lines=(p/'source_analysis.source').read_text().splitlines()
for i,line in enumerate(lines):
    if len(sys.argv)>1 and re.search(r'ROI_data|save\(|load\(|behavData|subID',line) or len(sys.argv)==1 and 230 <= i < 335:
        print(i+1,line)
a=E.parse(p/'article.source')
for s in a.findall('.//sec'):
    title=s.find('title')
    if title is not None:
        name=''.join(title.itertext())
        if len(sys.argv)==1 and any(k in name.lower() for k in ['experimental','procedure','cannon','task procedure']):
            print(name, ''.join(s.itertext())[:15000])

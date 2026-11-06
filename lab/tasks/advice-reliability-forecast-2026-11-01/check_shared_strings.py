import pathlib,zipfile,xml.etree.ElementTree as E,json
r=pathlib.Path(__file__).resolve().parent
with zipfile.ZipFile(r/'dataset_exp1.xlsx') as z:
 n={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 s=[''.join(t.text or '' for t in x.findall('.//m:t',n)) for x in E.fromstring(z.read('xl/sharedStrings.xml'))]
print(json.dumps(dict(enumerate(s)),indent=2))
(r/'SHARED_STRINGS.json').write_text(json.dumps(dict(enumerate(s)),indent=2))

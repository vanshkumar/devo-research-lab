import zipfile, pathlib, xml.etree.ElementTree as ET, json, hashlib, resource
root=pathlib.Path(__file__).resolve().parent
p=root/'dataset_exp1.xlsx'
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(p) as z:
    layout={'members':[{'path':i.filename,'compressed':i.compress_size,'decoded':i.file_size} for i in z.infolist()]}
    assert sum(i.file_size for i in z.infolist())<100_000_000
    layout['workbook_xml']=z.read('xl/workbook.xml').decode()
    layout['relationships_xml']=z.read('xl/_rels/workbook.xml.rels').decode()
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        ss=z.read('xl/sharedStrings.xml')
        strings=[''.join(t.text or '' for t in x.findall('.//m:t',ns)) for x in ET.fromstring(ss)]
        layout['shared_strings_bytes']=len(ss)
        layout['shared_strings_count']=len(strings)
    first=[]
    with z.open('xl/worksheets/sheet1.xml') as f:
        for _,e in ET.iterparse(f,events=('end',)):
            if e.tag.endswith('}row'):
                row={}
                for c in e.findall('m:c',ns):
                    v=c.find('m:v',ns)
                    value=None if v is None else v.text
                    if c.attrib.get('t')=='s' and value is not None: value=strings[int(value)]
                    if c.attrib.get('t')=='inlineStr': value=''.join(t.text or '' for t in c.findall('.//m:t',ns))
                    row[c.attrib['r']]=value
                first.append(row)
                if len(first)==3: break
    layout['first_three_sheet1_rows']=first
layout['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(root/'XLSX_LAYOUT.json').write_text(json.dumps(layout,indent=2))
print(json.dumps(layout,indent=2))

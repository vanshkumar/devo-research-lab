"""Read-only original OOXML source audit. No macro/pickle/workbook code execution."""
import datetime, hashlib, json, pathlib, posixpath, resource, zipfile, xml.etree.ElementTree as E
p=pathlib.Path(__file__).resolve().parent
f=p/'source/Supplementary Data 1.xlsx'
raw=f.read_bytes();assert hashlib.sha256(raw).hexdigest()=='2f8142a717bb1199e3a43563d57ef0c016c7a72084b2e2b91ed7be66194ef557'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
with zipfile.ZipFile(f) as z:
    book=E.fromstring(z.read('xl/workbook.xml'))
    rels={x.attrib['Id']:x.attrib['Target'] for x in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    shared=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        shared=[''.join(n.itertext()) for n in E.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
    sheets=[]
    for s in book.findall('m:sheets/m:sheet',NS):
        target=rels[s.attrib[R]]
        target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        xml=z.read(target)
        root=E.fromstring(xml); rows=[]
        for row in root.findall('m:sheetData/m:row',NS):
            cells={}
            for c in row.findall('m:c',NS):
                t=c.attrib.get('t');v=c.find('m:v',NS);formula=c.find('m:f',NS)
                val=None if v is None else v.text
                if t=='s':val=shared[int(val)]
                elif t=='inlineStr':val=''.join(c.find('m:is',NS).itertext())
                cells[c.attrib['r']]={'value':val,'type':t,'formula':None if formula is None else formula.text}
            rows.append({'source_row':row.attrib['r'],'cells':cells})
        sheets.append({'name':s.attrib['name'],'target':target,'xml_bytes':len(xml),
                       'dimension':root.find('m:dimension',NS).attrib if root.find('m:dimension',NS) is not None else None,
                       'rows':rows})
out={'calculated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'sha256':hashlib.sha256(raw).hexdigest(),'file_bytes':len(raw),'sheets':sheets,
     'shared_strings_count':len(shared),'all_cell_types_preserved':True,
     'note':'Original source values, error/blank/string/numeric/formula cache types preserved. No formula recalculation or workbook modification.',
     'exposure':'All worksheets/shared strings/cell tokens decoded. All values are consumed source context, not a pristine holdout.',
     'process_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(p/'SOCIAL_TABLE_TYPED.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'at':out['calculated_at_utc'],'file_bytes':len(raw),'sheets':[
 {'name':s['name'],'dimension':s['dimension'],'n_rows':len(s['rows']),
  'headers':s['rows'][0],'first_two_rows':s['rows'][1:3]} for s in sheets],
 'peak_rss':out['process_peak_rss_bytes_macos']},indent=2))

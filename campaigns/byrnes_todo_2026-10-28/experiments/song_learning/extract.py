"""Read-only XLSX extraction using only XML/ZIP stdlib; never rewrites inputs."""
import zipfile,xml.etree.ElementTree as E,json,pathlib,posixpath
H=pathlib.Path(__file__).resolve().parent;C=H.parents[1];D=C/'data/song_learning';N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def extract(path):
 with zipfile.ZipFile(path) as z:
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   rt=E.fromstring(z.read('xl/sharedStrings.xml'))
   strings=[''.join(q.itertext()) for q in rt.findall('s:si',N)]
  rel=E.fromstring(z.read('xl/_rels/workbook.xml.rels'));rels={q.attrib['Id']:q.attrib['Target'] for q in rel}
  book=E.fromstring(z.read('xl/workbook.xml'));out={}
  for sh in book.findall('s:sheets/s:sheet',N):
   target=rels[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']];target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
   rt=E.fromstring(z.read(target));rows=[]
   for row in rt.findall('s:sheetData/s:row',N):
    cells={}
    for c in row.findall('s:c',N):
     v=c.find('s:v',N);val=v.text if v is not None else None
     if c.attrib.get('t')=='s' and val is not None:val=strings[int(val)]
     elif c.attrib.get('t')=='inlineStr':val=''.join(c.find('s:is',N).itertext())
     elif val is not None:
      try:val=float(val)
      except ValueError:pass
     if val is not None:cells[c.attrib['r']]=val
    if cells:rows.append(cells)
   out[sh.attrib['name']]=rows
  return out
if __name__=='__main__':
 for p in D.glob('*.xlsx'):
  data=extract(p);(D/(p.stem+'_extracted.json')).write_text(json.dumps(data,indent=2)+'\n')
  print(p.name,[(k,len(v),max(len(x) for x in v)) for k,v in data.items()])
  for k,v in data.items():print(k,'FIRST_ROWS',v[:6])

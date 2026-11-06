import json, resource, xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent
d=json.loads((root/'openneuro-tree.json').read_text())
tree=d['tree']
summary={'sha':d['sha'],'truncated':d.get('truncated'), 'entries':len(tree),
 'files':sum(x['type']=='blob' for x in tree),
 'non_imaging_entries':[x for x in tree if x['type']=='blob' and not x['path'].endswith('.nii.gz')],
 'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(root/'TREE_CHECK.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
if (root/'openneuro-s3.xml').exists():
    xml=ET.fromstring((root/'openneuro-s3.xml').read_bytes())
    ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    objects=[{'key':node.find('s:Key',ns).text,'size':int(node.find('s:Size',ns).text)} for node in xml.findall('s:Contents',ns)]
    report={'is_truncated':xml.find('s:IsTruncated',ns).text,
     'objects':len(objects),'non_imaging':[x for x in objects if not x['key'].endswith('.nii.gz')],
     'listed_bytes':sum(x['size'] for x in objects),
     'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (root/'S3_CHECK.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
for filename in ['openneuro-tree-1.0.0.json','revaluation2017-tree.json']:
    source=json.loads((root/filename).read_text())
    entries=source['tree']
    report={'source':filename, 'sha':source['sha'], 'truncated':source.get('truncated'),
      'entries':len(entries),'files':sum(x['type']=='blob' for x in entries),
      'non_imaging_entries':[x for x in entries if x['type']=='blob' and not x['path'].endswith('.nii.gz')],
      'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (root/(filename+'.check.json')).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

import json
from pathlib import Path
R=Path(__file__).resolve().parent
j=json.loads((R/'cited_primary_crossref.json').read_bytes())['message']
print('TITLE',j.get('title'));print('ABSTRACT',j.get('abstract'));print('LINKS',j.get('link'));print('RESOURCE',j.get('resource'));print('LICENSE',j.get('license'))
for x in j.get('reference',[]):
    if any(w in str(x).lower() for w in ['routing','context','gale','switch','reinforcement','modality','olsen']):print('RELEVANT CITATION',x)
print('ALLREFERENCE_TITLES',[x.get('article-title') for x in j.get('reference',[]) if x.get('article-title')])

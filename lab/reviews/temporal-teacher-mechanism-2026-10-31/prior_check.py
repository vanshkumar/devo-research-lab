"""Inspect the cached primary article; no network or figure retrieval."""
import review_core as r
from html.parser import HTMLParser
import re,hashlib,json
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.hidden=max(0,self.hidden-1)
    def handle_data(self,value):
        if not self.hidden:self.parts.append(value)
p=r.ROOT/'sources/sensory_evaluator_feasibility_2026-10-28/primary.html'
b=r.read(p);parser=Text();parser.feed(b.decode());text=re.sub(r'\s+',' ',' '.join(parser.parts))
words=['HVC','temporal','actor','reinforcement','population']
locations={}
for term in words:
    hits=[m.start() for m in re.finditer(re.escape(term),text,re.I)]
    # Short internal inspection excerpts; no figures are rendered or newly acquired.
    locations[term]=[text[max(0,i-160):i+550] for i in hits[:3]]
r.dump('PRIOR_CHECK.json',{'source':str(p.relative_to(r.ROOT)),'sha256':hashlib.sha256(b).hexdigest(),
       'canonical_url':'https://elifesciences.org/reviewed-preprints/111771',
       'cached_primary_text_inspection':locations,'new_primary_requests':0,
       'interpretation_limit':'Selective source-scope inspection, not exhaustive priority proof; no novel theorem/model-class claim.'})
print(json.dumps(locations,indent=2))

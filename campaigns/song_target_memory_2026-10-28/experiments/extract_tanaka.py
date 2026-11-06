"""Offline text extraction from the pinned public PMC HTML; no external dependency."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json

class Text(HTMLParser):
    def __init__(self):
        super().__init__();self.out=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style']:self.skip+=1
        if tag in ['p','h1','h2','h3','h4','li','div','section']:self.out.append('\n')
    def handle_endtag(self,tag):
        if tag in ['script','style']:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.out.append(data)

if __name__=='__main__':
    p=Path(__file__).resolve().parents[1]/'inputs'/'tanaka'
    b=(p/'pmc.html').read_bytes()
    m=json.loads((p/'manifest.json').read_text())
    assert hashlib.sha256(b).hexdigest()==m['sha256']
    s=Text();s.feed(b.decode())
    text=''.join(s.out)
    # Keep raw inputs immutable. The saved reference extraction must agree.
    assert text==(p/'article.txt').read_text()
    print('Verified source checksum and deterministic text extraction:',len(b),'bytes')

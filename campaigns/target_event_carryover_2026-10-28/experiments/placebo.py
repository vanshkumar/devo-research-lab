"""Fixed pre-index endpoint placebo; derived by linearity from identical level/change designs."""
from analysis import *

def main(part):
 level=json.loads((ROOT/'outputs'/f'{part}_Hand_raw_level_all.json').read_text());change=json.loads((ROOT/'outputs'/f'{part}_Hand_raw_change_all.json').read_text());out={};summaries=[]
 for f in FILES:
  fits=[]
  for a,b in zip(level[f]['lags'],change[f]['lags']):
   scores=np.array(a['contrast']['scores'])-np.array(b['contrast']['scores'])
   fits.append({'contrast':{'estimate':a['contrast']['estimate']-b['contrast']['estimate'],'scores':scores}})
  ss=curve_summary(fits);summaries.append(ss);out[f]=ss
 out['pooled']=pooled_summary(summaries);out['interpretation']='Association of index target event with pretreatment five-endpoint mean after the same assigned-input adjustment; diagnostic, not a treatment effect.'
 (ROOT/'outputs'/f'{part}_preindex_placebo.json').write_text(json.dumps(out,indent=2)+'\n');print(part,out['pooled'])
if __name__=='__main__':
 import sys
 main(sys.argv[1] if len(sys.argv)>1 else 'validation')

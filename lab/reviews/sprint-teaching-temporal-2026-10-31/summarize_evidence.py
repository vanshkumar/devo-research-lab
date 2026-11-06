"""Summarize actual independent computations and cached publication scope."""
import os,sys
sys.dont_write_bytecode=True
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='2'
from collections import defaultdict
from html.parser import HTMLParser
import hashlib,json,re
import numpy as np
from audit_common import HERE,SOURCE,read,j,save

class Paragraphs(HTMLParser):
    def __init__(self):super().__init__();self.depth=0;self.buf=[];self.paragraphs=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('p','h1','h2','h3'):
            if self.depth==0:self.buf=[]
            self.depth+=1
    def handle_data(self,data):
        if self.depth:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag in ('p','h1','h2','h3') and self.depth:
            self.depth-=1
            if not self.depth:
                text=re.sub(r'\s+',' ',''.join(self.buf)).strip()
                if text:self.paragraphs.append(text)

def main():
    d=j(HERE/'DYNAMICS_RESULTS.json');summaries=[]
    for p in d['plants']:
        warm=p['candidate_conditioned_5_cycle_contrary_test'];order={r['policy']:r for r in warm if r['kind']=='order'}
        duration={round(r['stretch'],8):r for r in warm if r['kind']=='duration'}
        pair=next(r for r in p['fresh_order_pairs'] if r['variant']=='no_clock_forward')
        row={'plant':p['plant'],'fresh_no_clock_wrong_minus_target_Hz':pair['bestwrong_minus_target_Hz'],
             'continuous_cycle5_order_wrong_minus_target_Hz':order['bestwrong']['cycle_means_Hz'][-1]-order['target']['cycle_means_Hz'][-1],
             'continuous_cycle4_order_wrong_minus_target_Hz':order['bestwrong']['cycle_means_Hz'][-2]-order['target']['cycle_means_Hz'][-2],
             'continuous_order_score_cycle4_to5_max_change_Hz':max(abs(r['cycle_means_Hz'][-1]-r['cycle_means_Hz'][-2]) for r in order.values()),
             'continuous_cycle5_duration07_minus1_Hz':duration[.7]['cycle_means_Hz'][-1]-duration[1.]['cycle_means_Hz'][-1],
             'continuous_duration_score_cycle4_to5_max_change_Hz':max(abs(r['cycle_means_Hz'][-1]-r['cycle_means_Hz'][-2]) for r in duration.values()),
             'duration':[],'reverse_tutor_positive':p['102_positive_reverse_preference']}
        for name in ('no_clock_forward','tonic_forward','onset_reset'):
            rows=[r for r in p['duration_common_tail'] if r['variant']==name]
            target=min(rows,key=lambda r:abs(r['stretch']-1.));other=[r for r in rows if abs(r['stretch']-.8)>1e-12 and abs(r['stretch']-1.)>1e-12]
            final=other[0] if other else target
            row['duration'].append({'variant':name,'final_stretch':final['stretch'],
                 'final_minus_target_1300_Hz':final['prefix_1300_Hz']-target['prefix_1300_Hz'],
                 'final_minus_target_2000_Hz':final['mean_2000_Hz']-target['mean_2000_Hz'],
                 'exposure_normalized_final_minus_target_Hz':final['quiet_subtracted_excess_per_active_ms_Hz']-target['quiet_subtracted_excess_per_active_ms_Hz'],
                 'final_minus_target_gold_MSE':final['independent_waveform_MSE']-target['independent_waveform_MSE'],
                 'target_active_ms':target['active_ms'],'final_active_ms':final['active_ms'],
                 'target_input_energy':target['input_energy'],'final_input_energy':final['input_energy']})
        summaries.append(row)
    save('ADVERSARIAL_SUMMARY.json',{'plants':summaries,'all_dynamic_checks_passed':d['all_passed'],'dynamic_check_count':len(d['checks']),
         'independent_integrations':d['independent_integrations'],'max_source_trace_error':max(c.get('detail',{}).get('source_trace_error',0) for c in d['checks'])})
    raw=read(SOURCE/'primary.html','cached_primary_publication')
    parser=Paragraphs();parser.feed(raw.decode('utf-8','replace'))
    patterns=('temporal','irregular','reinforcement','motor learning','premotor','duration','reward landscape','timing')
    selected=[]
    for i,text in enumerate(parser.paragraphs):
        if any(pattern in text.lower() for pattern in patterns):selected.append({'paragraph_index':i,'text':text})
    save('PUBLICATION_SCOPE_EVIDENCE.json',{'source_url':'https://elifesciences.org/reviewed-preprints/111771',
         'cached_primary_sha256':hashlib.sha256(raw).hexdigest(),'matches_saved_primary_pin':hashlib.sha256(raw).hexdigest()=='222eefc904fe92a4a05b6312986a29e41c265cf47637ac52027e797bb1ddfc63',
         'matching_paragraphs':selected,'read_scope':'Cached publication only; no new biological dataset, network or new priority search.'})
    print(json.dumps({'adversarial_results':summaries,'max_source_trace_error':max(c.get('detail',{}).get('source_trace_error',0) for c in d['checks']),
         'publication_scope_paragraphs':selected[:16]}))

if __name__=='__main__':main()

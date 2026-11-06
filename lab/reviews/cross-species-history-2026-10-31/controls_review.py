"""Assess saved controls only: no fit batch, generator or optimizer rerun."""
import json,resource,datetime
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent;AUTHOR=HERE.parents[1]/'tasks'/HERE.name

def main():
    paths=[AUTHOR/'corrected/CONTROLS.json',AUTHOR/'corrected/CONTROL_FITS.json',AUTHOR/'corrected/CONTROL_RUN.json']
    scores,fits,run=[json.loads(p.read_text()) for p in paths]
    assert len(fits)==540
    keys=Counter((r['tag'],r['augmented'],r['fold'],r['model']) for r in fits)
    assert len(keys)==540 and set(keys.values())=={1}
    assert set(r['model'] for r in fits)=={'B','H','T'}
    records=[]
    for family in ('null','shared','different'):
        for baseline in ('B','S'):
            for species in ('human','mouse'):
                for comparison in ('H-minus-B','T-minus-H','T-minus-B'):
                    selected=sorted([r for r in scores if r['family']==family and r['baseline']==baseline and r['species']==species and r['scope']=='support' and r['comparison']==comparison],key=lambda r:r['seed'])
                    assert [r['seed'] for r in selected]==list(range(6))
                    values=[r['gain_nat'] for r in selected]
                    records.append(dict(family=family,baseline=baseline,species=species,comparison=comparison,gains_by_seed=values,mean_gain=sum(values)/6,min_gain=min(values),max_gain=max(values),seeds_point_gain_at_least_005=sum(v>=.005 for v in values),seeds_point_gain_negative=sum(v<0 for v in values),intervals_saved=any(r['interval95']!=[None,None] for r in selected),practical_joint_rule_certified=False))
    paired=[]
    for family in ('null','shared','different'):
        for baseline in ('B','S'):
            for comp in ('H-minus-B','T-minus-H','T-minus-B'):
                hh=next(r for r in records if r['family']==family and r['baseline']==baseline and r['species']=='human' and r['comparison']==comp)
                mm=next(r for r in records if r['family']==family and r['baseline']==baseline and r['species']=='mouse' and r['comparison']==comp)
                paired.append(dict(family=family,baseline=baseline,comparison=comp,seeds_both_species_point_gain_at_least_005=sum(h>=.005 and m>=.005 for h,m in zip(hh['gains_by_seed'],mm['gains_by_seed'])),seeds_both_species_positive=sum(h>0 and m>0 for h,m in zip(hh['gains_by_seed'],mm['gains_by_seed']))))
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),saved_datasets=18,saved_fits=len(fits),saved_score_records=len(scores),coefficient_lengths=sorted(set(len(r['coefficients']) for r in fits)),all_stored_success=all(r['success'] for r in fits),stored_gradient_max=max(r['gradient_max'] for r in fits),fit_tag_counts=dict(Counter(r['tag'] for r in fits)),records=records,paired_point_checks=paired,author_control_peak_rss_bytes=run['rss_bytes'],author_cap_breach_preserved=run['rss_bytes']>1000000000,limitations=['Saved control score records contain aggregate fixed-fit means, no intervals. Their meaningful_positive=False is automatic when intervals are disabled, not a tested failure/success decision.', 'Controls fit only B/H/T, so the human_fixed/mouse_fixed transfer pipeline is not directly calibrated.', 'Six seeds per family do not certify biological coverage or power. No boundary calibration exists.', 'The full-design generating baseline coefficients, generated outcomes, row probabilities and per-unit control losses are not saved; this review checks record consistency and score magnitudes, not independent control outcome/score reconstruction.', 'Histories and response/omission masks are fixed from consumed actual choices; generated responses do not update future predictors. These are conditional synthetic-design checks, not autonomous generated learning.'],resource=dict(read_file_bytes=sum(p.stat().st_size for p in paths),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    (HERE/'CONTROL_ASSESSMENT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('saved_datasets','saved_fits','saved_score_records','all_stored_success','stored_gradient_max','paired_point_checks','resource')},indent=2))
    print(json.dumps([r for r in records if (r['family']=='shared' and r['comparison']=='H-minus-B') or (r['family']=='different' and r['comparison']=='T-minus-H') or (r['family']=='null' and r['comparison']=='H-minus-B')],indent=2))

if __name__=='__main__':main()

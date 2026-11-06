"""Reproduce the executed original-condition source challenge from cached vectors."""
from independent import HERE, Accounting, save


def main():
    meter=Accounting('final consequential original-source falsification')
    data=meter.json(HERE/'SOURCE_FAMILY_PREAUTHOR.json')
    out=[]
    for cutoff in [200,1000]:
        for metric in ['A','D']:
            rows=[r for r in data['highlights'] if r['kind']=='source' and r['reference']=='recent_selected'
                  and r['cutoff']==cutoff and r['metric']==metric]
            worst=max(rows,key=lambda r:r['joint_upper']);i=worst['index'];se=data['bands']['se'][i]
            out.append(dict(label=worst,se=se,benefit_margin_headroom=worst['margin']-worst['point'],
                            point_plus_1SE=worst['point']+se,point_plus_1_96SE=worst['point']+1.96*se,
                            note='Descriptive studentizer comparison, not a replacement inferential family or repaired gate'))
    peak=max([r for r in data['source_points'] if r['cutoff']==1000 and r['reference']=='original'],
             key=lambda r:r['relative_score_gain'])
    paired=next(r for r in data['source_points'] if r['draw']==peak['draw'] and r['cutoff']==1000
                and r['reference']=='recent_selected')
    save('SOURCE_FALSIFICATION.json',dict(original_condition_examples=out,
        largest_retained_original_late_GRU_point_gain=peak,same_draw_strong_recent_reference=paired,
        interpretation='Source-only limitations and stronger ordinary explanation; no post-hoc subgroup/model choice or pointwise decision substitution.'))
    save('SOURCE_FALSIFICATION_RESOURCES.json',meter.receipt())


if __name__=='__main__': main()

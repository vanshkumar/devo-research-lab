"""Record falsified hypotheses separately from successful numerical checks."""
import json
from audit_common import HERE,PILOT,j,save

def main():
    summary=j(HERE/'ADVERSARIAL_SUMMARY.json');actor=j(HERE/'FINAL_SCIENTIFIC_SUMMARY.json');hypotheses=[];arithmetic=[]
    for p,a in zip(summary['plants'],actor['normalized_actor_control']):
        plant=p['plant']
        hypotheses.append({'plant':plant,'hypothesis':'quiet_reset_is_sufficient_explanation_of_wrong_order_preference',
            'prediction_if_true':'wrong-minus-target score becomes nonnegative under candidate-conditioned repeated cycling',
            'observed_gap_Hz':p['continuous_cycle5_order_wrong_minus_target_Hz'],
            'supported':p['continuous_cycle5_order_wrong_minus_target_Hz']>=0,
            'readout_mean_cycle4_to5_change_Hz':p['continuous_order_score_cycle4_to5_max_change_Hz']})
        hypotheses.append({'plant':plant,'hypothesis':'silence_subtracted_active_exposure_score_is_duration_faithful',
            'prediction_if_true':'unit-duration target is not dominated by the score-selected wrong duration',
            'chosen_duration':a['normalized_final_duration'],'chosen_minus_target_Hz':a['normalized_chosen_minus_target_Hz'],
            'supported':not a['wrong_selected_point_has_lower_score_than_target'],
            'full25query_actor_completed':True})
        f=j(PILOT/('outputs/teaching_followup_%03d.json'%plant))
        for row in f['preferences']:
            costs=row['costs'];chosen=min(range(len(costs)),key=costs.__getitem__);rank=1+sum(c<costs[row['desired_order']] for c in costs)
            arithmetic.append({'plant':plant,'variant':row['variant'],'content':row['content'],
                'preferred_order':chosen,'desired_rank':rank,'passed':chosen==row['preferred_order'] and rank==row['desired_rank']})
        if plant==102:
            r=p['reverse_tutor_positive'];values={(v['net'],v['order']):v['score_Hz'] for v in r}
            hypotheses.append({'plant':102,'hypothesis':'all_order_information_is_absent_after_zero_HVC_tutoring',
                'prediction_if_true':'tutor reversal does not reverse the forward-versus-reverse pair preference',
                'forward_critic_reverse_minus_forward_Hz':values['forward',2]-values['forward',0],
                'reverse_critic_reverse_minus_forward_Hz':values['reverse_tutored',2]-values['reverse_tutored',0],
                'supported':not(values['forward',2]>values['forward',0] and values['reverse_tutored',2]<values['reverse_tutored',0])})
    save('SCIENTIFIC_CHECKS.json',{'hypotheses':hypotheses,'note':'False supported values preserve failed scientific explanations; numerical replay success does not make these hypotheses true.',
        'additional6policy_arithmetic_checks':arithmetic,'all_arithmetic_passed':all(c['passed'] for c in arithmetic)})
    print(json.dumps({'failed_scientific_hypotheses':sum(not h['supported'] for h in hypotheses),'scientific_hypotheses_tested':len(hypotheses),
       'additional_arithmetic_checks':len(arithmetic),'all_arithmetic_passed':all(c['passed'] for c in arithmetic)}))

if __name__=='__main__':main()

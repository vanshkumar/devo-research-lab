from pathlib import Path
import os,json
os.environ.setdefault('MPLCONFIGDIR','/tmp/target_event_matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];D=R/'outputs/recovery'
s=json.loads((D/'summary.json').read_text());o=json.loads((D/'oracle.json').read_text());sc=s['scenarios']
lines=['# Recovery and discrimination results','',
'2026-10-28. Final inference uses Welch–Satterthwaite degrees of freedom across the two independent sets, each with ten person clusters. All 3,900 simulations used **reserved input sequences only**. No empirical reserved or external outcome was accessed. Prior fixed-df results are preserved in `outputs/recovery_df18/`; estimates and standard errors are unchanged by the interval amendment.','',
'## Result','',
'The robust primary observable estimator has approximately calibrated intervals in the tested challenges but insufficient sensitivity to a 0.2° mean modulation. At actual-schedule physical effects of approximately −0.2° and +0.2°, zero was excluded in 17.7% and 11.0% of simulations, respectively. No simulation in any scenario produced an interval wholly inside ±0.2°. A null empirical result from this estimator therefore cannot support the prespecified equivalence claim.','',
'This is an estimator/design tradeoff under the tested noise regime, **not a universal information limit**. An oracle using the correct generative mean and Gaussian noise law discriminates the same ±0.2° physical alternatives from fixed retention with >99.99% accuracy. Even after removing flexible current-cell learning, current-cell endpoint and block-drift directions, oracle accuracy remains >99.99% for the negative and >99.98% for the positive case. The lead therefore pursued a separately labeled low-dimensional efficiency repair.','',
'By contrast, a fixed-retention model with state-dependent perceived-error correction produces exactly the same endpoints as retention modulation. Its oracle accuracy is 50%. This is an algebraic mechanistic ambiguity, distinct from the weak primary estimator. An unrestricted dynamic expression state supplies a second exact equivalence.','',
'## Simulation controls','',
'- 300 replicates per scenario; 20 people, actual reserved schedules, source-file/SN keys preserved.','- Endpoint noise SD 3° before the five-prior-reach mean is subtracted; development differenced residual SD ranged 2.79–3.09°. This is a conservative calibration, not a fitted full noise model.','- Independent motor and observation AR(1) components (variance shares .35/.65; correlations .70/.25), slow sinusoidal/linear drift, fast-state process noise SD .08°, lognormal gain variation with log SD .20 and noise variation with log SD .15.','- Fixed, independent 3% outcome omissions with seed194192; scheduled updates and original time gaps remain. This is conditional-on-mask recovery, not an outcome-dependent missingness analysis.','- Exact frozen-estimator scalar/cluster-score operators are verified against direct five-lag fitting; largest numerical discrepancy is '+f"{s['operator_verification']['max_error']:.2g}"+'°.','- Physical truth is computed from explicit preceding-clamp/index-event counterfactuals and actual intervening transitions. Sixty full-chronology checks match the analytic formula within 2.78e−16°. Noiseless projection is separately evaluated with process, observation and drift noise removed.','',
'## Numeric results','',
'All angles are degrees. Coverage is for the physical scalar; rejection is two-sided exclusion of zero. Percentages have binomial uncertainty recorded in `summary.json`. The correctly specified linear controls are event-level regression controls, not physical reaching models.','',
'| Scenario | Physical truth | Mean estimate | Noiseless projection | Mean SE | Coverage | Reject zero |','|---|---:|---:|---:|---:|---:|---:|']
for name,v in sc.items():
 lines.append(f"| {name} | {v['mean_physical_truth']:+.3f} | {v['mean_estimate']:+.3f} | {v['mean_noiseless_projection']:+.3f} | {v['mean_se']:.3f} | {v['coverage_physical']['rate']:.1%} | {v['reject_zero']['rate']:.1%} |")
lines += ['',
'The four fixed-storage/direct-expression nulls have false-positive rates of 3.0–6.7%, with their 95% binomial intervals containing 5%. Physical-scalar coverage across all challenges is 93.3–97.0%, so the tested coverage discrepancies are modest at 300 replicates. Neither coverage nor low false positives supplies sensitivity: correctly specified ±0.2° regression controls also detect only 12.7–17.3%.','',
'## Isolated impulse versus actual schedule','',
'With the original generator, isolated ±0.2° effects become actual-schedule means −0.158° and +0.257° because subsequent events further attenuate or amplify the previous input. The estimator also differs from the physical effect: negative-case noiseless projection is −0.192°. This distinction is retained rather than calling the estimator output its own truth.','',
'The additional `actual_margin` cases fix the scientific margin at ±0.2°. Fast gain was set to .90° (slow gain .20°) to permit a −0.2° actual-schedule effect without a sign-reversing transition; the isolated input effect was solved before simulation. The negative and positive isolated reference values are '+f"{sc['actual_margin_negative']['isolated_reference_effect']:+.6f}° and {sc['actual_margin_positive']['isolated_reference_effect']:+.6f}°"+'. Participant gain variation then produces small replicate variation about the prescribed population/reference effect. These additional cases supplement the original scenarios; they do not overwrite them or change the practical threshold.','',
'## Oracle and strongest alternative','',
'Known Gaussian noise uses the same 3° endpoint SD and the two AR components; process noise is set to zero for the oracle, and drift is known absent. Available main-trial endpoints retain their original time gaps. The conditional means and participant parameters are known. Thus oracle results are optimistic information checks for stipulated model pairs, not power estimates for human data or a validation of those models.','',
'| Pair | Oracle accuracy | After nuisance projection |','|---|---:|---:|']
for name,v in o['scenarios'].items():lines.append(f"| {name} | {v['oracle_accuracy']:.8f} | {v['nuisance_projected_accuracy']:.8f} |")
lines += ['',
'The nuisance projection spans free cell-specific gains at two fixed timescales, direct current-cell endpoint effects, and participant/block intercepts and linear drift. It does not make unknown time constants, non-Gaussian noise or readout mechanism known. The exact perceived-error equivalence survives all such projections because its mean difference is zero.','',
'## Reproduction','',
'```sh',
'.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/check_generators.py',
'.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/physical_truth_check.py',
'.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/recovery.py --reps 300',
'.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/oracle.py',
'.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/write_report.py',
'```','',
'Final scenario arrays, summary JSON/CSV and oracle calculations are in `outputs/recovery/`; logs are in `logs/recovery.log` and `logs/recovery_oracle.log`. Analysis source hash and development calibration-source hash are included in `summary.json`. The 3,900-replicate run took '+f"{s['seconds']:.1f}"+' seconds in the existing workspace environment.']
(R/'audits/recovery_design/RECOVERY_REPORT.md').write_text('\n'.join(lines)+'\n')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
ax=axes[0,0]
for name,color in [('actual_margin_negative','#3366aa'),('actual_margin_positive','#b64545')]:
 rows=json.loads((D/(name+'.json')).read_text());est=[x['estimate'] for x in rows]
 ax.hist(est,bins=np.linspace(-1,1,30),density=True,alpha=.42,color=color,label=f"True {np.mean([x['truth'] for x in rows]):+.2f}°")
 ax.axvline(np.mean([x['truth'] for x in rows]),color=color,linestyle='--')
ax.axvline(0,color='black',linewidth=.8);ax.set(xlabel='Estimated mean modulation (°)',ylabel='Density',title='A  Robust estimates at the ±0.2° margin');ax.legend(frameon=False)
ax=axes[0,1]
for name,color,label in [('retention_positive','#b64545','Persistent'),('expression_next_positive','#339966','Next reach only'),('rebound_positive','#9966aa','Rebound')]:
 v=sc[name];ax.plot(range(1,6),v['physical_curve'],color=color,linestyle='--',marker='o',label=label+' truth')
 ax.plot(range(1,6),v['mean_curve'],color=color,alpha=.8)
ax.axhline(0,color='black',linewidth=.8);ax.set(xlabel='Reach after index event',ylabel='Signed modulation (°)',title='B  Matched immediate, different later effects');ax.legend(frameon=False,fontsize=8);ax.text(.03,.03,'Solid: mean estimate; dashed: physical truth',transform=ax.transAxes,fontsize=8)
ax=axes[1,0]
names=['two_timescale_null','gain_only_null','online_null','expression_current_positive']
labels=['Two timescales','Current gain','Online correction','Current expression']
rates=np.array([sc[k]['reject_zero']['rate'] for k in names]);ci=np.array([sc[k]['reject_zero']['binomial95'] for k in names])
ax.errorbar(rates*100,np.arange(4),xerr=np.stack([rates-ci[:,0],ci[:,1]-rates])*100,fmt='o',color='#334455',capsize=3)
ax.axvline(5,color='black',linestyle='--',linewidth=.8);ax.set_yticks(range(4),labels);ax.set(xlabel='False positives (%)',title='C  Null calibration, 300 replicates each',xlim=(0,13));ax.invert_yaxis()
ax=axes[1,1]
x=np.arange(2);r=np.array([sc['actual_margin_negative']['correct_sign_detection']['rate'],sc['actual_margin_positive']['correct_sign_detection']['rate']]);oracle=np.array([o['scenarios']['fixed_vs_actual_minus02']['oracle_accuracy'],o['scenarios']['fixed_vs_actual_plus02']['oracle_accuracy']])
ax.bar(x-.17,r*100,width=.32,color='#557799',label='Robust scalar detection');ax.bar(x+.17,oracle*100,width=.32,color='#aaaaaa',label='Known-model classification')
ax.set_xticks(x,['−0.2°','+0.2°']);ax.set(ylabel='Probability (%)',title='D  Estimator sensitivity vs model information',ylim=(0,110));ax.legend(frameon=False,fontsize=8)
fig.savefig(D/'recovery_summary.png',dpi=170);fig.savefig(D/'recovery_summary.pdf');plt.close(fig)
print('Wrote recovery report and figure')

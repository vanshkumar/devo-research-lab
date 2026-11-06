"""Preselected unused Fig2 source robustness; read-only ZIP-member verification."""
import pathlib,json,csv,xml.etree.ElementTree as E,zlib,hashlib,statistics,math
import numpy as np
from scipy import stats
H=pathlib.Path(__file__).resolve().parent;C=H.parents[1];D=C/'data/song_learning/fig2_members';N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def sheet(name):
 mp=json.loads((D/'sheet_map.json').read_text());di=json.loads((D/'zip_directory.json').read_text());p=D/mp[name].replace('/','__');b=p.read_bytes();e=di[mp[name]];assert len(b)==e['uncompressed'] and zlib.crc32(b)&0xffffffff==e['crc'];rt=E.fromstring(b);return np.array([[float(c.find('s:v',N).text) for c in row.findall('s:c',N)] for row in rt.findall('s:sheetData/s:row',N)])

def save(name,rows):
 with (H/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

if __name__=='__main__':
 close=sheet('g.Closer_vals').ravel();far=sheet('g.Farther_vals').ravel();dec=sheet('f.deciles');assert len(close)==len(far)==25 and dec.shape==(24000,10)
 diff=close-far;loo=(diff.sum()-diff)/24
 # Panel f spans -1 to1sec with24000 displayed samples; supplied g is the definitive200-300ms scalar target.
 # Compare both conventional endpoint grids and report the interpolation ambiguity, rather than claiming raw timestamps.
 windows={}
 for convention,t in [('half_open',np.arange(24000)/12000-1),('inclusive',np.linspace(-1,1,24000))]:
  d=dec[(t>=.2)&(t<.3)].mean(0);windows[convention]=d
 highmean=float(close.mean());lowmean=float(far.mean());a=windows['half_open'];b=windows['inclusive'];endpoint_match=max(abs(a[0]-highmean),abs(a[-1]-lowmean))
 # Post-inspection consistency check: endpoints numerically match g; this does not establish independent quality ordering.
 assert endpoint_match<.002,('Source panel aggregation not reconciled',endpoint_match)
 # The worksheet has no decile labels. Preserve source A..J ordering, do not choose orientation from dopamine.
 slope=float(stats.spearmanr(np.arange(10),a).statistic)
 save('followup_paired_quality.csv',[dict(syllable_row=i+1,closer_dff_percent=float(x),farther_dff_percent=float(y),difference_percentage_points=float(x-y),independent_bird_id='not supplied') for i,(x,y) in enumerate(zip(close,far))])
 save('followup_decile_profile.csv',[dict(source_column=i+1,mean_200_300_halfopen=float(x),mean_200_300_inclusive=float(y)) for i,(x,y) in enumerate(zip(a,b))])
 # Independent scalar math check and known-answer covariance, without fitted simulation routines.
 sd=statistics.mean([float(x-y) for x,y in zip(close,far)]);assert abs(sd-float(diff.mean()))<1e-14
 analytical={'gaussian_covariance':'Cov(epsilon, -||mu+epsilon-theta||^2)=2*sigma^2*(theta-mu)', 'derivation':'Expand squared norm; centered Gaussian cubic moments vanish and E[epsilon_i*epsilon_j]=sigma^2 delta_ij. This covariance exists even when the song-update equation contains only the latent target, without dopamine.', 'known_single_feature_case':{'sigma':.25,'theta_minus_mu':.4,'exact_covariance':2*.25**2*.4}}
 result=dict(n_syllables=25,closer_mean=float(close.mean()),farther_mean=float(far.mean()),paired_difference_mean=float(diff.mean()),paired_difference_median=float(np.median(diff)),paired_difference_range=[float(diff.min()),float(diff.max())],positive_differences=int((diff>0).sum()),leave_one_syllable_difference_range=[float(loo.min()),float(loo.max())],reference_paired_t_statistic=float(stats.ttest_rel(close,far).statistic),reference_paired_t_pvalue=float(stats.ttest_rel(close,far).pvalue),warning_reference_test='reproduces source syllable-level calculation; syllables within six birds are not25 independent animals. Do not use as fresh bird-level inference.',bird_grouping_sign_constraint='All25 paired differences are positive, so every nonempty group mean remains positive under any grouping into birds; this does not supply missing bird-level variances or prove a population effect.',decile_response=dict(half_open=a.tolist(),inclusive=b.tolist(),max_time_grid_difference=float(np.max(abs(a-b))),endpoint_aggregate_match_error=endpoint_match,spearman_in_source_column_order=slope,strictly_decreasing_in_source_column_order=bool((np.diff(a)<0).all()),quality_direction='not independently labeled in worksheet; first/last columns numerically reconcile with closer/farther g as a post-inspection consistency check',time_axis='display-grid convention based on stated -1..+1sec plotting span, not raw acquisition timestamps; g scalar panel is definitive'),analytical_constraint=analytical,claims=['Definitive g pairs support the relative-quality contrast. The unlabeled decile columns are strictly ordered in source order; direction relative to quality is not independently established by worksheet labels.','These data do not manipulate tutor identity or identify how a tutor template is acquired.','Other causal studies establish pathway roles; this descriptive source-data audit does not overturn them.'])
 (H/'followup_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

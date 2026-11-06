"""Frozen cross-experiment clock calibration, no juvenile fitting."""
import json,pathlib,math
p=pathlib.Path(__file__).resolve().parent
slope=.0283;sem=.0022;n=10
# Source Long & Fee2008 motif-duration stretch. Values are positive per degree cooling.
# Student-t(9) 97.5th percentile pinned only for an approximate mean-slope interval.
t=2.2621571628540993
low=slope-t*sem;high=slope+t*sem
out={'date':'2026-10-28','source_url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC2723166/','source_location':'Dynamics in HVC, Figure1e/f; publisher proof PDF1-2 independently agrees','n_birds':n,'duration_fraction_per_C_cooling':slope,'sem':sem,'observed_bird_slope_range':[.0189,.0397],'linear_calibration_validity_C':[0,6.5],'mean_slope_approx_95_CI':[low,high],'formula':'duration_ratio_if_shared_clock = 1 / (1 + slope * cooling_C)','assumptions':['Adult output duration gain is inverse of the same neural speed used for juvenile encoding.','Cooling spread, brain state, age, and measurement metric do not change gain.','No compensation or other plasticity changes extent between encoding and readout.'],'not_evidence':'These predicted values are not juvenile observations; adult SEM does not capture cross-age mapping uncertainty.','predictions':[]}
for temperature in [0,1,2,3,4,5,6,6.5]:
 out['predictions'].append({'cooling_C':temperature,'predicted_pupil_tutor_duration_ratio':1/(1+slope*temperature),'ratio_from_mean_slope_CI':[1/(1+high*temperature),1/(1+low*temperature)],'ratio_from_observed_bird_slope_range':[1/(1+.0397*temperature),1/(1+.0189*temperature)],'external_time_template_ratio':1.0})
(p/'cooling_calibration.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

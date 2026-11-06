"""Investment checks; stdlib only, no author code or original empirical rows."""
import hashlib
import json
import math
from pathlib import Path
import platform
import resource
import statistics as st
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SRC = ROOT / 'lab/tasks/acquisition-reactive-sequence-2026-11-04'
started = time.time()
cpu_started = time.process_time()
inputs = []


def read_json(name):
    path = SRC / name
    data = path.read_bytes()
    inputs.append({'path': str(path.relative_to(ROOT)), 'bytes': len(data),
                   'sha256': hashlib.sha256(data).hexdigest()})
    return json.loads(data)


cal = read_json('CALIBRATION.json')
track = read_json('TRACK_CALIBRATION.json')
manifest = read_json('SOURCE_MANIFEST.json')
sites = dict(zip(manifest['subjects'], manifest['labs']))
assert len(sites) == len(manifest['subjects']) == 64
animals = sorted(track['score'])
assert set(animals) == set(cal['per_animal']) == set(sites)
diff = {a: track['score'][a]['log_loss'] - cal['per_animal'][a]['existing']['log_loss'] for a in animals}
assert all(track['score'][a]['n'] == cal['per_animal'][a]['existing']['n'] for a in animals)
by_site = {}
for site in sorted(set(sites.values())):
    aa = [a for a in animals if sites[a] == site]
    tt = st.mean(track['score'][a]['log_loss'] for a in aa)
    rr = st.mean(cal['per_animal'][a]['existing']['log_loss'] for a in aa)
    assert abs(tt - track['site_loss'][site]) < 1e-12
    assert abs(rr - cal['summary']['existing']['site_loss'][site]) < 1e-12
    by_site[site] = {'n': len(aa), 'tracker': tt, 'GRU': rr, 'difference': tt-rr}


def interval(values, critical):
    mean = st.mean(values)
    sd = st.stdev(values)
    se = sd/math.sqrt(len(values))
    return {'n': len(values), 'mean': mean, 'sd': sd, 'se': se,
            'descriptive_t95': [mean-critical*se, mean+critical*se]}


site_values = [s['difference'] for s in by_site.values()]
animal_summary = interval(list(diff.values()), 1.998340542520741)
site_summary = interval(site_values, 2.306004135204166)
new_sites = ['hoferlab', 'wittenlab']
old_sites = [s for s in by_site if s not in new_sites]
precision = {}
z = st.NormalDist().inv_cdf(.975)+st.NormalDist().inv_cdf(.9)
for margin in [.01, .005]:
    precision[str(margin)] = {
        'margin_nats': margin,
        'normal_sites_for_80pct_CI_inside_symmetric_margin_at_zero':
            math.ceil((z*site_summary['sd']/margin)**2),
        'normal_independent_animals_analogue':
            math.ceil((z*animal_summary['sd']/margin)**2)}

# Enumerated adaptive teacher reference. The next input discloses Y1.
p = .7
joint = {(y1,y1,y2): (p if y1 else 1-p)*((.2+.6*y1) if y2 else (.8-.6*y1))
         for y1 in [0,1] for y2 in [0,1]}
assert abs(sum(joint.values())-1) < 1e-14
given_x2_one = {str((y1,x2,y2)): mass/p for (y1,x2,y2),mass in joint.items() if x2 == 1}
replayed = {(y1,1,y2): (p if y1 else 1-p)*(.8 if y2 else .2)
            for y1 in [0,1] for y2 in [0,1]}
assert abs(sum(replayed.values())-1) < 1e-14
teacher = {
    'joint': {str(k): v for k,v in joint.items()},
    'conditional_given_X2_one': given_x2_one,
    'do_replay_X2_one': {str(k): v for k,v in replayed.items()},
    'actual_P_Y1_one_given_X2_one': 1.,
    'replay_P_Y1_one_given_fixed_X2_one': p,
    'replay_probability_incompatible_with_actual_teacher':
        sum(v for (y1,x2,y2),v in replayed.items() if x2 != y1),
    'likelihood_ratio_joint_path_111_p07_vs_p04': (.7*.8)/(.4*.8),
    'likelihood_ratio_actual_conditional_path_given_X2_one': 1.,
    'interpretation': 'A common known adaptive teacher cancels from causal sequential likelihood ratios, not from the normalization conditioning on a full realized future schedule.'}

# Exact expectation checks of a score tracker and a reward-dependent update.
score_errors = []
reward_errors = []
second_moments = []
for p in [.01,.1,.25,.5,.7,.9,.99]:
    for correct in [0,1]:
        for x in [-1.,.5,1.]:
            eta,a,b = .12, .8, .4
            score_mean = sum((p if y else 1-p)*eta*(y-p)*x for y in [0,1])
            reward_mean = sum((p if y else 1-p)*eta*(a+b*int(y==correct))*(y-p)*x for y in [0,1])
            reward_exact = eta*b*p*(1-p)*(2*correct-1)*x
            second = sum((p if y else 1-p)*(eta*(y-p)*x)**2 for y in [0,1])
            score_errors.append(abs(score_mean))
            reward_errors.append(abs(reward_mean-reward_exact))
            second_moments.append(second)
assert max(score_errors) < 1e-15
assert max(reward_errors) < 1e-15

result = {
    'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
    'status': 'executed developmental investment checks only',
    'sign': 'positive tracker-minus-GRU loss favors GRU',
    'observations': sum(track['score'][a]['n'] for a in animals),
    'animal': animal_summary,
    'equal_site': site_summary,
    'sites': by_site,
    'unseen_training_sites_equal_site_mean': st.mean(by_site[s]['difference'] for s in new_sites),
    'overlapping_training_sites_equal_site_mean': st.mean(by_site[s]['difference'] for s in old_sites),
    'animals_favoring_GRU': sum(d>0 for d in diff.values()),
    'sites_favoring_GRU': sum(d>0 for d in site_values),
    'precision_planning_sensitivity': precision,
    'teacher_reference': teacher,
    'score_update_reference': {'max_score_mean_error': max(score_errors),
                               'max_reward_mean_error': max(reward_errors),
                               'score_update_second_moment_range': [min(second_moments),max(second_moments)],
                               'checked_cases': len(score_errors)},
    'limitations': [
        'Old conditional scores have different training rosters and asymmetric site exposure.',
        'Nine selected sites are not a random sample of arbitrary new labs; intervals are descriptive.',
        'Future-horizon precision can differ; normal site-count extrapolation is not a main power guarantee.',
        'Source-fit and shared-training uncertainty are not represented by these intervals.',
        'Toy references establish probability distinctions, not biological teacher or learning-rule correctness.'],
    'resources': {'inputs': inputs, 'explicit_file_read_bytes': sum(v['bytes'] for v in inputs),
                  'cpu_seconds': time.process_time()-cpu_started,
                  'wall_seconds': time.time()-started,
                  'peak_rss_reported_native': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'peak_rss_units': 'bytes' if platform.system()=='Darwin' else 'kilobytes',
                  'physical_io_and_runtime_import_reads': 'unknown',
                  'network_ingress': 0,
                  'original_row_reads': 0}
}
(OUT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['teacher_reference','sites']},indent=2))

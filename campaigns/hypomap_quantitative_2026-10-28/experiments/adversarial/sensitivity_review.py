"""Independent analytic injection check and transparent technical-output audit.

Uses independently extracted counts. Does not import technical model functions.
Poisson injection probabilities are calculated exactly, not simulated.
"""
from collections import defaultdict
from pathlib import Path
import csv, hashlib, json, math
import numpy as np
from scipy.stats import poisson

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TECH = ROOT / 'outputs/technical'


def read(path):
    with path.open() as f: return list(csv.DictReader(f))


def dump_csv(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def tail_poisson_binomial(probs, at_least):
    pmf = [1.]
    for p in probs:
        following = [0.] * (len(pmf)+1)
        for k, v in enumerate(pmf):
            following[k] += (1-p)*v
            following[k+1] += p*v
        pmf = following
    return sum(pmf[at_least:])


def main():
    cells = read(HERE/'independent_candidate_counts.csv')
    donors = defaultdict(list)
    for c in cells:
        for key in ['minor', 'major', 'T', 'OXT', 'AVP']: c[key] = int(c[key])
        donors[c['donor_id']].append(c)
    exact = []
    for donor, group in donors.items():
        for ratio in [.1, .25, .5]:
            for baseline in ['zero_minor', 'observed_minor']:
                p = []
                for c in group:
                    M = c['major']; m = c['minor'] if baseline == 'observed_minor' else 0
                    # Fixed major M; added Poisson count can become the new major.
                    # Both genes >=10 and min/max>=.1 iff M>=10 and 10<=minor<=10*M,
                    # with the additional lower bound ceil(M/10).
                    low, high = max(10, (M+9)//10)-m, 10*M-m
                    probability = 0 if M < 10 else float(poisson.sf(low-1, ratio*M)-poisson.sf(high, ratio*M))
                    p.append(max(0., min(1., probability)))
                need = max(10, math.ceil(.2*len(group)))
                # In the observed-baseline scenario, non-injected cells retain
                # their already-observed threshold status as well.
                baseline_hits = [int(c['minor'] >= 10 and 10*c['minor'] >= c['major']) if baseline == 'observed_minor' else 0 for c in group]
                latent_probs = [.2*prob + .8*hit for prob, hit in zip(p, baseline_hits)]
                exact.append(dict(donor=donor, Dataset=group[0]['Dataset'], n=len(group),
                    injected_ratio=ratio, baseline=baseline, expected_recovery=sum(p)/len(p),
                    expected_positive_at_20pct_latent=sum(latent_probs),
                    nomination_count_required=need,
                    probability_count_criterion_if_20pct_latent=tail_poisson_binomial(latent_probs, need)))
    dump_csv(HERE/'analytic_injection_recovery.csv', exact)

    # Compare each technical direct-injection Monte Carlo mean with its exact
    # observed-count conditional expectation, using the recorded denominator.
    simulations = read(TECH/'direct_injection_recovery.csv')
    grouped = defaultdict(list)
    sizes = defaultdict(set)
    for row in simulations:
        key = (row['donor'], float(row['injected_ratio']))
        grouped[key].append(float(row['fraction']))
        sizes[key].add(int(row['n']))
    mc = []
    for (donor, ratio), fractions in grouped.items():
        ex = next(r for r in exact if r['donor']==donor and r['injected_ratio']==ratio and r['baseline']=='observed_minor')
        assert len(sizes[(donor, ratio)]) == 1
        kept = next(iter(sizes[(donor, ratio)]))
        assert kept in [len(donors[donor]), sum(c['major'] > 0 for c in donors[donor])]
        expected = ex['expected_recovery']*len(donors[donor])/kept
        se = float(np.std(fractions, ddof=1)/math.sqrt(len(fractions)))
        mc.append(dict(donor=donor, ratio=ratio, replications=len(fractions), exact_expected=expected,
            mc_mean=float(np.mean(fractions)), mc_se=se,
            standardized_difference=(float(np.mean(fractions))-expected)/se if se else None))
    dump_csv(HERE/'direct_injection_mc_audit.csv', mc)

    scores = read(TECH/'model_heldout_scores.csv')
    score_groups = defaultdict(list)
    for row in scores: score_groups[(row['pool'], row['conditioning'])].append(row)
    heldout = []
    for (pool, condition), rows in score_groups.items():
        heldout.append(dict(pool=pool, conditioning=condition, n_donors=len(rows),
            total_delta=sum(float(r['delta_logscore']) for r in rows),
            delta_excluding_znZv1=sum(float(r['delta_logscore']) for r in rows if r['donor']!='znZv1'),
            convergence_failures=sum(r['trace_success']!='True' or r['mixed_success']!='True' for r in rows)))
    cellscores = read(TECH/'model_per_cell_scores.csv')
    contributions = defaultdict(lambda: dict(n=0, delta=0.))
    for row in cellscores:
        if row['conditioning']!='minor_given_major_truncated': continue
        label = 'primary' if row['primary']=='True' else ('minor_lt10' if float(row['minor'])<10 else 'other_nonprimary')
        key = (row['pool'], row['donor'], label)
        contributions[key]['n'] += 1
        contributions[key]['delta'] += float(row['delta_logscore'])
    dump_csv(HERE/'model_gain_categories.csv', [dict(pool=k[0], donor=k[1], category=k[2], **v) for k,v in contributions.items()])
    sim_scores = read(TECH/'model_simulation_scores.csv')
    byrep = defaultdict(float)
    successes = defaultdict(lambda: [0,0])
    for row in sim_scores:
        byrep[(row['scenario'],int(row['replicate']))] += float(row['delta_logscore'])
        successes[row['scenario']][0] += row['trace_success']=='True' and row['mixed_success']=='True'
        successes[row['scenario']][1] += 1
    scenarios = defaultdict(list)
    for (name, rep), value in byrep.items(): scenarios[name].append(value)
    sim_summary = {s: dict(replicates=len(v), positive_delta_replicates=sum(x>0 for x in v),
        min_delta=min(v), median_delta=float(np.median(v)), max_delta=max(v),
        successful_folds=successes[s][0], total_folds=successes[s][1],
        injected_shapes=sorted({float(r['injected_shape']) for r in sim_scores if r['scenario']==s})) for s,v in scenarios.items()}
    moderate_byrep = defaultdict(float)
    for row in read(TECH/'model_moderate_noise_diagnostics.csv'):
        moderate_byrep[(row['scenario'], row['replicate'])] += float(row['delta_logscore'])
    moderate = {}
    for name in sorted({key[0] for key in moderate_byrep}):
        v = [value for (scenario, rep), value in moderate_byrep.items() if scenario == name]
        moderate[name] = dict(replicates=len(v), positive_delta_replicates=sum(x>0 for x in v), median_delta=float(np.median(v)))
    params = read(TECH/'model_parameters.csv')
    result = dict(analytic_recovery=exact, monte_carlo_check=mc, heldout_summary=heldout,
        simulation_summary=sim_summary, moderate_noise_diagnostics=moderate,
        parameter_checks=dict(any_nonconverged=any(r['success']!='True' for r in params),
            mixed_weight_range=[min(float(r['mixed_weight']) for r in params if r['model']=='mixed'),max(float(r['mixed_weight']) for r in params if r['model']=='mixed')],
            mixed_beta_range=[min(float(r['beta_mixed']) for r in params if r['model']=='mixed'),max(float(r['beta_mixed']) for r in params if r['model']=='mixed')]),
        input_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [HERE/'independent_candidate_counts.csv', HERE/'sensitivity_review.py', ROOT/'experiments/technical/run.py', ROOT/'experiments/technical/extra_controls.py', ROOT/'experiments/technical/IMPLEMENTATION.md', ROOT/'experiments/technical/TECHNICAL.md'] + sorted(TECH.glob('*.csv'))},
        limitations='Analytic injection is conditional on measured major counts and a Poisson observation model; neither a calibrated biological effect nor power for latent transcription. 20% latent scenario is illustrative, not an inferential bound.')
    (HERE/'technical_audit_result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(heldout=heldout, simulation=sim_summary, max_mc_standardized_difference=max(abs(r['standardized_difference']) for r in mc if r['standardized_difference'] is not None)), indent=2))


if __name__ == '__main__': main()

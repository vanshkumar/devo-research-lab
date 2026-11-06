"""Exact equal-label-cost contribution screen; Python standard library only."""
from datetime import datetime, timezone
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, permutations
import json
from pathlib import Path
import resource
import sys
import time


def main():
    started = time.perf_counter()
    n = 5
    incumbent = 0
    # Utilities are integer ranks until final division by n-1.
    worlds = tuple(permutations(range(n)))
    pairs = tuple(combinations(range(n), 2))
    all_worlds = (1 << len(worlds)) - 1
    masks = tuple(sum(1 << w for w, ranks in enumerate(worlds)
                      if ranks[i] > ranks[j]) for i, j in pairs)
    choices = {}

    def indexes(mask):
        while mask:
            bit = mask & -mask
            yield bit.bit_length() - 1
            mask ^= bit

    @lru_cache(None)
    def terminal(mask):
        ids = tuple(indexes(mask))
        safe = tuple(i for i in range(n)
                     if all(worlds[w][i] >= worlds[w][incumbent] for w in ids))
        costs = tuple((sum(n - 1 - worlds[w][i] for w in ids), i) for i in safe)
        return min(costs)

    @lru_cache(None)
    def optimal(mask, budget):
        stop_cost, stop_item = terminal(mask)
        best = stop_cost
        action = ('stop', stop_item)
        if budget:
            for q, winmask in enumerate(masks):
                left = mask & winmask
                right = mask ^ left
                if not left or not right:
                    continue
                cost = optimal(left, budget - 1) + optimal(right, budget - 1)
                if cost < best:
                    best = cost
                    action = ('query', q)
        choices[(mask, budget)] = action
        return best

    def replay_tree(ranks, budget):
        mask = all_worlds
        used = 0
        scalar_consistent = list(range(len(worlds)))
        while True:
            action, value = choices[(mask, budget)]
            if action == 'stop':
                # Independent list filtering, not the bit-mask transition.
                assert set(scalar_consistent) == set(indexes(mask))
                assert all(worlds[w][value] >= worlds[w][incumbent]
                           for w in scalar_consistent)
                return value, used
            i, j = pairs[value]
            answer = ranks[i] > ranks[j]
            scalar_consistent = [w for w in scalar_consistent
                                 if (worlds[w][i] > worlds[w][j]) == answer]
            left = mask & masks[value]
            mask = left if answer else mask ^ left
            used += 1
            budget -= 1

    def passive_design(query_ids):
        # Construct observation cells independently from scalar signs.
        cells = {}
        for w, ranks in enumerate(worlds):
            observations = tuple(ranks[pairs[q][0]] > ranks[pairs[q][1]]
                                 for q in query_ids)
            cells.setdefault(observations, []).append(w)
        total = 0
        unsafe = 0
        for ids in cells.values():
            candidates = []
            for i in range(n):
                if all(worlds[w][i] >= worlds[w][0] for w in ids):
                    candidates.append((sum(n - 1 - worlds[w][i] for w in ids), i))
            cost, selected = min(candidates)
            total += cost
            unsafe += sum(worlds[w][selected] < worlds[w][0] for w in ids)
        assert unsafe == 0
        return total, len(cells)

    results = []
    scalar_checks = 0
    for budget in range(n):
        opt = optimal(all_worlds, budget)
        replay_cost = 0
        uses = []
        tournament_cost = 0
        tournament_safety_violations = 0
        null_winners = []
        for ranks in worlds:
            item, used = replay_tree(ranks, budget)
            replay_cost += n - 1 - ranks[item]
            uses.append(used)
            assert used <= budget
            champion = 0
            for challenger in range(1, budget + 1):
                if ranks[challenger] > ranks[champion]:
                    champion = challenger
            tournament_cost += n - 1 - ranks[champion]
            tournament_safety_violations += ranks[champion] < ranks[0]
            if ranks[0] == n - 1:
                null_winners.append((item, champion))
            if budget == n - 1:
                assert ranks[item] == ranks[champion] == n - 1
            scalar_checks += 1
        assert replay_cost == opt
        assert tournament_safety_violations == 0
        assert all(x == (0, 0) for x in null_winners)
        direct_fraction = Fraction(tournament_cost, len(worlds) * (n - 1))
        m = budget + 1
        analytic = Fraction(n - m, (m + 1) * (n - 1))
        assert direct_fraction == analytic
        passive_candidates = []
        for query_ids in combinations(range(len(pairs)), budget):
            cost, cells = passive_design(query_ids)
            passive_candidates.append((cost, query_ids, cells))
        passive_cost, passive_queries, cells = min(passive_candidates)
        optimal_fraction = Fraction(opt, len(worlds) * (n - 1))
        passive_fraction = Fraction(passive_cost, len(worlds) * (n - 1))
        # This is the prospective falsifier, not a requirement for correctness.
        direct_matches_optimal = opt == tournament_cost
        results.append({
            'budget': budget,
            'worlds': len(worlds),
            'adaptive_safe_regret_exact': str(optimal_fraction),
            'adaptive_safe_regret': float(optimal_fraction),
            'direct_champion_regret_exact': str(direct_fraction),
            'analytic_direct_regret_exact': str(analytic),
            'direct_matches_optimal': direct_matches_optimal,
            'adaptive_query_uses_min_max': [min(uses), max(uses)],
            'best_fixed_safe_regret_exact': str(passive_fraction),
            'best_fixed_safe_regret': float(passive_fraction),
            'best_fixed_queries': [pairs[q] for q in passive_queries],
            'fixed_designs_examined': len(passive_candidates),
            'best_fixed_observation_cells': cells,
            'safety_violations': 0,
            'incumbent_best_null_worlds': len(null_winners),
        })
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if sys.platform == 'darwin' else peak * 1024
    result = {
        'calculated_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Cheap equal-information falsifier; standard reference, not a novel claim',
        'class': 'Five reachable outputs; uniform 120 strict rank-utility permutations',
        'judge': 'Exact pairwise signs only; no true utility supplied to any policy',
        'safety': 'Terminal output no worse than incumbent in every consistent world',
        'results': results,
        'all_direct_budgets_match_optimal': all(r['direct_matches_optimal'] for r in results),
        'scalar_world_budget_replays': scalar_checks,
        'independent_checks': [
            'Mask-based Bellman values vs full scalar policy replay',
            'Independent scalar-filtered version spaces and every terminal safety decision',
            'Direct scalar tournament vs analytic order-statistic expectation',
            'All full-budget outputs globally best',
            'Incumbent-best null always retains incumbent',
        ],
        'dp_cache': optimal.cache_info()._asdict(),
        'terminal_cache': terminal.cache_info()._asdict(),
        'wall_seconds': time.perf_counter() - started,
        'peak_rss_bytes': peak_bytes,
        'python': sys.version,
        'empirical_records_read': 0,
        'public_operations_in_process': 0,
        'randomness': 'None; exhaustive finite enumeration',
    }
    destination = Path(__file__).with_name('FIRST_CALCULATION.json')
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

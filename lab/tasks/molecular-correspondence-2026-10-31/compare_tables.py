"""Frozen conditional POMC subtype permutation test on selected published tables."""
import csv
import hashlib
import itertools
import json
import math
import resource
import time
import numpy as np
from feature_audit import TARGETS, SCENARIOS, table
from source_audit import OUT


def mse(a, b):
    return float(np.mean(np.square(a-b)))


def cor(a, b):
    x = np.asarray(a).ravel() - np.mean(a)
    y = np.asarray(b).ravel() - np.mean(b)
    return float(np.sum(x*y) / math.sqrt(np.sum(x*x)*np.sum(y*y)))


def analyze(H, M, HG, MG, genes):
    # Equal weights over source subtype groups and common genes; no nuclei pseudo-replication.
    hc = H - H.mean(axis=0, keepdims=True)
    mc = M - M.mean(axis=0, keepdims=True)
    baseline = mse(hc, np.zeros_like(hc))
    permutations = []
    for perm in itertools.permutations(range(3)):
        p = np.array(perm)
        permutations.append({
            "mouse_group_for_human_row": list(perm),
            "raw_mse": mse(H, M[p]),
            "global_abundance_adjusted_mse": mse(H, HG + M[p] - MG),
            "pomc_gene_centered_mse": mse(hc, mc[p]),
            "pomc_gene_centered_correlation": cor(hc, mc[p]),
            "raw_correlation": cor(H, M[p])})
    ident = permutations[0]
    per_gene = []
    for j,g in enumerate(genes):
        per_gene.append({"gene": g, "human": H[:,j].tolist(), "mouse_first": M[:,j].tolist(),
            "human_global_neurons": float(HG[j]), "mouse_global_neurons": float(MG[j]),
            "raw_mse": mse(H[:,j],M[:,j]), "centered_mse": mse(hc[:,j],mc[:,j]),
            "class_abundance_mse": mse(hc[:,j],np.zeros(3)),
            "subtype_centered_cross_product": float(np.mean(hc[:,j]*mc[:,j]))})
    # Positive known-correspondence control and abundance-only negative control.
    positive_losses = [mse(hc,hc[np.array(p)]) for p in itertools.permutations(range(3))]
    flat_mouse = np.tile(M.mean(axis=0),(3,1))
    negative_losses = [mse(H,flat_mouse[np.array(p)]) for p in itertools.permutations(range(3))]
    return {
        "genes": genes, "shape": list(H.shape), "identity": ident,
        "class_gene_abundance_baseline_mse": baseline,
        "identity_centered_reduction_vs_class_mean_percent": 100*(baseline-ident["pomc_gene_centered_mse"])/baseline,
        "global_human_abundance_only_mse": mse(H,HG),
        "identity_global_adjusted_reduction_percent": 100*(mse(H,HG)-ident["global_abundance_adjusted_mse"])/mse(H,HG),
        "identity_centered_rank_of_6": 1+sum(x["pomc_gene_centered_mse"] < ident["pomc_gene_centered_mse"]-1e-14 for x in permutations),
        "identity_raw_rank_of_6": 1+sum(x["raw_mse"] < ident["raw_mse"]-1e-14 for x in permutations),
        "mean_permutation_centered_mse": float(np.mean([p["pomc_gene_centered_mse"] for p in permutations])),
        "identity_centered_reduction_vs_permutation_mean_percent": 100*(np.mean([p["pomc_gene_centered_mse"] for p in permutations])-ident["pomc_gene_centered_mse"])/np.mean([p["pomc_gene_centered_mse"] for p in permutations]),
        "permutations": permutations, "per_gene": per_gene,
        "controls": {"positive_self_centered_losses":positive_losses,
            "positive_identity_is_unique_zero": positive_losses[0] == 0 and min(positive_losses[1:]) > 0,
            "negative_abundance_only_losses": negative_losses,
            "negative_permutation_range": max(negative_losses)-min(negative_losses)}}


def main():
    tables = {s: table(s) for s in SCENARIOS[:3]}
    pairs = sorted(set.intersection(*(set((r["gene"],r["mouse_gene"]) for r in t) for t in tables.values())))
    genes = [g for g,m in pairs]
    H,M,HG,MG = [],[],[],[]
    source_rows = []
    for s,t in tables.items():
        human_cols = [c for c in t[0] if c.startswith("C4-")]
        mouse_cols = [c for c in t[0] if c.startswith("C465-")]
        assert len(human_cols)==1 and mouse_cols
        rows = {(r["gene"],r["mouse_gene"]): r for r in t}
        h,m,hg,mg = [],[],[],[]
        for pair in pairs:
            r=rows[pair]
            hv = float(r[human_cols[0]])
            mv = float(r[mouse_cols[0]])
            h.append(hv);m.append(mv)
            hg.append(float(r["expr_human_all"]));mg.append(float(r["expr_mouse_all"]))
            source_rows.append({"scenario":s,"gene":pair[0],"mouse_gene":pair[1],"human_cluster":human_cols[0],
                "mouse_first":mouse_cols[0],"human_expression":hv,"mouse_expression":mv,
                "all_mouse_expressions":{c:float(r[c]) for c in mouse_cols},
                "source_ratio":float(r["pct_ratio_adj"]),"recomputed_ratio":math.log2(hv/mv)})
        H.append(h);M.append(m);HG.append(hg);MG.append(mg)
    H,M,HG,MG = map(lambda x:np.asarray(x,dtype=float),(H,M,HG,MG))
    assert np.isfinite(H).all() and np.isfinite(M).all()
    # These are the same source global-neuron definitions across selected subtype tables.
    max_hg_diff = float(np.max(np.abs(HG-HG[0])))
    max_mg_diff = float(np.max(np.abs(MG-MG[0])))
    assert max_hg_diff < 1e-12 and max_mg_diff < 1e-12
    ratio_error = max(abs(r["source_ratio"]-r["recomputed_ratio"]) for r in source_rows)
    assert ratio_error < 1e-12
    all5=analyze(H,M,HG[0],MG[0],genes)
    fixed = [j for j,g in enumerate(genes) if g in TARGETS]
    fixed4=analyze(H[:,fixed],M[:,fixed],HG[0,fixed],MG[0,fixed],[genes[j] for j in fixed])
    out={"status":"conditional_selected_published_table_obstacle_test_not_held_gene_prediction",
        "completed_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "source_order":list(tables),"source_rows":source_rows,
        "all_five_common_receptors":all5,"four_prespecified_targets":fixed4,
        "source_checks":{"global_human_max_repeat_difference":max_hg_diff,"global_mouse_max_repeat_difference":max_mg_diff,"max_author_ratio_reconstruction_error":ratio_error},
        "protocol_sha256":hashlib.sha256((OUT/"PROTOCOL.md").read_bytes()).hexdigest(),
        "peak_rss_bytes_macos":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "numpy_version":np.__version__,"no_biological_uncertainty_inferred":True,
        "independent_validation":False}
    (OUT/"COMPARISON.json").write_text(json.dumps(out,indent=2)+"\n")
    with (OUT/"PERMUTATIONS.csv").open("w") as f:
        writer=csv.DictWriter(f,fieldnames=["panel"]+list(all5["permutations"][0]));writer.writeheader()
        for name,result in [("all5",all5),("fixed4",fixed4)]:
            for r in result["permutations"]:writer.writerow({"panel":name,**r})
    print(json.dumps({"all5":{k:v for k,v in all5.items() if k not in ["permutations","per_gene"]},
        "fixed4":{k:v for k,v in fixed4.items() if k not in ["permutations","per_gene"]},
        "source_checks":out["source_checks"],"peak_rss_bytes_macos":out["peak_rss_bytes_macos"]},indent=2))


if __name__ == "__main__":
    main()

"""Finite overlap/source-dependency and table coverage audit; no fitted model."""
import csv
import hashlib
import io
import json
from source_audit import OUT, BASE, read

TARGETS = "OXTR AVPR1A AVPR1B AVPR2 MC3R MC4R LEPR GHSR HCRTR1 HCRTR2 NPY1R NPY2R NPY4R NPY5R CRHR1 CRHR2 GNRHR KISS1R GALR1 GALR2 GALR3 SSTR1 SSTR2 SSTR3 SSTR4 SSTR5 NTSR1 NTSR2 TACR1 TACR2 TACR3 TRHR PRLHR QRFPR NMUR1 NMUR2 RXFP1 RXFP2 SCTR CALCR CALCRL GLP1R GIPR GCGR PTH1R PTH2R OPRM1 OPRD1 OPRK1 NPBWR1 NPBWR2 UTS2R PROKR1 PROKR2".split()
SCENARIOS = ["pomc_lepr", "pomc_glp1r", "pomc_glipr1", "agrp"]


def flatten(x):
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        return sum((flatten(v) for v in x.values()), [])
    return sum((flatten(v) for v in x), [])


def table(s):
    b = read(OUT / "sources" / (s + "_gpcr_table.txt"), "selected published GPCR table; consumed conditional evaluation")
    text = b.decode()
    delim = csv.Sniffer().sniff(text[:4096], delimiters=",\t").delimiter
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def run():
    targets = set(TARGETS)
    assert len(targets) == len(TARGETS)
    out = {"target_count": len(targets), "targets": TARGETS, "protocol_sha256": hashlib.sha256((OUT/"PROTOCOL.md").read_bytes()).hexdigest()}
    for fname in ["feature_set_cross_species.json", "feature_set.json"]:
        genes = flatten(json.loads(read(OUT / "sources" / fname, "actual fixed published integration feature membership")))
        out[fname] = {"features": len(genes), "unique_features": len(set(genes)), "target_overlap": sorted(targets.intersection(genes)), "target_overlap_count": len(targets.intersection(genes))}
    tables = {s: table(s) for s in SCENARIOS}
    out["tables"] = {s: {"rows": len(t), "columns": list(t[0]), "genes": [r["gene"] for r in t], "ortholog_pairs": [[r["gene"],r["mouse_gene"]] for r in t]} for s,t in tables.items()}
    common = set.intersection(*(set((r["gene"],r["mouse_gene"]) for r in tables[s]) for s in SCENARIOS[:3]))
    out["common_pomc_pairs"] = sorted(common)
    out["common_pomc_pair_count"] = len(common)
    out["common_pomc_predeclared_targets"] = sorted(g for g,m in common if g in targets)
    cross = set(flatten(json.loads((OUT/"sources/feature_set_cross_species.json").read_text())))
    out["common_pomc_direct_crossspecies_features"] = sorted(g for g,m in common if g in cross)
    # Existing mapping is descriptive; no expression reconstruction is inferred from it.
    b = read(BASE / "data/atlas/matched_clusters_scviCorPruned.tsv", "same pinned published pairing for coverage audit")
    mapping = list(csv.DictReader(io.StringIO(b.decode()), delimiter="\t"))
    out["published_mapping"] = {"edges": len(mapping), "human_clusters": len(set(r["from"] for r in mapping)), "mouse_clusters": len(set(r["to"] for r in mapping))}
    (OUT / "FEATURE_AUDIT.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k:v for k,v in out.items() if k != "tables"}, indent=2))
    print(json.dumps({s:{"rows":len(t),"columns":list(t[0])} for s,t in tables.items()}, indent=2))


if __name__ == "__main__":
    run()

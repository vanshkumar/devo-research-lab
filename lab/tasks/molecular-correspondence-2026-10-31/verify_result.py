"""Separately written scalar reconstruction from exact public source tables."""
import csv
import hashlib
import io
import itertools
import json
import math
import resource
from source_audit import OUT, read, ledger, save


def mean(x):
    return math.fsum(x)/len(x)


def loss(H,M,p):
    return mean([(H[i][j]-M[p[i]][j])**2 for i in range(3) for j in range(len(H[0]))])


def main():
    results=json.loads(read(OUT/"COMPARISON.json","scalar reimplementation comparison reference"))
    features=json.loads(read(OUT/"FEATURE_AUDIT.json","feature overlap/exposure reconstruction"))
    rows={}
    exposure={}
    for s in ["pomc_lepr","pomc_glp1r","pomc_glipr1","agrp"]:
        text=read(OUT/"sources"/(s+"_gpcr_table.txt"),"independent scalar table reread; all source values remain consumed").decode()
        data=list(csv.DictReader(io.StringIO(text),delimiter=","))
        rows[s]=data
        pairs=[(r["gene"],r["mouse_gene"]) for r in data]
        assert len(set(pairs))==len(data)
        hcols=[k for k in data[0] if k.startswith("C4-")]
        mcols=[k for k in data[0] if k.startswith("C465-")]
        exposure[s]={"source_rows":len(data),"human_clusters":hcols,"mouse_clusters":mcols,
            "genes":sorted(set(r["gene"] for r in data)),"ortholog_pairs":pairs,
            "cluster_expression_values":len(data)*(len(hcols)+len(mcols)),
            "global_expression_values":2*len(data),"source_ratio_values":len(data)}
    pairs=sorted(set.intersection(*[{(r["gene"],r["mouse_gene"]) for r in rows[s]} for s in list(rows)[:3]]))
    H=[];M=[]
    for s in list(rows)[:3]:
        d={(r["gene"],r["mouse_gene"]):r for r in rows[s]}
        hc=next(k for k in rows[s][0] if k.startswith("C4-"))
        mc=next(k for k in rows[s][0] if k.startswith("C465-"))
        H.append([float(d[p][hc]) for p in pairs]);M.append([float(d[p][mc]) for p in pairs])
    cols=len(pairs)
    Hmeans=[mean([H[i][j] for i in range(3)]) for j in range(cols)]
    Mmeans=[mean([M[i][j] for i in range(3)]) for j in range(cols)]
    hc=[[H[i][j]-Hmeans[j] for j in range(cols)] for i in range(3)]
    mc=[[M[i][j]-Mmeans[j] for j in range(cols)] for i in range(3)]
    errors=[];scalar=[]
    for p in itertools.permutations(range(3)):
        raw=loss(H,M,p);cen=loss(hc,mc,p)
        ref=next(r for r in results["all_five_common_receptors"]["permutations"] if r["mouse_group_for_human_row"]==list(p))
        errors += [abs(raw-ref["raw_mse"]),abs(cen-ref["pomc_gene_centered_mse"])]
        scalar.append({"permutation":list(p),"raw_mse":raw,"centered_mse":cen})
    class_loss=mean([x*x for row in hc for x in row])
    mean_offset=mean([(x-y)**2 for x,y in zip(Hmeans,Mmeans)])
    var_mouse=mean([x*x for row in mc for x in row])
    algebra_errors=[abs(r["raw_mse"]-r["centered_mse"]-mean_offset) for r in scalar]
    algebra_errors.append(abs(mean([r["centered_mse"] for r in scalar])-class_loss-var_mouse))
    per_gene=[]
    for j,(g,m) in enumerate(pairs):
        base=mean([hc[i][j]**2 for i in range(3)])
        err=mean([(hc[i][j]-mc[i][j])**2 for i in range(3)])
        per_gene.append({"gene":g,"class_mean_mse":base,"identity_centered_mse":err,"gain":base-err})
    # Independently check the predeclared four-gene restriction as well.
    ix=[j for j,(g,m) in enumerate(pairs) if g in features["targets"]]
    fh=[[r[j] for j in ix] for r in hc];fm=[[r[j] for j in ix] for r in mc]
    fixed_errors=[]
    for p in itertools.permutations(range(3)):
        ref=next(r for r in results["four_prespecified_targets"]["permutations"] if r["mouse_group_for_human_row"]==list(p))
        fixed_errors.append(abs(loss(fh,fm,p)-ref["pomc_gene_centered_mse"]))
    assert max(errors+algebra_errors+fixed_errors)<1e-12
    pins=[]
    manifest=json.loads(read(OUT/"SOURCE_MANIFEST.json","verify published Git tree and exact source pins"))
    for r in manifest:
        b=read(OUT/"sources"/r["file"],"independent SHA256/Git blob verification")
        sha=hashlib.sha256(b).hexdigest()
        assert sha==r["sha256"]
        pins.append({"file":r["file"],"sha256":sha,"pass":True})
    cross=set(json.loads(read(OUT/"sources/feature_set_cross_species.json","independent source feature membership reconstruction")))
    human=set(json.loads(read(OUT/"sources/feature_set.json","independent human feature membership reconstruction")))
    targets=set(features["targets"])
    overlap={"cross_species":len(targets&cross),"human_clustering":len(targets&human),
        "either_feature_set":len(targets&(cross|human)),"both_feature_sets":len(targets&cross&human),
        "neither_listed_feature_set":sorted(targets-cross-human)}
    metadata=json.loads(read(OUT/"sources/cam111988_datacite.json","source metadata and explicit absence of file sizes/content URL"))["data"]["attributes"]
    source_metadata={k:metadata[k] for k in ["doi","url","rightsList","sizes","formats","contentUrl","version","updated"]}
    out={"max_scalar_numpy_disagreement":max(errors+fixed_errors),"max_decomposition_error":max(algebra_errors),
        "scalar_permutations":scalar,"best_posthoc_permutation_not_adopted":min(scalar,key=lambda x:x["centered_mse"]),
        "class_mean_mse":class_loss,"species_gene_mean_offset_mse":mean_offset,
        "mouse_within_gene_variance":var_mouse,"per_gene_identity_gain":per_gene,
        "feature_overlap":overlap,"pins":pins,"exposure":exposure,
        "distinct_exported_gene_pairs":len(set((r["gene"],r["mouse_gene"]) for d in rows.values() for r in d)),
        "all_exported_cluster_expression_values":sum(r["cluster_expression_values"] for r in exposure.values()),
        "datacite_metadata":source_metadata,"no_donor_units_in_selected_tables":True,
        "peak_rss_bytes_macos":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (OUT/"SCALAR_VERIFICATION.json").write_text(json.dumps(out,indent=2)+"\n")
    a=ledger()
    # Conservative whole-run allowance for Python/NumPy/runtime reads, repeated source
    # inspection, source-tool orchestration, documentation and output verification.
    # It replaces (does not stack with) the initial25MB context reserve.
    a["context_code_output_reserve_bytes"]=150000000
    a["reserve_note"]="150MB conservative whole-run context/dependency/documentation/output allowance; explicit scientific source/data charges remain additional; exact provider network bytes unavailable as separately recorded."
    save(a)
    print(json.dumps({k:v for k,v in out.items() if k not in ["pins","exposure","datacite_metadata"]},indent=2))
    print(json.dumps({"public_requests_charged":a["public_requests"],"new_ingress_bytes_charged":a["new_ingress_bytes"],"read_bytes_charged":a["charged_read_bytes"]}))


if __name__=="__main__":
    main()

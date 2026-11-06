"""Independent audit: stdlib CSV/counts and literal archived-R response semantics.

Does not import the campaign's run.py or any of its outputs. Does not execute Rmd.
"""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"data/social_learning"
OUT=Path(__file__).resolve().parent


def iscolor(value):
    return value in {"p","g"}


def exact_twosided(k,n):
    # At p=.5 denominators cancel in the probability-ordering definition.
    threshold=math.comb(n,k)
    return sum(math.comb(n,j) for j in range(n+1) if math.comb(n,j)<=threshold)/2**n


def main():
    raw=(DATA/"data_primacy.csv").read_bytes()
    rows=list(csv.DictReader(raw.decode().splitlines()))
    results=[]
    detail=[]
    for treatment in ["T","C1","C2"]:
        group=[(i+2,r) for i,r in enumerate(rows) if r["treatment"]==treatment]
        eligible=[]
        r_glmm=[]
        supplied=[]
        for line,r in group:
            dc=iscolor(r["color_court_1"]) and iscolor(r["color_court_2"])
            mate=iscolor(r["test_color"])
            first=r["demo_color_2"] if treatment=="C2" else r["demo_color_1"]
            last=r["demo_color_1"] if treatment=="C1" else r["demo_color_2"]
            ok=dc and mate
            if ok:
                eligible.append((r["test_color"]==first,r["test_color"]==last))
            # Literal ifelse((equal == 1) & (dc == 1),1,0):
            # FALSE & NA is FALSE, so all non-DC trials receive 0;
            # TRUE & NA stays NA for DC trials without a mating.
            response=0 if not dc else None if not mate else int(r["test_color"]==first)
            if response is not None:
                r_glmm.append(response)
            observed=None if r["copy_dc_bin"]=="NA" else int(r["copy_dc_bin"])
            if observed is not None:
                supplied.append(observed)
            detail.append(dict(csv_line=line,treatment=treatment,double_courtship=dc,mating=mate,eligible=ok,
                               reconstructed_script_score=response,supplied_score=observed,
                               paper_score=int(r["test_color"]==last) if ok else None))
        kfirst=sum(x[0] for x in eligible)
        klast=sum(x[1] for x in eligible)
        n=len(eligible)
        mismatch=sum(1 for x in detail if x["treatment"]==treatment and x["supplied_score"]!=x["reconstructed_script_score"])
        results.append(dict(treatment=treatment,total=len(group),eligible_n=n,first_or_unique_k=kfirst,last_or_unique_k=klast,
                            paper_binomial_p=exact_twosided(klast,n),
                            archived_glmm_n=len(r_glmm),archived_glmm_k=sum(r_glmm),
                            noneligible_rows_in_archived_glmm=sum(1 for x in detail if x["treatment"]==treatment and not x["eligible"] and x["reconstructed_script_score"] is not None),
                            supplied_n=len(supplied),supplied_k=sum(supplied),script_vs_supplied_mismatches=mismatch))
    # Independent invariant: in contradictory-demo T, paper-last + first counts equal n.
    mainrow=results[0]
    assert mainrow["first_or_unique_k"]+mainrow["last_or_unique_k"]==mainrow["eligible_n"]
    assert sum(r["eligible_n"] for r in results)==205
    assert all(r["script_vs_supplied_mismatches"]==0 for r in results)
    result={"csv_sha256":hashlib.sha256(raw).hexdigest(),"row_count":len(rows),"counts":results,
            "method":"Independent stdlib CSV reconstruction and exact integer binomial enumeration; no root results imported.",
            "rmd_sha256":hashlib.sha256((DATA/"primacy_bias_script.Rmd").read_bytes()).hexdigest(),
            "not_executed":"Original Rmd, fonts, installs, or mixed-model fitting."}
    (OUT/"audit_counts.json").write_text(json.dumps(result,indent=2)+"\n")
    with (OUT/"audit_row_reconstruction.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=detail[0]);w.writeheader();w.writerows(detail)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()

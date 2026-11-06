"""Plot saved numerical results, without rerunning or fitting models."""
from pathlib import Path
import json
import csv

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
summary=json.loads((HERE/"outputs/summary.json").read_text())
trajectory=list(csv.DictReader((HERE/"outputs/pilot_b_trajectories.csv").open()))
fig,axs=plt.subplots(1,2,figsize=(11,4),layout="constrained")
for method,style in [("oja","o-"),("pca","s--"),("full_linear","^-"),("oracle_signal_axis","d:")]:
    sub=[r for r in summary["pilot_a"] if r["method"]==method and r["rho"]==.8]
    axs[0].plot([r["v"] for r in sub],[r["median_shifted_r2"] for r in sub],style,label=method)
axs[0].set_xscale("log",base=2)
axs[0].axhline(0,color="k",alpha=.2,lw=1)
axs[0].set(xlabel="Nuisance variance (signal variance 1.0625)",ylabel="Held-out shifted R² (median of 20 seeds)",title="A. Correlation at training can hide bottleneck loss")
axs[0].legend(fontsize=8)
for method in ["constant_oja","annealed_oja","frozen_oja","projected_hebb"]:
    sub=[r for r in trajectory if r["environment"]=="switch" and r["method"]==method and int(r["t"])>=20000]
    times=sorted(set(int(r["t"]) for r in sub))
    values=np.array([[float(r["current_pc_alignment_sq"]) for r in sub if int(r["t"])==t] for t in times])
    # t=20000 describes the pre-switch axis, so begin the switched-axis curve at t=20100.
    axs[1].plot(np.array(times[1:])-20000,np.median(values[1:],axis=1),label=method)
    axs[1].fill_between(np.array(times[1:])-20000,np.quantile(values[1:],.1,axis=1),np.quantile(values[1:],.9,axis=1),alpha=.12)
axs[1].axhline(.9,color="k",alpha=.3,ls=":")
axs[1].set(xlabel="Observations after 90° covariance switch",ylabel="Squared alignment to current dominant axis",ylim=(-.02,1.02),title="B. Bounded weights can still fail to track")
axs[1].legend(fontsize=8)
fig.savefig(HERE/"outputs/pilots.png",dpi=180)

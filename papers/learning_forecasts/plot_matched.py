"""Plot saved matched-cohort diagnostic; reads no raw behavior or model files."""
from pathlib import Path
import hashlib
import json
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "devo-forecast-mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "experiments/matched_history_diagnostic_2026-10-29/RESULT.json"
data = json.loads(SOURCE.read_text())
assert data["n"] == 24 and not data["external_access"]
assert not data["new_learner_fit"]

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0),
                         gridspec_kw={"width_ratios": [1.45, 1]})
colors = {"conditional_rnn": "#138060", "autonomous_rnn": "#bd4c28",
          "autonomous_growth": "#356fa0"}
labels = {"conditional_rnn": "RNN: actual-history diagnostic",
          "autonomous_rnn": "RNN: autonomous forecast",
          "autonomous_growth": "Growth: autonomous forecast"}
x = 1250 + np.arange(6) * 500
axes[0].plot(x, np.asarray(data["observed_curve"]) * 100,
             "o-", color="#222222", linewidth=2, label="Observed")
order = ["conditional_rnn", "autonomous_growth", "autonomous_rnn"]
for name in order:
    metric = data["metrics"][name]
    axes[0].plot(x, np.asarray(metric["forecast_curve"]) * 100,
                 "--" if name == "conditional_rnn" else "-",
                 color=colors[name], linewidth=2, label=labels[name])
axes[0].set(title="A  Same 24 animals and exact-100% endpoint",
            xlabel="Task opportunity (500-trial bin midpoint)",
            ylabel="Equal-side accuracy (%)", ylim=(48, 70))
axes[0].legend(frameon=False, fontsize=9, loc="upper left")
axes[0].grid(axis="y", alpha=.2)
values = [100 * data["metrics"][name]["population_curve_mae"] for name in order]
axes[1].bar(np.arange(3), values, color=[colors[n] for n in order], width=.65)
axes[1].set_xticks(np.arange(3), ["Actual-history\nRNN diagnostic", "Autonomous\ngrowth", "Autonomous\nRNN"])
for i, value in enumerate(values):
    axes[1].text(i, value + .15, f"{value:.2f}", ha="center", fontweight="bold")
axes[1].set(title="B  Population mean-curve error",
            ylabel="Mean absolute error (percentage points)", ylim=(0, 8.3))
axes[1].grid(axis="y", alpha=.2)
axes[1].set_axisbelow(True)
fig.suptitle("History-informed tracking and prospective acquisition forecasts", fontsize=15)
fig.text(.055, .075,
         "Diagnostic is postvalidation: actual future stimuli and prior choices/rewards are supplied.\n"
         "Central prefix state + analytic probabilities differ from the autonomous 512-particle mixture.\n"
         "Curves and bars are descriptive; this comparison does not isolate a causal source of forecast error.",
         fontsize=9, va="bottom")
fig.subplots_adjust(left=.07, right=.98, bottom=.29, top=.83, wspace=.32)
out = HERE / "figures"
out.mkdir(exist_ok=True)
for suffix in ("png", "svg"):
    fig.savefig(out / f"matched_history.{suffix}", dpi=180)
plt.close(fig)
(out / "MATCHED_HISTORY_SOURCE.json").write_text(json.dumps({
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "scope": "Descriptive saved-output plot; no new observations or fits",
    "matplotlib": matplotlib.__version__, "numpy": np.__version__,
}, indent=2) + "\n")
print(out / "matched_history.png")

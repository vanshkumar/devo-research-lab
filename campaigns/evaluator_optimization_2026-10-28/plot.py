"""Render the frozen evaluator study analysis without changing study outputs.

Usage: .venv/bin/python campaigns/evaluator_optimization_2026-10-28/plot.py \
  --analysis ANALYSIS.json --base-dir TRAJECTORY_DIRECTORY
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ["MPLCONFIGDIR"] = str(ROOT / ".mplconfig")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ARMS = ("oracle_joint", "learned35_joint", "learned35_fixed",
        "learned140_joint", "untutored_joint", "shuffled35_joint")
LABELS = {"oracle_joint": "Oracle", "learned35_joint": "35 joint",
          "learned35_fixed": "35 fixed", "learned140_joint": "140 joint",
          "untutored_joint": "Untutored", "shuffled35_joint": "Shuffled35"}
COLORS = {"oracle_joint": "#2566a2", "learned35_joint": "#c45a17",
          "learned35_fixed": "#9571b1", "learned140_joint": "#27846b",
          "untutored_joint": "#8a785c", "shuffled35_joint": "#747b82"}


def finite(values, label):
    if any(value is None for value in values):
        raise ValueError(f"Undefined {label}; no plants may be omitted for plotting.")
    result = np.asarray(values, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError(f"Nonfinite {label}; no plants may be omitted for plotting.")
    return result


def column(analysis, arm, key):
    plants = analysis["analysis"]["plant_ids"]
    rows = analysis["plant_level"][arm]
    if [row["plant_id"] for row in rows] != plants:
        raise ValueError(f"Plant order differs across analysis rows for {arm}")
    return finite([row[key] for row in rows], f"{arm}/{key}")


def trajectory(base_dir, plants, arm, rounds):
    curves = []
    for plant in plants:
        path = base_dir / f"plant_{plant:03d}" / f"{arm}_trajectory.npz"
        with np.load(path, allow_pickle=False) as z:
            losses = np.asarray(z["true_losses"], dtype=float)
            if losses.ndim != 1 or len(losses) <= rounds:
                raise ValueError(f"Trajectory does not contain round {rounds}: {path}")
            if not np.isfinite(losses[:rounds+1]).all() or losses[0] <= 0:
                raise ValueError(f"Undefined/nonfinite trajectory normalization: {path}")
            if not np.array_equal(z["queries"][:rounds+1], 1+10*np.arange(rounds+1)):
                raise ValueError(f"Unmatched feedback budget: {path}")
            curves.append(losses[:rounds+1]/losses[0])
    return np.asarray(curves)


def extension_available(base_dir, plants):
    for plant in plants:
        for arm in ("oracle_joint", "learned35_joint"):
            path = base_dir / f"plant_{plant:03d}" / f"{arm}_trajectory.npz"
            with np.load(path, allow_pickle=False) as z:
                if len(z["true_losses"]) < 129:
                    return False
    return True


def mean_sem(ax, x, values, arm, label=None):
    mean = values.mean(axis=0)
    sem = values.std(axis=0, ddof=1)/np.sqrt(len(values)) if len(values) > 1 else np.zeros_like(mean)
    ax.fill_between(x, mean-sem, mean+sem, color=COLORS[arm], alpha=.12, linewidth=0)
    ax.plot(x, mean, color=COLORS[arm], linewidth=2.0, label=label or LABELS[arm])


def bootstrap_bar(ax, x, summary, color, linewidth=2.2):
    mean = summary["mean"]
    interval = summary["paired_plant_percentile_95_interval"]
    if mean is None or interval is None:
        raise ValueError("Undefined endpoint summary; no plants may be omitted for plotting.")
    lo, hi = interval
    ax.vlines(x, lo, hi, color=color, linewidth=linewidth, zorder=5)
    ax.hlines([lo, hi], x-.055, x+.055, color=color, linewidth=linewidth, zorder=5)
    ax.scatter([x], [mean], s=48, color=color, edgecolor="white", linewidth=.7, zorder=6)


def style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e8e8e8", linewidth=.7, zorder=0)
    ax.tick_params(labelsize=9)
    ax.set_axisbelow(True)


def render(analysis, base_dir):
    plants = analysis["analysis"]["plant_ids"]
    rounds = int(analysis["analysis"]["rounds"])
    n = len(plants)
    if not n:
        raise ValueError("Empty study ensemble")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 11, "axes.labelsize": 10,
                         "pdf.fonttype": 42, "ps.fonttype": 42,
                         "savefig.facecolor": "white"})
    fig, axes = plt.subplots(2, 2, figsize=(12, 9.4))
    fig.subplots_adjust(left=.085, right=.975, bottom=.17, top=.925,
                        wspace=.27, hspace=.43)
    for ax in axes.flat:
        style_axis(ax)
    jitter = np.linspace(-.115, .115, n) if n > 1 else np.array([0.])

    ax = axes[0, 0]
    for x, arm in enumerate(ARMS):
        values = column(analysis, arm, "normalized_final_true_loss")
        ax.scatter(x+jitter, values, s=23, color=COLORS[arm], alpha=.57,
                   linewidth=0, zorder=3)
        bootstrap_bar(ax, x, analysis["arm_summaries"][arm]["normalized_final_true_loss"], COLORS[arm])
    ax.axhline(1, color="#555555", linestyle="--", linewidth=1, label="Initial error")
    ax.set_xticks(np.arange(len(ARMS)))
    ax.set_xticklabels([LABELS[arm].replace(" ", "\n") for arm in ARMS])
    ax.set_xlim(-.55, len(ARMS)-.45)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("True target MSE / initial MSE")
    ax.set_title(f"A  Terminal target error ({rounds} rounds)", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper right")

    ax = axes[0, 1]
    for arm in ("oracle_joint", "learned35_joint", "learned140_joint", "shuffled35_joint"):
        values = trajectory(base_dir, plants, arm, rounds)
        saved = column(analysis, arm, "normalized_final_true_loss")
        if not np.allclose(values[:, -1], saved, rtol=1e-12, atol=1e-12):
            raise ValueError(f"Trajectory/analysis endpoint mismatch: {arm}")
        mean_sem(ax, np.arange(rounds+1), values, arm)
    ax.set_xlim(0, rounds)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Optimization round (10 feedback slots)")
    ax.set_ylabel("True target MSE / initial MSE")
    ax.set_title("B  Target error during optimization", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)

    ax = axes[1, 0]
    a35 = column(analysis, "learned35_joint", "terminal_true_mse")
    a140 = column(analysis, "learned140_joint", "terminal_true_mse")
    for offset, y35, y140 in zip(jitter, a35, a140):
        ax.plot([offset, 1+offset], [y35, y140], color="#b5b5b5", alpha=.65,
                linewidth=.8, zorder=1)
    for x, arm, values in ((0, "learned35_joint", a35), (1, "learned140_joint", a140)):
        ax.scatter(x+jitter, values, s=28, color=COLORS[arm], alpha=.75, linewidth=0, zorder=3)
        bootstrap_bar(ax, x, analysis["arm_summaries"][arm]["terminal_true_mse"], COLORS[arm])
    threshold = analysis["analysis"].get("secondary_target_fidelity_mse_threshold", .4)
    ax.axhline(threshold, color="#777777", linewidth=1, linestyle=":", label=f"MSE = {threshold:g}")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["35 tutor renditions", "140 tutor renditions"])
    ax.set_xlim(-.4, 1.4)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Terminal true target MSE")
    ax.set_title("C  Additional tutoring, paired plants", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8, loc="upper right")

    ax = axes[1, 1]
    extension = rounds == 64 and extension_available(base_dir, plants)
    if extension:
        for arm in ("oracle_joint", "learned35_joint"):
            curves = trajectory(base_dir, plants, arm, 128)
            mean_sem(ax, np.arange(64, 129), curves[:, 64:129], arm)
        ax.set_xlim(64, 128)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Optimization round (10 feedback slots)")
        ax.set_ylabel("True target MSE / initial MSE")
        ax.set_title("D  Additional optimization", loc="left", fontweight="bold")
        ax.legend(frameon=False, fontsize=8)
    else:
        gain35 = column(analysis, "learned35_joint", "final_gain")
        gain140 = column(analysis, "learned140_joint", "final_gain")
        ax.scatter(gain35, gain140, s=36, color="#555b65", alpha=.75, linewidth=0, zorder=3)
        ax.plot([0, 2], [0, 2], color="#aaaaaa", linewidth=1, linestyle=":")
        ax.axhline(1, color="#888888", linewidth=.8, linestyle="--")
        ax.axvline(1, color="#888888", linewidth=.8, linestyle="--")
        ax.set_xlim(-.04, 2.04)
        ax.set_ylim(-.04, 2.04)
        ax.set_xlabel("Final gain, 35 tutor renditions")
        ax.set_ylabel("Final gain, 140 tutor renditions")
        ax.set_title("D  Final auditory-drive gain", loc="left", fontweight="bold")

    fig.suptitle("Sensory evaluator feedback through independently drawn motor plants", fontsize=14)
    uncertainty = "A, C: means and 95% paired whole-plant bootstrap intervals. B"
    uncertainty += ", D: means ±1 SEM across plants." if extension else ": means ±1 SEM across plants."
    footer = (f"N = {n} independent reachable plants; six supplied contexts; source clock; zero dynamical noise.\n"
              f"{uncertainty} All plants shown in A, C.\n"
              "Gain scales signed auditory drive; the assay does not model physical sound pressure. Secondary comparisons are descriptive.")
    fig.text(.085, .088, footer, ha="left", va="center", fontsize=8.6, linespacing=1.5, color="#444444")
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", "--analysis-json", "--analysisJSON", dest="analysis_path", type=Path, required=True)
    parser.add_argument("--base-dir", type=Path, required=True)
    args = parser.parse_args()
    analysis = json.loads(args.analysis_path.read_text())
    fig = render(analysis, args.base_dir)
    output_dir = HERE / "figures"
    output_dir.mkdir(exist_ok=True)
    fig.savefig(output_dir/"result.png", dpi=200)
    fig.savefig(output_dir/"result.pdf")
    plt.close(fig)
    print(json.dumps({"png": str(output_dir/"result.png"), "pdf": str(output_dir/"result.pdf")}))


if __name__ == "__main__":
    main()

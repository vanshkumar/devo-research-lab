"""Render the primary intervals and absolute proper risks from the saved analysis."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter


def main():
    result = get(HERE / 'ANALYSIS.json')
    labels = ['Original growth', 'Recent growth · 100', 'Recent growth · 250']
    references = ['growth', 'recent100', 'recent250']
    assert [r['reference'] for r in result['primary']] == references
    colors = ['#224c70', '#12776f', '#846047']
    fig, (contrast_ax, risk_ax) = plt.subplots(1, 2, figsize=(11, 4.6),
        gridspec_kw={'width_ratios': [1.38, 1.]})
    fig.subplots_adjust(left=.22, right=.965, bottom=.25, top=.73, wspace=.43)
    fig.text(.045, .90, 'Independent acquisition forecasts', fontsize=19, weight='bold', color='#182a36')
    fig.text(.045, .827, '192 deposited animals  ·  1,001–3,000 scored opportunities', fontsize=11, color='#4b606a')

    contrast_ax.axvline(0, color='#627983', lw=1.1, ls='--', zorder=0)
    for j, record in enumerate(result['primary']):
        band = record['D']
        x = band['point']
        contrast_ax.errorbar(x, j, xerr=[[x-band['lower']], [band['upper']-x]],
            fmt='o', ms=7, capsize=4, color=colors[j], lw=2)
    contrast_ax.set_yticks([0, 1, 2], labels)
    contrast_ax.set_ylim(2.6, -.55)
    contrast_ax.xaxis.set_major_formatter(FormatStrFormatter('%.4f'))
    contrast_ax.set_title('Primary contrasts at 200 opportunities', loc='left', weight='bold', fontsize=11, pad=12)
    contrast_ax.set_xlabel('0.9 × reference risk − GRU risk')
    contrast_ax.grid(axis='x', color='#d7e0e3', linewidth=.65)
    contrast_ax.set_axisbelow(True)

    keys = references + ['gru']
    legend_labels = ['Original', 'Recent 100', 'Recent 250', 'GRU975']
    risk_lookup = {(r['cutoff'], r['actor']): r['mean_metrics']['proper_V']
                   for r in result['absolute_calibration']}
    x = np.arange(2)
    for j, (actor, name, color) in enumerate(zip(keys, legend_labels, colors + ['#a14a53'])):
        risks = [risk_lookup[(origin, actor)] for origin in (200, 1000)]
        risk_ax.bar(x+(j-1.5)*.19, risks, width=.18, label=name, color=color)
    risk_ax.set_xticks(x, ['200', '1,000'])
    risk_ax.set_xlabel('Observed opportunities at forecast origin')
    risk_ax.set_ylabel('Mean mixed energy score')
    risk_ax.set_title('Absolute risk at both origins', loc='left', weight='bold', fontsize=11, pad=12)
    risk_ax.legend(loc='upper center', bbox_to_anchor=(.5, -.25), ncol=2, frameon=False, fontsize=8)
    risk_ax.grid(axis='y', color='#d7e0e3', linewidth=.65)
    risk_ax.set_axisbelow(True)
    for ax in (contrast_ax, risk_ax):
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['bottom', 'left']].set_color('#a0aeb3')
        ax.tick_params(color='#a0aeb3', labelcolor='#263b44', labelsize=9)
    fig.text(.045, .042, 'Nominal simultaneous 95% paired-animal intervals at left. Zero marks a 10% risk reduction.',
             fontsize=9, color='#4b606a')
    fig.savefig(HERE / 'CONFIRMATION_SUMMARY.png', dpi=190, facecolor='white')
    plt.close(fig)
    receipt('FIGURE', all_jobs_terminal=True)


if __name__ == '__main__':
    main()

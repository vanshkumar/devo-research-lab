"""Plot saved independent evidence only; no source circuits or outcomes opened."""
import os
from pathlib import Path
HERE=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(HERE/'matplotlib_cache')
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    order=json.loads((HERE/'ADVERSARIAL_SUMMARY.json').read_text())['plants']
    actor=json.loads((HERE/'FINAL_SCIENTIFIC_SUMMARY.json').read_text())['normalized_actor_control']
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,ax=plt.subplots(1,3,figsize=(13.5,4.2),constrained_layout=True)
    x=np.arange(3);labels=[str(r['plant']) for r in order]
    ax[0].bar(x-.17,[1000*r['fresh_no_clock_wrong_minus_target_Hz'] for r in order],width=.32,label='Isolated / quiet reset',color='#3b6c9c')
    ax[0].bar(x+.17,[1000*r['continuous_cycle5_order_wrong_minus_target_Hz'] for r in order],width=.32,label='Continuous cycle 5',color='#de8d36')
    ax[0].axhline(0,color='black',lw=.8);ax[0].set(xticks=x,xticklabels=labels,ylabel='Wrong − target cost (mHz)',title='A  Wrong-order preference survives')
    ax[0].legend(fontsize=8,loc='lower left');ax[0].text(.02,.97,'Negative favors the wrong sequence',transform=ax[0].transAxes,va='top',fontsize=9)
    ax[1].plot(x,[r['raw_final_duration'] for r in actor],'o-',color='#3b6c9c',label='Whole-cycle mean')
    ax[1].plot(x,[r['normalized_final_duration'] for r in actor],'s-',color='#de8d36',label='Exposure-normalized')
    ax[1].plot(x,[r['oracle_final_duration'] for r in actor],'D',color='#333333',label='Waveform oracle')
    ax[1].axhline(1,color='black',lw=.7,ls='--');ax[1].set(xticks=x,xticklabels=labels,ylim=(.65,1.25),ylabel='Selected duration / tutor duration',title='B  Readout changes the duration bias')
    ax[1].legend(fontsize=8,loc='upper right');ax[1].text(.02,.04,'25 actor queries; frozen no-clock critics',transform=ax[1].transAxes,fontsize=8)
    ax[2].bar(x,[1000*r['normalized_chosen_minus_target_Hz'] for r in actor],color='#b8514b',width=.55)
    ax[2].axhline(0,color='black',lw=.8);ax[2].set(xticks=x,xticklabels=labels,ylabel='Chosen − target normalized cost (mHz)',title='C  Normalization is not full correction')
    ax[2].text(.02,.97,'All selected wrong durations score lower',transform=ax[2].transAxes,va='top',fontsize=9)
    for a in ax:a.set_xlabel('Consumed synthetic plant')
    fig.suptitle('Temporal reward fidelity: three consumed cases, fixed synapses',fontsize=14)
    fig.savefig(HERE/'INDEPENDENT_RESULT.png',dpi=180)
    fig.savefig(HERE/'INDEPENDENT_RESULT.svg')

if __name__=='__main__':main()

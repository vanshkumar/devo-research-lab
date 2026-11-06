"""Bounded source-law audit; ONE permitted development-only observation calibration."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import sys
sys.dont_write_bytecode=True
import hashlib, io, json, resource, time
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.stats import beta

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CAMP=ROOT/'campaigns/human_learning_routes_2026-10-28'

def main():
    start=time.monotonic(); pins=[]
    def read(p,charge=3):
        b=p.read_bytes(); pins.append(dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),charge=charge*len(b)))
        return b
    builder=ET.fromstring(read(ROOT/'sources/human_learning_feasibility_2026-10-28/WIN_cursor_ibl.psyexp'))
    loops=[]; relevant=[]
    for e in builder.iter():
        if e.tag=='LoopInitiator':
            loops.append(dict(e.attrib,params=[p.attrib for p in e if p.tag=='Param']))
        if e.tag=='Param' and ('pregen' in e.attrib.get('val','') or 'filename' in e.attrib.get('val','')):
            relevant.append(e.attrib)
    lock=json.loads(read(CAMP/'protocol/FINAL_FREEZE.json'))
    verified={}
    for name in ('experiments/model.py','protocol/FINAL_PROTOCOL.md','protocol/split_manifest.csv'):
        verified[name]=hashlib.sha256(read(CAMP/name)).hexdigest()==lock['sha256'][name]
    assert all(verified.values())
    manifests=json.loads(read(CAMP/'experiments/source_audit/sources/manifest.json'))
    manifest={x['file']:x for x in manifests}
    schedules=[]
    for i in range(10):
        name=f'pregen_sequence_{i}.xlsx'; b=read(CAMP/'experiments/source_audit/sources'/name,20)
        assert hashlib.sha256(b).hexdigest()==manifest[name]['sha256']
        x=pd.read_excel(io.BytesIO(b),nrows=600)
        side=np.where(x.eccentricity.to_numpy()<0,1,-1)
        schedules.append(dict(side=side,contrast=side*np.round(x.contrastDelta.to_numpy()/.2,2),bias=x.bias.to_numpy()))
    split=pd.read_csv(io.BytesIO(read(CAMP/'protocol/split_manifest.csv')),dtype={'subject':str})
    dev=pd.read_csv(io.BytesIO(read(CAMP/'inputs/development_numeric.csv')),dtype={'subject':str,'session':str})
    val=pd.read_csv(io.BytesIO(read(CAMP/'inputs/validation_numeric.csv')),dtype={'subject':str,'session':str})
    assert set(dev.subject)==set(split.loc[split.partition=='development','subject'])
    assert set(val.subject)==set(split.loc[split.partition!='development','subject'])
    calibration=[]
    for condition,a in dev.loc[dev.trial.ge(200)].groupby('instructions'):
        n=len(a); omitted=int(a.choice.eq(0).sum()); aa=omitted+.5; bb=n-omitted+.5
        calibration.append(dict(condition=int(condition),source_people=int(a.subject.nunique()),n=n,omissions=omitted,alpha=aa,beta=bb,mean=aa/(aa+bb),q025=float(beta.ppf(.025,aa,bb)),q975=float(beta.ppf(.975,aa,bb))))
    people=[]; checks=[]
    for sid,s in val.groupby('subject',sort=True):
        s=s.sort_values('trial'); early=s.loc[s.trial.lt(200)]; assert len(early)==200
        visible=early.sideContrast.to_numpy(); choice=early.choice.to_numpy(); fb=early.feedbackType.to_numpy()
        responding=np.isin(choice,(-1,1)); revealed=np.where(responding,choice*fb,0.)
        # Match only participant-visible inputs and actually revealed PREFIX side.
        matches=[i for i,x in enumerate(schedules) if np.allclose(visible,x['contrast'][:200],atol=1e-12,rtol=0.) and np.array_equal(revealed[responding],x['side'][:200][responding])]
        assert len(matches)==1,(sid,matches)
        seq=matches[0]; x=schedules[seq]
        assert np.array_equal(s.stimSide.to_numpy(),x['side'])
        assert np.allclose(s.sideContrast.to_numpy(),x['contrast'],atol=1e-12,rtol=0.)
        part=split.loc[split.subject==sid,'partition'].iloc[0]
        people.append(dict(subject=sid,condition=int(s.instructions.iloc[0]),partition=part,source_sequence=seq,
                           prefix_choice=choice.astype(int).tolist(),prefix_feedback=np.where(responding,fb,0.).astype(int).tolist(),
                           side_contrast=x['contrast'].tolist(),teacher_side=x['side'].tolist(),teacher_bias=x['bias'].tolist()))
        checks.append(dict(subject=sid,sequence=seq,early_visible_and_revealed_prefix_unique=True,all600_source_inputs_match=True))
    forecast_inputs=dict(people=people,observation_calibration=calibration,
        omission_law='One condition-specific constant omission probability; independent of scheduled side, choice and past. Jeffreys Beta(.5,.5) calibrated only on original development trials201-600. Main integrates its posterior predictive law; this is an observation assumption, not biological certification.',
        teacher_law='Known deterministic source XLSX continuation selected uniquely by first200 visible inputs/revealed sides. Future realized targets ARE known to the environment and forecaster through this exact lookup. No independent Bernoulli target law is asserted.',
        prefix_convention='Actual observed trials1-200 only; omitted feedback coded0. Later actual choices/feedback/omissions absent from this forecast input file.')
    (HERE/'FORECAST_INPUTS.json').write_text(json.dumps(forecast_inputs,indent=2)+'\n')
    result=dict(utc=datetime.now(timezone.utc).isoformat(),decision='CONTINUE_ONE_NARROW_FORWARD_COMPARISON',
        justification='The saved campaign tests conditional predictions/recovery of different synthetic populations, not marginal future choices from its fixed primary fits and original first200 calibration. It remains numerically possible that strong persistence beats shared history after integrating generated later behavior. The operational test is limited to a fully known deterministic teacher; it cannot establish generated-teacher transport, closed-loop feedback causality or complete the scientific goal.',
        pre_main_revision_used=1,revision='PI-authorized sole source-only omission-law calibration; all learning weights/random-effect prediction kernels stay fixed.',
        file_checks=verified,source_loops=loops,source_selection_fragments=relevant,checks=checks,observation_calibration=calibration,pins=pins,
        explicit_read_hash_decode_charge=sum(x['charge'] for x in pins),wall_seconds=time.monotonic()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_future_response_scores_computed=False,learning_fits=0,original134MB_csv_opened=False,public_operations=0,physical_io='unknown',runtime_host_peak='unknown')
    (HERE/'FEASIBILITY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('utc','decision','source_loops','source_selection_fragments','observation_calibration','explicit_read_hash_decode_charge','wall_seconds','peak_rss_bytes')},indent=2))

if __name__=='__main__': main()

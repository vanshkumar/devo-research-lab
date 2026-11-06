"""Post-freeze numerical audit only; source prefixes, no actual future data."""
from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent
C=HERE.parents[2]
sys.path.insert(0,str(C/'code'))
import production_replay as r

def main():
    source_manifest=C/'protocols/SOURCE_FORECASTS.json'
    source=json.loads(source_manifest.read_text())
    assert source['all_forecasts_saved_before_scored_outcomes']
    mp=C/'protocols/SOURCE_POLICY_SWAP_FORECASTS.json'
    manifest=json.loads(mp.read_text())
    # Match the already frozen replay selection, rather than outcome selection.
    selection=json.loads((HERE/'SOURCE_RESULT.json').read_text())['subjects']
    model=r.load_rnn(r.MODEL);bank=r.load_bank(r.BANK);records=[]
    for subject in selection:
        folder=C/'artifacts/forecasts/source'
        meta=json.loads((folder/(subject+'__rnn.json')).read_text())
        path=folder/(subject+'__prefix.npz')
        assert r.digest(path)==meta['prefix_sha256']
        r.log(dict(event='independent_fixed_swap_replay_saved_source_prefix',subject=subject,
                   prefix_sha256=r.digest(path),swap_manifest_sha256=r.digest(mp),actual_future_outcomes_accessed=False))
        with np.load(path,allow_pickle=False) as z:
            prefix={k:z[k] for k in z.files if k!='future_session_start'};starts=z['future_session_start']
        n=meta['particles']
        with np.load(folder/(subject+'__rnn.npz'),allow_pickle=False) as z:seed=int(z['seed'])
        state,calibration=r.prefix_uncertainty(model,prefix,meta,n,seed)
        common=r.draw_initial(prefix,bank,n,seed+211,exclude=subject,competence='growth')
        w,cov,_=r.fit_competence(prefix,ridge=.5)
        persistence=np.random.default_rng(seed+313).multivariate_normal(w,cov,size=n)
        row=dict(subject=subject,particles=n,seed=seed,models={})
        for record in [v for v in manifest['records'] if v['subject']==subject]:
            kind=record['model'];path=r.ROOT/record['path'];assert r.digest(path)==record['sha256']
            rebuilt=r.replay(model,prefix,starts,common,state,persistence,kind,'external',seed)
            with np.load(path,allow_pickle=False) as z:
                errors={k:float(np.max(np.abs(z[k]-v))) for k,v in rebuilt.items()}
            assert errors['samples']==0 and errors['counts']==0 and max(errors.values())<1e-8,(subject,kind,errors)
            row['models'][kind]=dict(forecast_sha256=r.digest(path),errors=errors)
            np.savez_compressed(HERE/('fixed_swap__'+subject+'__'+kind+'.npz'),**rebuilt)
        records.append(row);print(json.dumps(row),flush=True)
    result=dict(passed=True,scope='Independent fixed sampler and recurrent simulation; no real future outcomes',
                subjects=selection,records=records,manifest_sha256=r.digest(mp),code_sha256=r.digest(__file__))
    (HERE/'FIXED_SWAP_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()

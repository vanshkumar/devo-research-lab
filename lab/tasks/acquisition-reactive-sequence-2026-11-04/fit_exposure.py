"""Compare recorded historical actor fitting exposure to this development roster."""
from collections import Counter

from source import HERE, OLD, POP, REV, BYTES, META_PINS, check, get, save, utc


def main():
    p = get(POP/'protocols/FREEZE.json','625535ac5c20fe7301b7dcdec22549fd0a708271cc51dd79df8dee6f5c37a64c')
    pins = {x['path']:x['sha256'] for x in p['files']}
    p = OLD/'protocols/RNN_FREEZE.json'
    rnn = get(p,pins[str(p.relative_to(HERE.parents[2]))])
    pins_rnn = {x['path']:x['sha256'] for x in rnn['files']}
    info = get(OLD/'artifacts/rnn/RNN_SELECTION.json',pins_rnn['artifacts/rnn/RNN_SELECTION.json'])
    alloc = get(OLD/'artifacts/rnn/main_ALLOCATION.json')
    dev = get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json')
    split = get(OLD/'protocols/SPLIT.json',pins[str((OLD/'protocols/SPLIT.json').relative_to(HERE.parents[2]))])
    labs = {x['subject']:x['lab'] for x in split['standard']}
    check(alloc['train']==dev['train'] and alloc['validation']==dev['validation'] and
          len(alloc['train'])==info['train_animals']==62 and len(alloc['validation'])==info['development_cv_animals']==12,
          'Original GRU allocation/selection inconsistent')
    fit = get(REV/'artifacts/transition_fit/FIT_DISPOSITION.json')
    check([x['subject'] for x in fit['records']]==alloc['train'],'Session rho allocation mismatch')
    used = [x['subject'] for x in fit['records'] if x['eligible_full_horizon']]
    check(len(used)==fit['eligible']==46,'Session rho scoring count')
    m = get(HERE/'SOURCE_MANIFEST.json')
    # Unique original episode and object identifiers, not fuzzy matching labels.
    eids = [x['eid'] for x in m['sessions']]
    assets = [a['dataset_id'] for x in m['sessions'] for a in x['assets'].values()]
    check(len(set(eids))==len(eids) and len(set(assets))==len(assets),'Duplicate source objects')
    strata = {}
    cal = get(HERE/'CALIBRATION.json')
    track = get(HERE/'TRACK_CALIBRATION.json')
    for lo,hi,name in [(0,40,'historical40'),(40,64,'later24')]:
        ids = m['subjects'][lo:hi]
        src_labs = m['labs'][lo:hi]
        exposure = {}
        for k,roster in [('actor_optimizer',alloc['train']),('actor_checkpoint_allocated',alloc['validation']),('session_rho_scored',used)]:
            seen = set(labs[s] for s in roster)
            overlap = sorted(set(src_labs)&seen)
            exposure[k] = dict(fit_n=len(roster),fit_lab_counts=dict(Counter(labs[s] for s in roster)),
                               common_animals=sorted(set(ids)&set(roster)), common_sites=overlap,
                               n_development_animals_in_common_sites=sum(l in seen for l in src_labs))
        strata[name] = dict(exposure=exposure,sites=dict(Counter(src_labs)),
            animal_mean_log_loss={k:sum(cal['per_animal'][s][k]['log_loss'] for s in ids)/len(ids)
                                  for k in cal['summary']},
            animal_mean_track_loss=sum(track['score'][s]['log_loss'] for s in ids)/len(ids))
    save('FIT_EXPOSURE.json',dict(utc=utc(),strata=strata,source_episode_count=len(eids),asset_count=len(assets),
         original_cv_actually_evaluated=info['evaluated_cv_animals'],actor_checkpoint=info['best']['epoch'],
         note='Session rho shares original GRU weights; these fits were not rotated with our site folds. No current recurrent fit.',
         bytes=dict(BYTES),metadata_sha256=META_PINS))


if __name__=='__main__':
    main()

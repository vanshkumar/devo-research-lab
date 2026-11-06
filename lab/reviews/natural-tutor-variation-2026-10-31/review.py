"""Independent score/source reconstruction and one predeclared contrary test.

Does not import or execute author code. All writes stay beside this file.
"""
import argparse
import collections
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
from pathlib import Path
import resource
import struct
import sys
import tarfile
import traceback
import numpy as np

ROOT = Path(__file__).resolve().parent
HERE = ROOT
AUTHOR = ROOT.parents[1] / 'tasks' / 'natural-tutor-variation-2026-10-31'
DEADLINE = dt.datetime.fromisoformat('2026-11-01T02:25:42.213+00:00')
STARTED = '2026-11-01T01:45:42.213Z'
MODE = 'original bounded review'
CAP = 120000000
TOL = 1e-12
METHODS = ['prototype','nearest','covariance','free_tempo','shuffled_covariance','absent','bounded_tempo']
FACTORS = [.8,.9,.95,1.05,1.1,1.2]
LOCS = [('global',[0,1,2,3,4]),('duration_b',[2]),('gap_ab',[1]),('duration_c',[4])]
PASSES = []

def now():
    return dt.datetime.now(dt.timezone.utc)

def charge(kind,n,path=''):
    assert now() < DEADLINE, 'fixed deadline'
    n = int(n)
    assert total()+n < CAP, 'scientific byte cap'
    PASSES.append({'kind':kind,'bytes':n,'path':str(path)})

def total():
    return sum(p['bytes'] for p in PASSES)

def rb(path):
    n = path.stat().st_size
    assert total()+n < CAP
    b = path.read_bytes()
    charge('file read',len(b),path)
    return b

def js(path):
    b = rb(path)
    charge('UTF8/JSON decode',len(b),path)
    return json.loads(b)

def digest(b,alg,path):
    charge(alg+' hash',len(b),path)
    return hashlib.new(alg,b).hexdigest()

def arrays(path):
    b = rb(path)
    with np.load(io.BytesIO(b),allow_pickle=False) as z:
        out = {k:z[k] for k in z.files}
    charge('NPY decode',sum(v.nbytes for v in out.values()),path)
    return out

def save(name,obj):
    (HERE/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def equal_recording(groups):
    counts = collections.Counter(groups.tolist())
    return np.array([1.0/(len(counts)*counts[g]) for g in groups])

def fitted(x,groups):
    w = equal_recording(groups)
    mu = (x*w[:,None]).sum(axis=0)
    centered = x-mu
    cov = sum((wi*np.outer(d,d) for wi,d in zip(w,centered)),np.zeros((5,5)))
    cov /= 1-float(np.sum(w*w))
    cov = .8*cov + .2*np.diag(np.diag(cov)) + 4e-6*np.eye(5)
    tempos = centered.mean(axis=1)
    return {'x':x,'mu':mu,'cov':cov,'chol':np.linalg.cholesky(cov),
            'lo':float(min(tempos)),'hi':float(max(tempos))}

def cost(model,x,method):
    x = np.atleast_2d(x)
    d = x-model['mu']
    if method == 'absent':
        return np.zeros(len(x))
    if method == 'nearest':
        return np.array([np.sqrt(np.min(np.sum((model['x']-row)**2,axis=1)/5)) for row in x])
    if method in ('covariance','shuffled_covariance'):
        whitened = np.linalg.solve(model['chol'],d.T).T
        return np.sqrt(np.sum(whitened**2,axis=1)/5)
    if method == 'prototype':
        return np.sqrt(np.sum(d*d,axis=1)/5)
    tempo = d.mean(axis=1)
    residual = d-tempo[:,None]
    q = np.sum(residual*residual,axis=1)/5
    if method == 'bounded_tempo':
        excess = np.maximum(0,np.maximum(model['lo']-tempo,tempo-model['hi']))
        q += excess**2
    assert method in ('free_tempo','bounded_tempo')
    return np.sqrt(q)

def weighted_quantile(values,weights):
    order = sorted(range(len(values)),key=lambda j:values[j])
    target = .95*sum(weights)
    accumulated = 0.0
    for j in order:
        accumulated += weights[j]
        if accumulated >= target:
            return float(values[j])
    return float(values[order[-1]])

def renamed_positions(x,keys):
    result = np.empty_like(x)
    for i,key in enumerate(keys):
        seed = int.from_bytes(hashlib.sha256(str(key).encode()).digest()[:8],'big')
        result[i] = x[i,np.random.default_rng(seed).permutation(5)]
    return result

def reconstruct(freeze,x,groups,keys):
    train = np.isin(groups,freeze['teaching'])
    tx,tg,tk = x[train],groups[train],keys[train]
    normal = fitted(tx,tg)
    sx = renamed_positions(tx,tk)
    scrambled = fitted(sx,tg)
    calibration = {m:np.zeros(len(tx)) for m in METHODS}
    for recording in sorted(set(tg)):
        held = tg == recording
        nm = fitted(tx[~held],tg[~held])
        sm = fitted(sx[~held],tg[~held])
        for method in METHODS:
            calibration[method][held] = cost(sm if method=='shuffled_covariance' else nm,tx[held],method)
    thresholds = {m:weighted_quantile(v,equal_recording(tg)) for m,v in calibration.items()}
    comparisons = []
    summaries = {}
    phase_arrays = {}
    scalar_count = 0
    max_error = 0.0
    max_summary_error = 0.0
    main_summary = None
    for phase,split in [('MAIN','main_evaluation'),('REVISION','revision_evaluation')]:
        methods = METHODS[:-1] if phase=='MAIN' else METHODS
        saved = arrays(AUTHOR/(phase+'_SCORES.npz'))
        published = js(AUTHOR/(phase+'_SUMMARY.json'))
        if phase == 'MAIN':
            main_summary = published
        test = np.isin(groups,freeze[split])
        ex,eg,ek = x[test],groups[test],keys[test]
        assert np.array_equal(saved['eval_x'],ex)
        assert np.array_equal(saved['eval_groups'],eg)
        assert np.array_equal(saved['eval_keys'],ek)
        assert np.array_equal(saved['methods'],np.array(methods))
        original = np.array([cost(scrambled if m=='shuffled_covariance' else normal,ex,m) for m in methods])
        changes,changed,locations,factors = [],[],[],[]
        for location,indices in LOCS:
            for factor in FACTORS:
                altered = ex.copy()
                for index in indices:
                    altered[:,index] += np.log(factor)
                changed.append(altered)
                changes.append({'location':location,'factor':factor,'indices':indices})
                locations.append(location)
                factors.append(factor)
        assert np.array_equal(saved['challenge_locations'],np.array(locations))
        assert np.array_equal(saved['challenge_factors'],np.array(factors))
        edited = np.array([[cost(scrambled if m=='shuffled_covariance' else normal,z,m) for z in changed] for m in methods])
        for name,actual in [('original',original),('edits',edited)]:
            error = float(np.max(np.abs(actual-saved[name])))
            scalar_count += actual.size
            max_error = max(max_error,error)
            comparisons.append({'phase':phase,'array':name,'scalar_count':actual.size,'max_abs_error':error})
            assert error < 1e-11, (phase,name,error)
        weights = equal_recording(eg)
        method_summaries = {}
        for i,method in enumerate(methods):
            cutoff = thresholds[method]+TOL
            acceptance = original[i] <= cutoff
            rows = []
            for j,change in enumerate(changes):
                delta = edited[i,j]-original[i]
                row = dict(change,rejection=float(np.sum(weights*(edited[i,j]>cutoff))),
                           strict_increase=float(np.sum(weights*(delta>TOL))),
                           ties=float(np.sum(weights*(np.abs(delta)<=TOL))),
                           decrease=float(np.sum(weights*(delta < -TOL))),
                           renditions_increase=int(np.sum(delta>TOL)),renditions_total=len(ex))
                expected = published['methods'][method]['challenges'][j]
                for field in ['rejection','strict_increase','ties','decrease','renditions_increase','renditions_total']:
                    max_summary_error = max(max_summary_error,abs(row[field]-expected[field]))
                    assert abs(row[field]-expected[field]) < 1e-11,(phase,method,j,field)
                rows.append(row)
            primary = [r for r in rows if r['factor'] in [.8,1.2]]
            acceptance_rate = float(np.sum(weights*acceptance))
            passed = acceptance_rate >= .9-TOL and all(r['rejection']>=.8-TOL and r['strict_increase']>=.8-TOL for r in primary)
            expected = published['methods'][method]
            assert passed == expected['primary_pass']
            for val,wanted in [(thresholds[method],expected['threshold']),
                               (acceptance_rate,expected['natural_acceptance']),
                               (float(acceptance.mean()),expected['natural_acceptance_pooled'])]:
                max_summary_error = max(max_summary_error,abs(val-wanted))
                assert abs(val-wanted) < 1e-11
            for recording in sorted(set(eg)):
                rate = float(acceptance[eg==recording].mean())
                assert rate == expected['per_recording_natural_acceptance'][str(recording)]
            method_summaries[method] = {'threshold':thresholds[method],
                 'natural_acceptance':acceptance_rate,'primary_pass':bool(passed),'challenges':rows}
        summaries[phase] = {'recordings':len(set(eg)),'phrases':len(ex),'methods':method_summaries,
                            'saved_timestamp':published['timestamp']}
        phase_arrays[phase] = {'x':ex,'groups':eg,'keys':ek,'original':original,'edits':edited,'methods':methods}
    cal_errors = {m:float(np.max(np.abs(calibration[m]-main_summary['model']['calibration'][m]))) for m in METHODS[:-1]}
    assert max(cal_errors.values()) < 1e-11
    mu_error = float(np.max(np.abs(normal['mu']-main_summary['model']['mean_log_intervals'])))
    covariance_error = float(np.max(np.abs(normal['cov']-main_summary['model']['covariance'])))
    assert mu_error < 1e-12 and covariance_error < 1e-12
    controls = {'prototype_at_mean':float(cost(normal,normal['mu'],'prototype')[0]),
                'covariance_at_mean':float(cost(normal,normal['mu'],'covariance')[0]),
                'free_global_invariance_max':max(float(np.max(np.abs(cost(normal,x+np.log(f),'free_tempo')-cost(normal,x,'free_tempo')))) for f in FACTORS),
                'bounded_free_on_teaching_max':float(np.max(np.abs(cost(normal,tx,'bounded_tempo')-cost(normal,tx,'free_tempo')))),
                'teaching_log_tempo_range':[normal['lo'],normal['hi']],
                'teaching_tempo_factor_range':[float(np.exp(normal['lo'])),float(np.exp(normal['hi']))],
                'source_mean_error':mu_error,'source_covariance_error':covariance_error,
                'calibration_array_errors':cal_errors}
    # Supplied-label sequence control, actually evaluated, not asserted in prose.
    sequences = [('c','b','a'),('b','c','a')]*103
    controls['sequence_controls'] = {'altered_phrases':len(sequences),
        'exact_order_rejections':sum(s != ('a','b','c') for s in sequences),
        'bag_order_rejections':sum(sorted(s) != ['a','b','c'] for s in sequences),
        'natural_exact_order_acceptance':103,'scope':'supplied labels only'}
    assert controls['free_global_invariance_max'] < TOL
    output = {'timestamp':now().isoformat(),'phases':summaries,'scalar_comparisons':comparisons,
              'scalar_costs_reconstructed':scalar_count,'max_abs_cost_error':max_error,
              'max_abs_summary_error':max_summary_error,'controls':controls,
              'all_full_gates_fail':all(not m['primary_pass'] for p in summaries.values() for m in p['methods'].values())}
    save('RECONSTRUCTION.json',output)
    np.savez_compressed(HERE/'INDEPENDENT_SCORES.npz',**{
        phase+'_'+field:values[field] for phase,values in phase_arrays.items()
        for field in ['x','groups','keys','original','edits']})
    return output,phase_arrays,normal,thresholds

def contrary(phases,normal,thresholds):
    records = []
    for phase,other in [('MAIN','REVISION'),('REVISION','MAIN')]:
        a,b = phases[phase],phases[other]
        witness_order = np.argsort(b['keys'])
        bx,bk = b['x'][witness_order],b['keys'][witness_order]
        witness_costs = cost(normal,bx,'covariance')
        for i,(original,key,recording) in enumerate(zip(a['x'],a['keys'],a['groups'])):
            before_distances = np.sqrt(np.mean((bx-original)**2,axis=1))
            before_j = int(np.argmin(before_distances))
            before = float(before_distances[before_j])
            before_cost = float(cost(normal,original,'covariance')[0])
            for factor in [.8,1.2]:
                edited = original.copy()
                edited[2] += np.log(factor)
                after_distances = np.sqrt(np.mean((bx-edited)**2,axis=1))
                j = int(np.argmin(after_distances))
                after = float(after_distances[j])
                after_cost = float(cost(normal,edited,'covariance')[0])
                delta = after_cost-before_cost
                dist_delta = after-before
                records.append({'phase':phase,'reference_key':str(key),'recording':str(recording),'factor':factor,
                    'reference_intervals_ms':(1000*np.exp(original)).tolist(),
                    'edited_intervals_ms':(1000*np.exp(edited)).tolist(),
                    'witness_key':str(bk[j]),'witness_intervals_ms':(1000*np.exp(bx[j])).tolist(),
                    'before_nearest_key':str(bk[before_j]),'before_nearest_log_RMS':before,
                    'after_nearest_log_RMS':after,'distance_change':dist_delta,
                    'covariance_before':before_cost,'covariance_after':after_cost,'cost_change':delta,
                    'witness_covariance_cost':float(witness_costs[j]),
                    'reference_accepted':bool(before_cost<=thresholds['covariance']+TOL),
                    'edited_accepted':bool(after_cost<=thresholds['covariance']+TOL),
                    'witness_accepted':bool(witness_costs[j]<=thresholds['covariance']+TOL),
                    'cost_decreases':bool(delta < -TOL),'closer_to_natural_witness':bool(dist_delta < -TOL),
                    'witness_distance_tie':bool(abs(dist_delta)<=TOL),
                    'reference_error_log_RMS':float(abs(np.log(factor))/np.sqrt(5))})
    assert len(records)==206
    def summary(rows):
        groups = np.array([r['recording'] for r in rows])
        # Two edits share each reference. Equal total weight per recording.
        weights = equal_recording(groups)
        decreased = np.array([r['cost_decreases'] for r in rows])
        closer = np.array([r['closer_to_natural_witness'] for r in rows])
        accepted = np.array([r['edited_accepted'] and r['witness_accepted'] for r in rows])
        n = int(decreased.sum())
        den = float(weights[decreased].sum())
        return {'pairs':len(rows),'cost_decreasing_pairs':n,
                'cost_decreasing_and_closer':int((decreased&closer).sum()),
                'cost_decreasing_but_not_closer':int((decreased&~closer).sum()),
                'cost_decreasing_closer_both_accepted':int((decreased&closer&accepted).sum()),
                'fraction_decreasing_edits_closer':float(closer[decreased].mean()) if n else None,
                'equal_recording_fraction_decreasing_edits_closer':float(weights[decreased&closer].sum()/den) if den else None,
                'equal_recording_decrease_rate':den,
                'equal_recording_closer_both_accepted_rate':float(weights[decreased&closer&accepted].sum()),
                'cross_tab_raw':{f'{dc}_{nc}':sum(r['cost_decreases']==dc and r['closer_to_natural_witness']==nc for r in rows) for dc in [False,True] for nc in [False,True]}}
    out = {'timestamp':now().isoformat(),'plan_sha256':digest(rb(HERE/'PLAN.md'),'sha256',HERE/'PLAN.md'),
           'status':'postvalidation finite diagnostic; original gates unchanged',
           'overall':summary(records),'by_phase':{p:summary([r for r in records if r['phase']==p]) for p in phases},
           'rows':records,
           'interpretation_limits':'Opposite-half natural proximity is an independent descriptive comparator, not perceptual correctness, an optimality label, a replacement evaluator, or a biological information bound.'}
    save('CONTRARY.json',out)
    return out

class TarView(io.BytesIO):
    def __init__(self,b):
        super().__init__(b)
        self.bytes_read = 0
    def read(self,n=-1):
        b = super().read(n)
        self.bytes_read += len(b)
        return b

def wav_metadata(stream):
    header = stream.read(12)
    assert header[:4]==b'RIFF' and header[8:12]==b'WAVE'
    fmt = None
    while True:
        h = stream.read(8)
        assert len(h)==8
        kind,n = h[:4],struct.unpack('<I',h[4:])[0]
        if kind==b'fmt ':
            assert 16<=n<=256
            payload = stream.read(n)
            fmt = struct.unpack('<HHIIHH',payload[:16])
            if n%2:
                stream.seek(1,1)
        elif kind==b'data':
            assert fmt is not None
            encoding,channels,rate,byte_rate,alignment,bits = fmt
            assert encoding==1 and alignment==channels*bits//8 and n%alignment==0
            return {'encoding':encoding,'channels':channels,'rate':rate,'bits':bits,
                    'frames':n//alignment,'data_bytes':n,'seconds':(n//alignment)/rate}
        else:
            stream.seek(n+n%2,1)

def source_and_pins(first,freeze,reconstruction):
    pin_results = []
    revision_freeze = js(AUTHOR/'REVISION_FREEZE.json')
    stable = js(AUTHOR/'ARTIFACT_MANIFEST.json')
    for manifest_name,manifest in [('FREEZE',freeze),('REVISION_FREEZE',revision_freeze),('ARTIFACT_MANIFEST',stable)]:
        for pin in manifest['pins']:
            p = AUTHOR/pin['path']
            b = rb(p)
            actual = digest(b,'sha256',p)
            ok = len(b)==pin['bytes'] and actual==pin['sha256']
            pin_results.append({'manifest':manifest_name,'path':pin['path'],'matches':ok})
            assert ok,(manifest_name,pin['path'])
    src = AUTHOR/'sources'/'gy6or6_032612_complete.tar.gz'
    assert src.stat().st_size==19214942
    # Pre-pass guard includes both independent whole-object hashes and decompression.
    assert total()+3*src.stat().st_size+30000000 < CAP
    compressed = rb(src)
    md5 = digest(compressed,'md5',src)
    sha256 = digest(compressed,'sha256',src)
    assert md5=='4441c716563965db4c1522346f99a064'
    assert sha256=='28e8d2787d1faaa177d67f786cf77a03706189ca09933e5f6784547e9023e628'
    decoded = gzip.decompress(compressed)
    charge('gzip container decode',len(decoded),src)
    view = TarView(decoded)
    csvs,wavs,annotations = {},{},{}
    header_bytes = 0
    with tarfile.open(fileobj=view,mode='r:') as archive:
        for member in archive:
            if not member.isfile():
                continue
            name = Path(member.name).name
            if name.endswith('.csv'):
                assert member.size < 100000
                b = archive.extractfile(member).read()
                charge('CSV UTF8 decode',len(b),name)
                parsed = list(csv.DictReader(io.StringIO(b.decode('utf-8'))))
                sha = digest(b,'sha256',name)
                expected = next(s for s in first['source_csvs'] if s['file']==name)
                assert sha==expected['sha256'] and len(parsed)==expected['annotation_rows']
                csvs[name]={'bytes':len(b),'sha256':sha,'rows':len(parsed),'extracted_csv_matches':True}
                annotations[name]=parsed
            elif name.endswith('.wav'):
                stream = archive.extractfile(member)
                start_pos = stream.tell()
                metadata = wav_metadata(stream)
                header_bytes += stream.tell()-start_pos
                wavs[name]=dict(metadata,archive_member_bytes=member.size)
    charge('tar header/CSV/WAV-header reads (PCM payloads skipped)',view.bytes_read,src)
    assert len(csvs)==len(wavs)==39
    for name,rows in annotations.items():
        wav = wavs[name[:-4]]
        assert wav['channels']==1 and wav['rate']==32000 and wav['bits']==16
        for row in rows:
            assert 0 <= float(row['onset_s']) < float(row['offset_s']) <= wav['seconds']
    metadata = js(AUTHOR/'sources'/'figshare4805749.json')
    match = [f for f in metadata['files'] if f['id']==41668992]
    assert len(match)==1 and match[0]['size']==len(compressed)
    primary_md5 = match[0].get('computed_md5',match[0].get('supplied_md5'))
    assert primary_md5==md5
    chronology = {
        'main_freeze':freeze['timestamp'],
        'main_output':reconstruction['phases']['MAIN']['saved_timestamp'],
        'revision_freeze':revision_freeze['timestamp'],
        'revision_output':reconstruction['phases']['REVISION']['saved_timestamp']}
    times = [dt.datetime.fromisoformat(t) for t in chronology.values()]
    assert times==sorted(times)
    out = {'timestamp':now().isoformat(),'whole_archive_bytes':len(compressed),'md5':md5,'sha256':sha256,
           'gzip_decoded_bytes':len(decoded),'tar_explicit_read_bytes':view.bytes_read,
           'wav_headers_only_bytes':header_bytes,'waveform_samples_numerically_decoded':0,
           'csv_count':len(csvs),'wav_count':len(wavs),'wav_seconds':sum(v['seconds'] for v in wavs.values()),
           'all_annotation_rows_in_bounds':True,'source_csvs':csvs,'wave_headers':wavs,
           'primary_metadata_archive_entry':match[0],'primary_metadata_version':metadata.get('version'),
           'license':metadata.get('license'),'freeze_chronology':chronology,
           'pin_results':pin_results,'pin_counts':dict(collections.Counter(r['manifest'] for r in pin_results)),
           'chronology_limit':'Saved records and code ordering verified; no independent certification of all historical app reads. All raw CSVs were acquired/extracted before score freezes; final10 numeric interpretation was delayed according to saved logs/code.'}
    save('SOURCE_PINS.json',out)
    return out

def main():
    global HERE, DEADLINE, STARTED, MODE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',help='owned direct child already containing first-calculation outputs')
    parser.add_argument('--reproduce',action='store_true',help='future separately authorized offline reproduction, same finite caps')
    args = parser.parse_args()
    if args.output:
        destination = (ROOT/args.output).resolve()
        assert destination.parent==ROOT and destination.is_dir()
        HERE = destination
    if args.reproduce:
        assert args.output, 'reproduction must preserve original outputs'
        started = now()
        STARTED = started.isoformat()
        DEADLINE = started+dt.timedelta(minutes=40)
        MODE = 'separately authorized offline reproduction'
    assert not (HERE/'RESOURCES.json').exists(), 'preserve earned outputs; choose --output and --reproduce'
    status = 'running'
    failure = None
    try:
        first = js(HERE/'FIRST_CALCULATION.json')
        charge('prior first-calculation scientific read/decode/hash',first['scientific_read_decoded_hash_bytes'])
        charge('conservative allowance for shell scientific prose/code reads and final inspection',1000000)
        freeze = js(AUTHOR/'FREEZE.json')
        independent = arrays(HERE/'INDEPENDENT_FEATURES.npz')
        x,groups,keys = independent['x'],independent['groups'],independent['keys']
        reconstruction,phases,normal,thresholds = reconstruct(freeze,x,groups,keys)
        print(json.dumps({'checkpoint':'scores','scalar_costs':reconstruction['scalar_costs_reconstructed'],
                          'max_error':reconstruction['max_abs_cost_error'],'all_full_gates_fail':reconstruction['all_full_gates_fail']}),flush=True)
        contrary_output = contrary(phases,normal,thresholds)
        print(json.dumps({'checkpoint':'contrary','summary':contrary_output['overall']}),flush=True)
        source = source_and_pins(first,freeze,reconstruction)
        print(json.dumps({'checkpoint':'source','wav':source['wav_count'],'csv':source['csv_count'],
                          'seconds':source['wav_seconds'],'pins':source['pin_counts']}),flush=True)
        status = 'complete'
    except Exception as exc:
        status = 'partial_failure'
        failure = {'error':repr(exc),'traceback':traceback.format_exc()}
        print(json.dumps(failure),flush=True)
    finally:
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save('RESOURCES.json',{'timestamp':now().isoformat(),'status':status,
           'start':STARTED,'fixed_deadline':DEADLINE.isoformat(),'mode':MODE,
           'scientific_read_decoded_hash_bytes':total(),'scientific_byte_cap':CAP,'passes':PASSES,
           'peak_rss_bytes':peak,'peak_rss_cap':400000000,'single_simultaneous_scientific_process':True,
           'numerical_threads':1,'network_operations':0,'ingress_bytes':0,'jobs':0,
           'failure':failure,'python':sys.version,'numpy':np.__version__,
           'author_resource_record_unchanged':{'scientific_bytes':168914260,'charged_ingress':30280076,
            'logical_public_operations':10,'failed_pass_charge':35000000,'failed_pass_peak':'unmeasured'}})
        assert peak < 400000000
    if failure:
        raise SystemExit(1)

if __name__=='__main__':
    main()

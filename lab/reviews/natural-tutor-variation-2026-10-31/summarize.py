"""Compact inspection of earned outputs; no refitting or new test."""
import argparse
import datetime
import json
from pathlib import Path
import resource

ROOT = Path(__file__).resolve().parent

def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',help='owned direct child containing a completed reproduction')
    args = parser.parse_args()
    if args.output:
        destination = (ROOT/args.output).resolve()
        assert destination.parent==ROOT and destination.is_dir()
        ROOT = destination
    passes = []
    def read(name):
        b = (ROOT/name).read_bytes()
        passes.append({'path':name,'kind':'summary read and JSON decode','bytes':2*len(b)})
        return json.loads(b)
    reconstruction = read('RECONSTRUCTION.json')
    contrary = read('CONTRARY.json')
    source = read('SOURCE_PINS.json')
    resources = read('RESOURCES.json')
    accepted = [r for r in contrary['rows'] if r['cost_decreases'] and r['closer_to_natural_witness'] and r['edited_accepted'] and r['witness_accepted']]
    first_witness = sorted(accepted,key=lambda r:(r['reference_key'],r['factor']))[0]
    concise = {'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'costs_reconstructed':reconstruction['scalar_costs_reconstructed'],
      'max_cost_error':reconstruction['max_abs_cost_error'],
      'max_summary_error':reconstruction['max_abs_summary_error'],
      'tempo_range':reconstruction['controls']['teaching_tempo_factor_range'],
      'free_invariance_max':reconstruction['controls']['free_global_invariance_max'],
      'source':{k:source[k] for k in ['md5','sha256','whole_archive_bytes','gzip_decoded_bytes','wav_seconds','wav_headers_only_bytes','pin_counts','freeze_chronology','primary_metadata_version','license']},
      'contrary':{'overall':contrary['overall'],'by_phase':contrary['by_phase'],'lexical_first_accepted_witness':first_witness},
      'phases':{},'sequence_controls':reconstruction['controls']['sequence_controls']}
    for phase,p in reconstruction['phases'].items():
        concise['phases'][phase] = {}
        for method,m in p['methods'].items():
            concise['phases'][phase][method] = {k:m[k] for k in ['threshold','natural_acceptance','primary_pass']}
            concise['phases'][phase][method]['20pct'] = [{k:r[k] for k in ['location','factor','rejection','strict_increase','ties','decrease']} for r in m['challenges'] if r['factor'] in [.8,1.2]]
    (ROOT/'DERIVED_SUMMARY.json').write_text(json.dumps(concise,indent=2)+'\n')
    resources['passes'].extend(passes)
    resources['scientific_read_decoded_hash_bytes'] += sum(p['bytes'] for p in passes)
    resources['peak_rss_bytes'] = max(resources['peak_rss_bytes'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    resources['summary_completed'] = concise['timestamp']
    assert resources['scientific_read_decoded_hash_bytes'] < resources['scientific_byte_cap']
    (ROOT/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
    print(json.dumps({k:concise[k] for k in ['costs_reconstructed','max_cost_error','max_summary_error','tempo_range','contrary']},indent=2))
    print(json.dumps({k:resources[k] for k in ['scientific_read_decoded_hash_bytes','peak_rss_bytes','jobs']},indent=2))

if __name__=='__main__':
    main()

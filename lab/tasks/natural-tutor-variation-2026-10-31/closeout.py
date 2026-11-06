"""Save accounting/provenance and stable artifact pins; no new scientific scoring."""
import datetime,hashlib,importlib.metadata,json,pathlib,resource
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text())
    # Conservative allowance for bounded result/context reads, output verification,
    # source text parsing overhead and final small manifests, not a credit reset.
    if not any(x.get('operation')=='closeout context and output allowance' for x in ledger['scientific_byte_passes']):
        ledger['scientific_read_decoded_hash_bytes']+=2000000
        ledger['scientific_byte_passes'].append({'operation':'closeout context and output allowance',
          'kind':'conservative summary/PNG/code/manifest read allowance','bytes':2000000})
    assert ledger['web_operations']+len(ledger['direct_operations'])==10
    assert ledger['direct_ingress_bytes']==28280076
    assert ledger['scientific_read_decoded_hash_bytes']<250000000
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    manifest={'primary_citation':'Nicholson, Queen, Sober (2017), Bengalese Finch song repository, figshare4805749v9',
      'doi':'10.6084/m9.figshare.4805749.v9','license':'CC BY4.0',
      'metadata_url':'https://api.figshare.com/v2/articles/4805749',
      'methodology_url':'https://www.vocalpy.org/bfsongrepo/',
      'direct_operations':ledger['direct_operations'],
      'web_operations':[
        {'kind':'search','purpose':'primary repeated-song dataset availability','charge_bytes':500000},
        {'kind':'search','purpose':'song similarity, alignment and timing prior work','charge_bytes':500000},
        {'kind':'open','url':'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0096484','charge_bytes':500000},
        {'kind':'open','url':'https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1012329','charge_bytes':500000}],
      'web_transport_telemetry':'not supplied; charges are conservative response allowances, not measured backend transport',
      'full_archive_md5_verified':'4441c716563965db4c1522346f99a064',
      'full_archive_sha256':'28e8d2787d1faaa177d67f786cf77a03706189ca09933e5f6784547e9023e628'}
    (ROOT/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    exposure={'current_task':'natural-tutor-variation-2026-10-31','reset':False,
      'primary_raw':'Full gy6or6/032612 archive acquired/decoded,39 WAV headers and39 CSVs inspected;2693 annotation rows ultimately decoded',
      'primary_features':{'bird_units':1,'recordings':39,'abc_renditions':201,'teaching':98,'main':51,'revision':52,
        'status':'all consumed; no untouched examples remain in this acquired bird/day'},
      'extra_raw':'bl26lb16/041912 first1MB then overlapping first8MB prefixes; first complete30.167875s WAV inspected; no annotations exposed in prefixes',
      'extra_summary':'leading seven WAV member headers in8MB prefix; not a second inferential bird',
      'designed_edits':'Feature-level multiplicative interval edits and symbolic order permutations; not recorded biological errors or acoustic resynthesis',
      'protected_and_closed':'No reads of Pan20,Flesch81/B2/B20,later HABITS,memory targets,reserved worms,motor Figure4_42/optional210 or closed archive/model repairs',
      'inherited_failures':'All prior lineages/freezes/exposure/resource breaches unchanged; this worker owns only its assigned task directory'}
    (ROOT/'EXPOSURE.json').write_text(json.dumps(exposure,indent=2)+'\n')
    now=datetime.datetime.now(datetime.timezone.utc)
    resources={'timestamp':now.isoformat(),'start':'2026-11-01T01:23:45.964Z','fixed_deadline':'2026-11-01T02:38:45.964Z',
      'elapsed_seconds':(now-datetime.datetime.fromisoformat('2026-11-01T01:23:45.964+00:00')).total_seconds(),
      'logical_public_operations':10,'operation_cap':12,'measured_direct_ingress_bytes':ledger['direct_ingress_bytes'],
      'conservative_web_response_charge_bytes':2000000,'charged_ingress_bytes':ledger['direct_ingress_bytes']+2000000,'ingress_cap_bytes':35000000,
      'scientific_read_decoded_hash_bytes':ledger['scientific_read_decoded_hash_bytes'],'scientific_read_cap_bytes':250000000,
      'largest_measured_peak_rss_bytes':ledger['peak_rss_bytes_measured_max'],'peak_rss_cap_bytes':650000000,
      'failed_size_guard_peak_rss':'unmeasured;35MB conservative read/decode/hash charge retained; full measured compliance not claimed',
      'single_simultaneous_scientific_process':True,'numerical_threads':1,'jobs':0,
      'acquisition_closed_no_later_than':'2026-11-01T01:33:27.669668Z','acquisition_cutoff':'2026-11-01T01:38:45.964Z',
      'known_failures':['one DNS failure;0 application body bytes','initial1MB prefix lacks complete sample/CSV',
        'first8MB inspection size guard failed before final RSS capture','streaming WAV header seekable parser failed; saved separately',
        'direct rg of downloaded HTML denied before payload read','plot initial default cache mkdir denied; temporary cache used; future code uses owned MPLCONFIGDIR'],
      'unrun':['independent external review','complete motor learning','acoustic metric/reconstruction from waveforms','biological/perceptual target validation','second inferential bird'],
      'versions':{'numpy':importlib.metadata.version('numpy'),'matplotlib':importlib.metadata.version('matplotlib')}}
    (ROOT/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
    pins=[]
    for p in sorted(ROOT.iterdir()):
        if p.is_file() and p.name not in ['ARTIFACT_MANIFEST.json','ACQUISITION.json','STATE.md','RETURN_STATUS.json','TERMINAL_REPORT.md']:
            b=p.read_bytes();pins.append({'path':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    (ROOT/'ARTIFACT_MANIFEST.json').write_text(json.dumps({'timestamp':now.isoformat(),'pins':pins,
      'source_object_hashes':'SOURCE_MANIFEST.json; annotation hashes in FREEZE.json; replay directory separately verified'},indent=2)+'\n')
    print(json.dumps(resources,indent=2))
if __name__=='__main__':main()

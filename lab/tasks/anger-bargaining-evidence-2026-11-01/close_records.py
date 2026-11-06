"""Summarize already saved provenance; no acquisition or empirical fitting."""
import json,hashlib,datetime,resource
from pathlib import Path
P=Path(__file__).resolve().parent
fetch=json.loads((P/'FETCH_LEDGER.json').read_text())
external=json.loads((P/'EXTERNAL_OPERATIONS.json').read_text())
listing=json.loads((P/'sources/data_code_listing.json').read_text())
expected={x['attributes']['name']:x['attributes']['extra']['hashes']['sha256'] for x in listing['data']}
sources=[]
for r in fetch:
 sources.append({k:r[k] for k in ['url','name','at','known_local_bytes','sha256']})
 sources[-1].update(status=r.get('status'),error=r.get('error'),
  expected_listing_sha256=expected.get(r['name']),
  listing_match=r['sha256']==expected[r['name']] if r['name'] in expected else None)
out={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'families':{'primary':['Van Kleef et al 2004 DOI10.1037/0022-3514.86.1.57',
 'Ye et al 2023 DOI10.1007/s10726-023-09850-0','Ferracci et al 2022 DOI10.3390/bs12010008'],
 'empirical':['Ye et al 2023/upbcf','Ferracci et al 2022']},
 'sources':sources,'external_receipts':[{'path':x,'bytes':(P/x).stat().st_size,
   'sha256':hashlib.sha256((P/x).read_bytes()).hexdigest()} for x in sorted({r['saved'] for r in external})],
 'licensing':{'upbcf_node_license':None,'upbcf_access':'public; current user read',
 'article_2023':'CC-BY4 article, external dataset license not certified'},
 'version_warning':'Exact retrieved bytes, matching OSF current version-1 listings. Not a certification of historical publication bytes.'}
(P/'SOURCE_MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n')
resources={'recorded_at':out['created_at'],
 'bounds':{'public_operations':30,'empirical_families':2,'primary_families':3,
   'new_ingress_bytes':25000000,'additional_scientific_read_decode_hash_bytes':250000000,'peak_rss_bytes':500000000},
 'deliberate_top_level_public_operations':len(fetch)+len(external),'provider_operations':len(external),
 'local_retrieval_attempts':len(fetch),'local_successes':sum('error' not in r for r in fetch),
 'local_failed_attempts':sum('error' in r for r in fetch),
 'known_local_retrieved_body_bytes':sum(r['known_local_bytes'] for r in fetch),
 'provider_ingress_allowance_bytes':sum(r['charged_ingress_allowance_bytes'] for r in external),
 'failed_local_ingress_charge_bytes':sum(r['charged_ingress_bytes'] for r in fetch if 'error' in r),
 'total_charged_ingress_bytes':sum(r['charged_ingress_bytes'] for r in fetch)+sum(r['charged_ingress_allowance_bytes'] for r in external),
 'additional_scientific_read_decode_hash_charge_bytes':20000000,
 'read_charge_interpretation':'Conservative executed-work allowance including repeated small-source reads/decodes/hashes and provider-receipt handling; not measured physical OS I/O. Payload and receipt files each under 100KB, each routine runs a bounded number of reads; no archive/decompression or large matrix operations.',
 'largest_measured_local_scientific_process_peak_rss_bytes':max([r['peak_rss_bytes'] for r in fetch]+[resource.getrusage(resource.RUSAGE_SELF).ru_maxrss]),
 'unknowns':['Provider/backend transfer bytes and peaks','Exact redirected-download hop/request counts',
  'Tool wrapper/hook OS reads and peaks','inspect_listing.py process RSS not recorded',
  'Exact physical OS I/O; allowances are not measurements'],
 'operation_interpretation':'14 deliberately requested top-level public operations, counting failed DNS and within-page finds; not 14 measured HTTP requests. Three successful object downloads redirected to public object storage; provider and redirect internals unknown.',
 'scientific_execution':'Serial local Python standard-library commands only; no numerical pool/threads, fitting service, background job or paid compute',
 'scientific_runs':[{'command':'inspect_listing.py data_code_listing.json','runs':1},
   {'command':'inspect_csv.py Study1_rawdata.csv','runs':1},
   {'command':'first_data_check.py','runs':1,'at':'2026-11-01T06:50:37.371535Z','peak_rss_bytes':15450112},
   {'command':'inspect_csv.py Study1_cleandata.csv','runs':1},
   {'command':'source_reconstruction.py','runs':2,'first_at':'2026-11-01T06:51:46.244771Z','last_at':'2026-11-01T06:52:24.479842Z',
    'reason':'Second execution added excluded participants limit fields; original matching and factorial results unchanged','peak_rss_bytes':[15876096,15728640]}],
 'denied_commands':['Pre-START ordinary rg pipe denied; no public request',
 'Inline Python listing inspection denied; replaced by scoped script',
 'head on new CSV denied; replaced by scoped registered scientific reader'],
 'exposure':{'Study1_raw':'Full 47757-byte CSV acquired/hashed/decoded, all170records and auxiliary/coded-ID fields consumed',
 'Study1_clean':'Full5957-byte CSV/all144rows/all15columns consumed',
 'Study2_Study3':'Current file names/metadata/hashes and published summaries exposed; payloads not acquired',
 'GDN_Rmd':'4826bytes/code inspected, not executed',
 'Ferracci_2022':'Primary text/methods/results/access summaries only; no participant payloads',
 'Van_Kleef_2004':'Primary abstract/institutional summary only; no original outcomes',
 'old_empirical_payloads':'none; all protected targets/closed branches unchanged'},
 'stage_status':{'original_response_calculation':'executed','realized_bargaining_outcomes':'not certified',
 'source_design_gate':'failed/closed','main_freeze':'UNRUN','predictions_scoring_controls':'UNRUN','independent_review':'not earned'},
 'jobs_running':0}
(P/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
print(json.dumps({k:resources[k] for k in ['deliberate_top_level_public_operations','known_local_retrieved_body_bytes','total_charged_ingress_bytes','additional_scientific_read_decode_hash_charge_bytes','largest_measured_local_scientific_process_peak_rss_bytes','jobs_running']},indent=2))
print('Source payload hash matches:',{x['name']:x['listing_match'] for x in sources if x['listing_match'] is not None})

import pathlib,json,hashlib,datetime,resource
root=pathlib.Path(__file__).resolve().parent
d=json.loads((root/'FIRST_DATA_CHECK.json').read_text())
people=sorted(map(int,d['metadata_people']))
assert len(people)==47 and all(x['chronology_complete'] and x['rows']==378 for x in d['metadata_people'].values())
ranked=sorted([i for i in people if i!=3],key=lambda i:hashlib.sha256(('advice-reliability-v1:'+str(i)).encode()).hexdigest())
source=sorted([3]+ranked[:23]);evaluation=sorted(ranked[23:])
assert len(source)==24 and len(evaluation)==23 and not(set(source)&set(evaluation))
out={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gate':'PASS for a bounded conditional forecast, with explicit limitations',
 'first_event_gate':True,'source_people':source,'evaluation_people':evaluation,'source_n':24,'evaluation_n':23,
 'unit':'Person. Seven ordered adviser blocks,54trials each; score trials19–54 using strictly preceding observations as history.',
 'inclusion':'All47exported two-session completers, including author-discarded25. Do not condition our primary endpoint on final accuracy or angle-based keep_trial_angle. Three noncompleters are absent; population remains conditional on completion.',
 'chronology':'Initial judgment → own confidence → adviser judgment and adviser confidence → final judgment → correct direction feedback. Adviser changes at each block; generic stable performance disclosed, numerical attributes not disclosed in Experiment1.',
 'informative_contrast':'Initial gap/confidence against matched source-fit simple cumulative/recency reliability and own-revision-history predictors; test extra nonlinear precision-weight term under a held-person split.',
 'past_information':'Current relative judgment gap, two current confidences, initial RT, session/block/trial indices, preceding ADT judgments/revisions and feedback. No nominal agent_type, current correctness/absolute errors, supplied optimal prediction, full-record derived variables, final RT or future rows as inputs.',
 'limitations':['Exported signed errors, not acquisition-raw screen angles or clock logs. Relative-angle invariance is assumed from a shared correct-direction reference and checked against available supplied influence/accuracy values.',
 'IDT practice observations are not in this workbook; learn only recorded ADT histories, with declared generic priors.',
 'Artificial advisers depend on each person prior performance; frozen forecasts are conditional on current presented advice and recorded prior behavior, not autonomous forecasts of adviser generation.',
 'OSF ny75f/5ekdb node_license is null. Article CC-BY4 does not certify a separate external-file license.',
 'Whole workbook acquired/hashed and all worksheet XML decoded before split. Only person3 numeric response rows interpreted; other participant metadata and parsed response strings already exposed. No historical nonaccess proof.',
 'Closest paper already models feedback learning and trial-level normative advice; this is a held-person predictive comparison, not a claim to first social reliability learning or uniquely latent trust.'],
 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(root/'DESIGN_GATE.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))

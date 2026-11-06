import datetime,hashlib,json,pathlib
p=pathlib.Path(__file__).resolve().parent
assert not (p/'FREEZE.json').exists()
assert not (p/'predictions.npz').exists() and not (p/'evaluation_features.npz').exists()
now=datetime.datetime.now(datetime.timezone.utc)
assert now < datetime.datetime(2026,11,1,7,38,tzinfo=datetime.timezone.utc)
names=['PROTOCOL.md','SPLIT.json','data.py','model.py','evaluate.py','controls.py','fitted_B.npz','fitted_H.npz','DEVELOPMENT.json','SOURCE_VALIDATION.json','FIRST_DATA_CHECK.json','ACQUISITIONS.json','source_analysis.source','source_model.source','task_generate.source','task_config.source','task_main.source','behavior_zip.source']
pins={name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in names}
out=dict(frozen_at=now.isoformat(),evaluation_values_unread=True,n_development=20,n_evaluation=19,chosen_ridge_B=.01,chosen_ridge_H=.1,development_cycle='Initial numerical rotation check failed from uint16->float32 angle conversion; raw outcomes cast to float64 before deg2rad. INITIAL_DATA.py/INITIAL_MODEL.py and INITIAL_DEVELOPMENT_FAILURE.json preserve failure. Feature maps, split, gate and scientific comparison unchanged; no more development revisions.',pins=pins)
(p/'FREEZE.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))

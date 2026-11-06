"""Optional full replay, new directory only; never overwrite original evidence."""
from data import ROOT
import hashlib,json,pathlib,shutil,sys
import controls

dest=pathlib.Path(sys.argv[1]).resolve()
assert ROOT in dest.parents,'Keep replay output inside this task directory'
assert not dest.exists(),'Choose a new empty output path'
frozen=json.loads((ROOT/'FREEZE.json').read_text())
assert hashlib.sha256((ROOT/'controls.py').read_bytes()).hexdigest()==frozen['pins']['controls.py']
dest.mkdir(parents=True)
for name in ['development_features.npz','evaluation_features.npz']:
    shutil.copyfile(ROOT/name,dest/name)
# Only the data/output path changes; equations, seeds, features and fitting do not.
controls.ROOT=dest
controls.main()
actual=json.loads((dest/'CONTROLS.json').read_text())
expected=json.loads((ROOT/'CONTROLS.json').read_text())
for group in ['null','positive']:
    for key in ['passes','n','mean_gain','mean_oracle_loss','mean_current_PE_oracle_loss']:
        assert abs(actual['summary'][group][key]-expected['summary'][group][key])<1e-11
print('Full conditional control replay matches saved summaries:',dest)

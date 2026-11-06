"""One-off bounded NPZ directory inspection; no author module import."""
import json
from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parents[2] / "tasks" / "variable-tutor-correction-2026-11-01"
out = {}
for condition in ("main", "contrary_decoupled", "contrary_noiseless", "contrary_resolution"):
    out[condition] = {}
    for name in ("observations.npz", "predictions.npz"):
        path = root / condition / name
        with ZipFile(path) as archive:
            items = archive.infolist()
        out[condition][name] = dict(archive_bytes=path.stat().st_size,
                                    decoded_total=sum(x.file_size for x in items),
                                    members=[[x.filename,x.compress_size,x.file_size] for x in items[:35]])
target = Path(__file__).resolve().parent / "SCHEMA.json"
target.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))

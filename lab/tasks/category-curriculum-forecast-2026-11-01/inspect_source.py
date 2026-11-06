"""Small-sample inspection; never loops over participant payloads."""
import hashlib
import json
import pathlib
import resource
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
src = ROOT / "source"
out = {"stimuli_readme_rtf": (src / "stimuli-readme.rtf").read_text()}
listing = json.loads((src / "highsim-trial-files.json").read_text())
out["highsim_files"] = [{"name": x["attributes"]["name"],
    "size": x["attributes"]["size"], "download": x["links"].get("download")}
    for x in listing["data"]]
with zipfile.ZipFile(src / "highsim-trials.zip") as z:
    out["zip_members"] = [{"name": x.filename, "size": x.file_size,
        "compressed": x.compress_size, "crc": x.CRC} for x in z.infolist()]
    name = next(x for x in z.namelist() if x.split("/")[-1] == "20.dat")
    raw = z.read(name)
    lines = raw.decode().splitlines()
    out.update(sample_member=name, sample_sha256=hashlib.sha256(raw).hexdigest(),
               sample_lines=len(lines), sample_start=lines[:18], sample_end=lines[-10:])
out["peak_rss_native"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(ROOT / "SOURCE_INSPECTION.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))

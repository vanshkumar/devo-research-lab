"""Pin and decode only the score members authorized by BRIEF.md."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import resource
import struct
import sys
import time
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = "lab/reviews/calibration-frontier-result-2026-11-05"
NEW = "lab/reviews/independent-confirmation-result-2026-11-05"
AUTH_OLD = "lab/tasks/calibration-frontier-main-2026-11-05"
AUTH_NEW = "lab/tasks/independent-acquisition-confirmation-2026-11-05"
INPUTS = {
    f"{OLD}/FULL_CONTRASTS.npz": ("contributions", "primary_indices", "subjects", "labs"),
    f"{NEW}/REVIEW_REDUCTIONS.npz": (
        "subjects", "actors", "origins", "pooled", "primary_D", "labs", "cohorts", "stream_scores"
    ),
}
DICTIONARIES = (
    f"{OLD}/final_challenge.py", f"{OLD}/FINAL_CHALLENGE.json", f"{OLD}/REFINED_CHECK.json",
    f"{OLD}/independent.py", f"{AUTH_OLD}/MAIN_RUN_FREEZE.json",
    f"{NEW}/score_review.py", f"{NEW}/REVIEW_CALCULATION.json",
    f"{AUTH_NEW}/PRE_OUTCOME_SEAL.json", f"{AUTH_NEW}/ACCESS_FOOTPRINT.json",
    f"{AUTH_NEW}/LITERAL_SENSITIVITY.json",
)
FOOTPRINT = f"{AUTH_NEW}/ACCESS_FOOTPRINT.json"


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


class MeasuredFile(io.FileIO):
    def __init__(self, meter, relative):
        super().__init__(ROOT / relative, "rb")
        self.meter = meter
        self.relative = relative

    def read(self, size=-1):
        body = super().read(size)
        self.meter.reads[self.relative] += len(body)
        return body


class Meter:
    def __init__(self):
        self.start = utc()
        self.cpu = time.process_time()
        self.reads = Counter()
        self.exposure = []

    def read(self, relative):
        with MeasuredFile(self, relative) as handle:
            return handle.read()

    def receipt(self, error=None):
        return {
            "start_utc": self.start, "end_utc": utc(), "pid": __import__("os").getpid(),
            "cpu_seconds_in_process": time.process_time() - self.cpu,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if sys.platform == "darwin" else 1024),
            "logical_file_reads": self.reads, "logical_file_bytes": sum(self.reads.values()),
            "npz_members_inflated": self.exposure,
            "npz_inflated_bytes_including_npy_headers": sum(r["bytes"] for r in self.exposure),
            "ingress_bytes": 0, "terminal_error": error,
        }


def member_payload(handle, info):
    assert not info.flag_bits & 1 and info.compress_type == zipfile.ZIP_DEFLATED
    assert info.file_size < 500_000
    handle.seek(info.header_offset)
    header = handle.read(30)
    assert header[:4] == b"PK\x03\x04"
    name_len, extra_len = struct.unpack_from("<HH", header, 26)
    assert handle.read(name_len).decode() == info.filename
    handle.seek(extra_len, 1)
    body = handle.read(info.compress_size)
    assert len(body) == info.compress_size
    return body


def archive(relative, meter, pins=None, np=None):
    records = {}
    arrays = {}
    with MeasuredFile(meter, relative) as handle, zipfile.ZipFile(handle) as zipped:
        names = zipped.namelist()
        assert len(set(names)) == len(names)
        if pins is not None:
            assert pins["directory_member_names"] == names
        for key in INPUTS[relative]:
            info = zipped.getinfo(key + ".npy")
            body = member_payload(handle, info)
            record = dict(name=info.filename, compressed_bytes=info.compress_size,
                          npy_bytes=info.file_size, crc32=info.CRC, sha256_compressed=digest(body))
            records[key] = record
            if pins is None:
                continue
            assert record == pins["authorized"][key]
            raw = zlib.decompress(body, wbits=-15)
            meter.exposure.append(dict(archive=relative, member=info.filename, bytes=len(raw),
                                       sha256_npy=digest(raw)))
            assert len(raw) == info.file_size and zlib.crc32(raw) == info.CRC
            a = np.load(io.BytesIO(raw), allow_pickle=False)
            meter.exposure[-1].update(shape=list(a.shape), dtype=str(a.dtype), cells=a.size)
            arrays[key] = a
    return arrays if pins is not None else dict(directory_member_names=names, authorized=records)


def pin(meter):
    dictionaries = {name: digest(meter.read(name)) for name in DICTIONARIES}
    seal = json.loads(meter.read(f"{AUTH_NEW}/PRE_OUTCOME_SEAL.json"))
    assert dictionaries[FOOTPRINT] == seal["pins"][FOOTPRINT]
    value = {
        "pinned_utc": utc(), "analysis_plan_sha256": digest(meter.read(str((HERE / "PLAN.md").relative_to(ROOT)))),
        "receipt_sources": [f"{OLD}/final_challenge.py", f"{NEW}/score_review.py",
                            f"{NEW}/REPRODUCE.md", f"{OLD}/REPRODUCE.md"],
        "dictionaries_and_aggregate_sources_sha256": dictionaries,
        "archives": {relative: archive(relative, meter) for relative in INPUTS},
        "note": "Pinned approved compressed members only. Other members' names are directory metadata.",
    }
    assert not meter.exposure
    save("INPUT_PINS.json", value)


if __name__ == "__main__":
    meter = Meter()
    error = None
    try:
        assert sys.argv[1:] == ["pin"]
        pin(meter)
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save("PIN_RESOURCES.json", meter.receipt(error))

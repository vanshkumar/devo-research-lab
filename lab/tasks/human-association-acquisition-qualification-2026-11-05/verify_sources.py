"""Verify the saved metadata and analysis code without opening trial objects."""

import hashlib
import json
import math
import resource
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources"


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def collection_total(name, total):
    page = json.loads((SOURCES / name).read_bytes())
    assert page["links"]["next"] is None, name
    assert page["links"]["meta"]["total"] == len(page["data"]) == total, name
    return page["data"]


def verify():
    access = json.loads((ROOT / "SOURCE_ACCESS.json").read_bytes())
    request_evidence = []
    for request in access["direct"]:
        name = request["saveAs"]
        assert request["httpStatus"] == 200
        assert request["bodyBytes"] <= request["capBytes"]
        evidence = {"name": name, "method": request["method"]}
        if request["method"] == "HEAD":
            assert name == "dne-mat.head" and request["bodyBytes"] == 0
            headers = (SOURCES / name).read_bytes()
            evidence["headers_sha256"] = sha256(headers)
            evidence["headers_bytes"] = len(headers)
            for line in headers.decode("latin-1").splitlines():
                key, _, value = line.partition(":")
                if key.lower() in {"date", "etag", "content-length", "accept-ranges"}:
                    evidence[key.lower()] = value.strip()
        else:
            assert request["method"] == "GET"
            assert not name.endswith((".mat", ".csv", ".zip"))
            body = (SOURCES / name).read_bytes()
            assert len(body) == request["bodyBytes"]
            evidence.update(body_bytes=len(body), sha256=sha256(body))
        request_evidence.append(evidence)

    node = json.loads((SOURCES / "osf-node.json").read_bytes())["data"]
    assert node["id"] == "5gbr3" and node["attributes"]["public"]
    assert node["attributes"]["title"] == "RLWM - Tortoise and Hare"
    contributor, = collection_total("osf-contributors.json", 1)
    author = contributor["embeds"]["users"]["data"]["attributes"]
    assert contributor["attributes"]["bibliographic"]
    assert author["full_name"] == "Anne Collins"
    assert author["external_identity"]["ORCID"]["status"] == "VERIFIED"
    provider, = collection_total("osf-providers.json", 1)
    assert provider["attributes"]["provider"] == "osfstorage"
    file, = collection_total("osf-files.json", 1)
    version, = collection_total("osf-versions.json", 1)
    for name in ["osf-children.json", "osf-linked.json", "osf-file-cedar.json"]:
        collection_total(name, 0)
    attributes = file["attributes"]
    assert file["id"] == "5da0ab3126eb50000b7c6280"
    assert attributes["guid"] == "fz9sw"
    assert attributes["name"] == version["attributes"]["name"] == "TortoiseAndHareData.csv"
    assert attributes["current_version"] == int(version["id"]) == 1
    evaluation_size = attributes["size"]
    assert evaluation_size == version["attributes"]["size"] == 4242799
    assert attributes["extra"]["hashes"]["sha256"] == (
        "5067c78123c8f5693efb903e22e30b9cf093e64cb3892ee34fc96ba264186694"
    )

    tree = json.loads((SOURCES / "wmh-tree.json").read_bytes())
    assert not tree["truncated"] and tree["sha"] == "f2d4108dea80642e7d5b95d1c108916091a221c8"
    entries = {entry["path"]: entry for entry in tree["tree"]}
    for request in access["direct"]:
        if "/AnneCollins/WMH/git/blobs/" in request["url"]:
            body = (SOURCES / request["saveAs"]).read_bytes()
            git_blob = hashlib.sha1(f"blob {len(body)}\0".encode() + body).hexdigest()
            assert git_blob == request["url"].rsplit("/", 1)[1]
            assert any(item.get("size") == len(body) and item["sha"] == git_blob
                       for item in entries.values())
    source = entries["RLWM/DataSets/Expe3.mat"]
    other = entries["RLWM/DataSets/Expe1.mat"]
    assert source["size"] == 352400 and other["size"] == 621081
    assert source["sha"] == "2ab7b32fd81296453835edb81a7c59d97d9325a2"

    # These are design arithmetic from the papers, not row or subject counts in the files.
    target_acquisition = (8 * 3 + 6 * 6) * 13
    target_retention = (6 * 3 + 6 * 6) * 4
    source_max_trials = sum(size * blocks for size, blocks in enumerate([3, 6, 4, 3, 3, 3], 1)) * 15
    bundle_bytes = source["size"] + evaluation_size
    return {
        "scope": "Static metadata and code integrity, plus paper-design arithmetic",
        "author": {"full_name": author["full_name"], "orcid": author["external_identity"]["ORCID"]},
        "evaluation_object": {"file_id": file["id"], "version": version["id"],
                              "name": attributes["name"], "bytes": evaluation_size,
                              "advertised_hashes": attributes["extra"]["hashes"],
                              "versioned_download": version["links"]["download"]},
        "source_index": {"tree": tree["sha"], "entries": len(entries),
                         "brown_eeg_expe3": source, "brown_cf12_expe1": other},
        "design_arithmetic": {
            "berkeley_tested_counts": [49, 42],
            "publication_excluded_on_late_performance": 6,
            "berkeley_acquisition_opportunities_per_complete_person": target_acquisition,
            "berkeley_retention_opportunities_per_complete_person": target_retention,
            "nominal_complete_csv_trial_rows_if_91_and_both_phases": 91 * (target_acquisition + target_retention),
            "brown_eeg_reported_people": 40,
            "brown_eeg_nominal_max_acquisition_trials_per_person": source_max_trials,
            "brown_eeg_nominal_3_or_6_load_blocks_across_40_people": 40 * (4 + 3),
            "nominal_person_level_95pct_normal_halfwidth_in_SD_units": {
                str(n): round(1.96 / math.sqrt(n), 6) for n in (36, 40, 42, 43, 49, 85, 91)
            },
        },
        "body_price": {"brown_eeg_plus_berkeley_once": bundle_bytes,
                       "two_complete_nominal_reads_from_retained_files": 2 * bundle_bytes,
                       "cold_review_redownload_total": 2 * bundle_bytes,
                       "brown_cf12_instead_plus_berkeley_once": other["size"] + evaluation_size},
        "observed_direct_body_bytes": sum(r["bodyBytes"] for r in access["direct"]),
        "requests_verified": request_evidence,
        "trial_data_files_opened": 0,
    }


if __name__ == "__main__":
    result = verify()
    result["verification_peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        result["verification_peak_rss_bytes"] *= 1024  # Linux reports KiB.
    (ROOT / "VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "requests_verified"}, indent=2))

"""ONE frozen contrary: source-person resampling, independently implemented fits."""
import os
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import datetime, hashlib, json, pathlib, resource, time, zipfile
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "tasks/surprise-history-forecast-2026-11-01"
PENALTIES = (.001, .01, .1, 1., 10.)

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def means_by_person(values, ids, people):
    return np.array([values[ids == person].mean() for person in people])

class SourceFit:
    def __init__(self, x, y, ids):
        self.x, self.y, self.ids = x, y, ids
        self.people = np.unique(ids)
        self.indices = [np.flatnonzero(ids == p) for p in self.people]
        self.means = np.stack([x[ix].mean(axis=0) for ix in self.indices])
        self.seconds = np.stack([np.einsum("ni,nj->ij", x[ix], x[ix]) / len(ix) for ix in self.indices])
        targets = np.column_stack((np.cos(y), np.sin(y)))
        self.target_means = np.stack([targets[ix].mean(axis=0) for ix in self.indices])
        self.cross = np.stack([np.einsum("ni,nj->ij", x[ix], targets[ix]) / len(ix) for ix in self.indices])

    def model(self, copies, penalty):
        n = float(copies.sum())
        assert n > 0
        weights = copies / n
        mu = np.einsum("p,pi->i", weights, self.means)
        second = np.einsum("p,pij->ij", weights, self.seconds)
        cov = second - np.outer(mu, mu)
        sd = np.sqrt(np.maximum(np.diag(cov), 0))
        sd[sd < 1e-10] = 1.
        ymean = np.einsum("p,pi->i", weights, self.target_means)
        xy = np.einsum("p,pij->ij", weights, self.cross) - np.outer(mu, ymean)
        gram = cov / sd[:, None] / sd[None, :]
        gram += np.eye(len(mu)) * penalty / n
        coef = np.linalg.solve(gram, xy / sd[:, None])
        assert np.isfinite(coef).all()
        return mu, sd, ymean, coef

    @staticmethod
    def predict(model, x):
        mu, sd, intercept, coef = model
        vectors = np.einsum("ni,ij->nj", (x - mu) / sd, coef) + intercept
        prediction = np.arctan2(vectors[:, 1], vectors[:, 0])
        prediction[np.linalg.norm(vectors, axis=1) < 1e-12] = 0
        return prediction

    def choose(self, copies):
        losses = np.zeros(len(PENALTIES))
        fold = np.arange(len(self.people)) % 5
        for k in range(5):
            validation = (fold == k) & (copies > 0)
            if not validation.any():
                continue
            train = copies.copy()
            train[fold == k] = 0
            assert train.sum() > 0
            selected_rows = np.concatenate([self.indices[j] for j in np.flatnonzero(validation)])
            for j, penalty in enumerate(PENALTIES):
                pred = self.predict(self.model(train, penalty), self.x[selected_rows])
                loss = 1 - np.cos(self.y[selected_rows] - pred)
                start = 0
                for person_index in np.flatnonzero(validation):
                    count = len(self.indices[person_index])
                    losses[j] += copies[person_index] * loss[start:start + count].mean() / copies.sum()
                    start += count
        chosen = int(np.argmin(losses))
        return self.model(copies, PENALTIES[chosen]), PENALTIES[chosen], losses

def direct_fit_check(fitter, copies, penalty, xval):
    ids, x, y = fitter.ids, fitter.x, fitter.y
    lookup = {p: j for j, p in enumerate(fitter.people)}
    per_row = np.array([copies[lookup[p]] / len(fitter.indices[lookup[p]]) for p in ids])
    per_row /= per_row.sum()
    mu = np.sum(x * per_row[:, None], axis=0)
    sd = np.sqrt(np.sum((x - mu) ** 2 * per_row[:, None], axis=0))
    sd[sd < 1e-10] = 1.
    z = np.column_stack((np.ones(len(x)), (x - mu) / sd))
    targets = np.column_stack((np.cos(y), np.sin(y)))
    gram = np.einsum("ni,n,nj->ij", z, per_row, z)
    gram += np.diag(np.r_[0., np.repeat(penalty / copies.sum(), x.shape[1])])
    rhs = np.einsum("ni,n,nj->ij", z, per_row, targets)
    coef = np.linalg.solve(gram, rhs)
    vectors = np.einsum("ni,ij->nj", np.column_stack((np.ones(len(xval)), (xval - mu) / sd)), coef)
    pred = np.arctan2(vectors[:, 1], vectors[:, 0])
    pred[np.linalg.norm(vectors, axis=1) < 1e-12] = 0
    moment = fitter.predict(fitter.model(copies, penalty), xval)
    return float(np.max(abs(np.angle(np.exp(1j * (pred - moment))))))

def main():
    start, clock_start = now(), time.monotonic()
    plan = (HERE / "CONTRARY_PLAN.md").read_bytes()
    plan_sha = hashlib.sha256(plan).hexdigest()
    d = dict(np.load(SOURCE / "development_features.npz", allow_pickle=False))
    e = dict(np.load(SOURCE / "evaluation_features.npz", allow_pickle=False))
    saved = dict(np.load(SOURCE / "predictions.npz", allow_pickle=False))
    assert np.array_equal(e["keys"], saved["keys"])
    people = np.unique(e["keys"][:, 0])
    designs_d = {"B": d["B"], "H": np.column_stack((d["B"], d["extra"]))}
    designs_e = {"B": e["B"], "H": np.column_stack((e["B"], e["extra"]))}
    fitters = {name: SourceFit(designs_d[name], d["y"], d["keys"][:, 0]) for name in ("B", "H")}
    verification = {}
    ones = np.ones(20, dtype=int)
    nonuniform = np.random.default_rng(19801).multinomial(20, np.repeat(.05, 20))
    for name in ("B", "H"):
        fitter = fitters[name]
        model, penalty, cv = fitter.choose(ones)
        prediction = fitter.predict(model, designs_e[name])
        difference = np.angle(np.exp(1j * (prediction - saved[name])))
        error = float(np.max(abs(difference)))
        direct_error = direct_fit_check(fitter, nonuniform, penalty, designs_e[name])
        verification[name] = {"selected_penalty": penalty, "cv_losses": cv.tolist(),
            "max_original_forecast_difference": error, "nonuniform_moments_vs_direct_max_radians": direct_error}
        assert penalty == {"B": .01, "H": .1}[name]
        assert error < 1e-8 and direct_error < 1e-8
    (HERE / "CONTRARY_FIT_VERIFICATION.json").write_text(json.dumps({"at": now(), "verification": verification}, indent=2) + "\n")
    print("Independent source selection and direct/moment fit checks passed", verification, flush=True)
    source_rng = np.random.default_rng(2026110103)
    evaluation_rng = np.random.default_rng(2026110104)
    records, copies_all, loss_b_all, loss_h_all = [], [], [], []
    for rep in range(200):
        if time.monotonic() - clock_start > 900:
            raise RuntimeError("Contrary 15-minute compute guard; preserve partial results and stop.")
        copies = source_rng.multinomial(20, np.repeat(.05, 20))
        predictions, penalties = {}, {}
        for name in ("B", "H"):
            model, penalties[name], _ = fitters[name].choose(copies)
            predictions[name] = fitters[name].predict(model, designs_e[name])
        losses = {name: 1 - np.cos(e["y"] - predictions[name]) for name in ("B", "H")}
        pb = means_by_person(losses["B"], e["keys"][:, 0], people)
        ph = means_by_person(losses["H"], e["keys"][:, 0], people)
        context_gain = {}
        for context in (0, 1):
            ix = e["keys"][:, 1] == context
            b = means_by_person(losses["B"][ix], e["keys"][ix, 0], people).mean()
            h = means_by_person(losses["H"][ix], e["keys"][ix, 0], people).mean()
            context_gain[str(context)] = float(1 - h / b)
        draw = evaluation_rng.integers(0, 19, 19)
        paired = float(1 - ph[draw].mean() / pb[draw].mean())
        bootstrap = np.random.default_rng(2026110200 + rep).integers(0, 19, (10000, 19))
        interval = np.quantile(1 - ph[bootstrap].mean(axis=1) / pb[bootstrap].mean(axis=1), [.025, .975]).tolist()
        gain = float(1 - ph.mean() / pb.mean())
        positive = all(v > 0 for v in context_gain.values())
        records.append({"rep": rep, "source_gain": gain, "source_plus_paired_evaluation_gain": paired,
            "context_gain": context_gain, "conditional_person_bootstrap95": interval, "penalties": penalties,
            "passes_original_joint_rule": bool(gain >= .05 and interval[0] > 0 and positive),
            "B_loss": float(pb.mean()), "H_loss": float(ph.mean())})
        copies_all.append(copies)
        loss_b_all.append(pb)
        loss_h_all.append(ph)
        if rep % 25 == 0:
            print("Source replicate", rep, "elapsed_seconds", round(time.monotonic() - clock_start, 2), flush=True)
            (HERE / "CONTRARY_PARTIAL.json").write_text(json.dumps({"at": now(), "rows": records}, indent=2) + "\n")
    summary = {}
    for field in ("source_gain", "source_plus_paired_evaluation_gain"):
        values = np.array([r[field] for r in records])
        summary[field] = {"percentiles_2_5_50_97_5": np.quantile(values, [.025, .5, .975]).tolist(),
            "mean": float(values.mean()), "n_at_least_5_percent": int(np.sum(values >= .05)),
            "min": float(values.min()), "max": float(values.max())}
    summary["both_contexts_positive"] = sum(all(v > 0 for v in r["context_gain"].values()) for r in records)
    summary["original_joint_passes"] = sum(r["passes_original_joint_rule"] for r in records)
    summary["penalty_counts"] = {name: {str(lam): sum(r["penalties"][name] == lam for r in records) for lam in PENALTIES} for name in ("B", "H")}
    decoded = 0
    source_bytes = 0
    for filename in ("development_features.npz", "evaluation_features.npz", "predictions.npz"):
        source_bytes += (SOURCE / filename).stat().st_size
        with zipfile.ZipFile(SOURCE / filename) as archive:
            decoded += sum(member.file_size for member in archive.infolist())
    out = {"started_at": start, "ended_at": now(), "plan_sha256": plan_sha, "replicates": 200,
        "source_seed": 2026110103, "paired_evaluation_seed": 2026110104, "author_code_imported": False,
        "original_fit_verification": verification, "summary": summary, "rows": records,
        "input_container_bytes": source_bytes, "input_decoded_array_bytes": decoded,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "elapsed_seconds": time.monotonic() - clock_start,
        "scope": "Finite empirical source/evaluation bootstrap perturbation, source selection repeated and duplicate identities grouped. These percentiles are not calibrated confidence intervals or new held-out evidence. Original frozen result unchanged."}
    np.savez(HERE / "contrary_person_losses.npz", source_copies=np.stack(copies_all),
        source_ids=fitters["B"].people, evaluation_ids=people,
        B_person_loss=np.stack(loss_b_all), H_person_loss=np.stack(loss_h_all))
    (HERE / "CONTRARY.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))

if __name__ == "__main__":
    main()

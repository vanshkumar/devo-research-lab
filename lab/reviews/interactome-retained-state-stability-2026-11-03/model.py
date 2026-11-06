"""Independent edge-list expression of the pinned 2019 release; no lab helper imports."""
import os
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy import sparse, linalg
from scipy.sparse.linalg import splu
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "lab/tasks/interactome-transient-reachability-2026-11-03/sources"
ORIGINAL = ROOT / "lab/tasks/connectome-persistence-contrast-2026-11-03/sources/interactome-initialize.py"
AUTHOR = ROOT / "lab/tasks/interactome-retained-state-stability-2026-11-03"
OUT = Path(__file__).resolve().parent
N = 279
GC, CAP, EC, AR, AD, BETA, CURRENT = .1, .015, -35., 1/1.5, 5/1.5, .125, 100000.
SCALE = 5.638259640019669
D = np.r_[np.full(N, SCALE), np.full(N, .1)]

def gitblob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

class Circuit:
    def __init__(self):
        self.gg = np.load(ASSETS / "Gg.npy", allow_pickle=False)
        self.gs = np.load(ASSETS / "Gs.npy", allow_pickle=False)
        self.e = -48. * np.load(ASSETS / "emask.npy", allow_pickle=False).reshape(N)
        self.gi, self.gj = np.nonzero(self.gg)
        self.gw = self.gg[self.gi, self.gj]
        self.si, self.sj = np.nonzero(self.gs)
        self.sw = self.gs[self.si, self.sj]
        self.G = sparse.csr_matrix(self.gg)
        self.S = sparse.csr_matrix(self.gs)
        self.gsum = np.bincount(self.gi, self.gw, minlength=N)
        self.ssum = np.bincount(self.si, self.sw, minlength=N)
        eq = round(AR / (AR + 2 * AD), 4)
        self.threshold_matrix = sparse.diags(GC + self.gsum + eq * (self.ssum - np.diag(self.gs))) - self.G
        self.threshold_factor = splu(self.threshold_matrix.tocsc())
        self.threshold_base = self.threshold_factor.solve(np.full(N, GC * EC) + eq * (self.S @ self.e))
        self.threshold_response = self.threshold_factor.solve(CURRENT * np.eye(N))
        raw_names = json.loads((ASSETS / "names-response.json").read_text())["result"]["structuredContent"]["content"]
        self.names = ast.literal_eval(raw_names)
        self.motor = np.array([i for i, n in enumerate(self.names) if n.startswith(("DB", "VB", "DD", "VD"))])
        self.background = self.mask({"PLML": .2, "PLMR": .2, "ASKL": .24, "ASKR": .24})
        self.fwd = self.mask({"PLML": .14, "PLMR": .14, "AVBL": .23, "AVBR": .23})
        self._const_jvv = (self.G - sparse.diags(self.gsum + GC)) / CAP

    def mask(self, values):
        z = np.zeros(N)
        for name, value in values.items():
            z[self.names.index(name)] = value
        return z

    def threshold(self, mask):
        return self.threshold_base + np.einsum("ij,j->i", self.threshold_response, mask)

    def rhs(self, y, mask):
        v, s = y[:N], y[N:]
        gap = np.bincount(self.gi, self.gw * (v[self.gj] - v[self.gi]), minlength=N)
        syn = np.bincount(self.si, self.sw * s[self.sj] * (self.e[self.sj] - v[self.si]), minlength=N)
        dv = (GC * (EC - v) + gap + syn + CURRENT * mask) / CAP
        sig = expit(BETA * (v - self.threshold(mask)))
        ds = AR * (1 - s) * sig - AD * s
        return np.r_[dv, ds]

    def jac(self, y, mask):
        v, s = y[:N], y[N:]
        sig = expit(BETA * (v - self.threshold(mask)))
        synsum = np.bincount(self.si, self.sw * s[self.sj], minlength=N)
        jvv = self._const_jvv - sparse.diags(synsum / CAP)
        jvs = sparse.csr_matrix((self.sw * (self.e[self.sj] - v[self.si]) / CAP, (self.si, self.sj)), shape=(N, N))
        jsv = sparse.diags(AR * (1-s) * BETA * sig * (1-sig))
        jss = sparse.diags(-AR * sig - AD)
        return sparse.bmat([[jvv, jvs], [jsv, jss]], format="csc")

    def source_comparator(self):
        """Only original released functions, not an investigator/reviewer helper."""
        names = {"EffVth", "EffVth_rhs", "update_Mask", "membrane_voltageRHS", "compute_jacobian", "voltage_filter"}
        parsed = ast.parse(ORIGINAL.read_text())
        tree = ast.Module(body=[n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
        scope = dict(np=np, sparse=sparse, linalg=linalg, N=N, Gc=GC, C=CAP, Ec=EC, ar=AR, ad=AD, B=BETA, Iext=CURRENT,
                     ggap=1., gsyn=1., Gg_Dynamic=self.gg.copy(), Gs_Dynamic=self.gs.copy(), E=self.e[:, None],
                     EMat=np.tile(self.e, (N, 1)), rate=.025, offset=.15)
        exec(compile(tree, str(ORIGINAL), "exec"), scope)
        scope["EffVth"](self.gg, self.gs)
        return scope

def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")

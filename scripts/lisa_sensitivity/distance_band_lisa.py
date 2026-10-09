"""
Distance-band (Euclidean radius) LISA, compared against KNN LISA.
Uses sparse W matrix + conditional permutation via global shuffle + sparse
matvec (fast, standard esda/GeoDa-equivalent approach) for both schemes.
"""
import numpy as np
from scipy.spatial import cKDTree
import scipy.sparse as sp
import matplotlib.pyplot as plt
import time

np.random.seed(42)

d = np.load("../grid_level_arrays.npz")
P30, H30 = d["P30"], d["H30"]
coords = np.load("grid_coords.npz")
x, y = coords["x"], coords["y"]
n = len(x)
tree = cKDTree(np.column_stack([x, y]))

exposure30 = P30 * H30
vals = np.log1p(exposure30)
z = vals - vals.mean()
m2 = np.mean(z ** 2)


def knn_weight_matrix(k):
    _, idx = tree.query(np.column_stack([x, y]), k=k + 1)
    idx = idx[:, 1:]
    rows = np.repeat(np.arange(n), k)
    cols = idx.ravel()
    data = np.full(n * k, 1.0 / k)
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n))


def distband_weight_matrix(r):
    pairs = tree.query_pairs(r=r, output_type="ndarray")
    rows = np.concatenate([pairs[:, 0], pairs[:, 1]])
    cols = np.concatenate([pairs[:, 1], pairs[:, 0]])
    data = np.ones(len(rows))
    W = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    deg = np.asarray(W.sum(axis=1)).ravel()
    deg[deg == 0] = 1  # avoid div0 for isolates
    Dinv = sp.diags(1.0 / deg)
    return Dinv @ W, deg


def local_moran_sparse(Wmat, nperm=499):
    lag = Wmat @ z
    I_obs = z * lag / m2
    I_sim = np.empty((nperm, n), dtype=np.float32)
    for p in range(nperm):
        zp = np.random.permutation(z)
        # focal z_i stays fixed (conditional permutation); only the
        # *assignment of values to neighbor positions* is shuffled
        I_sim[p] = z * (Wmat @ zp) / m2
    ge = (np.abs(I_sim) >= np.abs(I_obs)).sum(axis=0)
    p_sim = (ge + 1) / (nperm + 1)
    quad = np.full(n, "NS", dtype=object)
    hh = (z > 0) & (lag > 0); ll = (z < 0) & (lag < 0)
    hl = (z > 0) & (lag < 0); lh = (z < 0) & (lag > 0)
    quad[hh] = "HH"; quad[ll] = "LL"; quad[hl] = "HL"; quad[lh] = "LH"
    return dict(I=I_obs, p=p_sim, quad=quad, lag=lag)


def bh_fdr(p, alpha=0.05):
    nloc = len(p); order = np.argsort(p); ranked = p[order]
    thresh = (np.arange(1, nloc + 1) / nloc) * alpha
    below = ranked <= thresh
    if not below.any(): return np.zeros(nloc, dtype=bool)
    cutoff_p = ranked[np.max(np.where(below)[0])]
    return p <= cutoff_p


radii = [1100, 1600, 2300, 3300]
results_db = {}
for r in radii:
    t0 = time.time()
    W, deg = distband_weight_matrix(r)
    res = local_moran_sparse(W)
    print(f"r={r}m  avg_deg={deg.mean():.1f}  ({time.time()-t0:.1f}s)")
    sig = bh_fdr(res["p"], 0.05)
    q = np.where(sig, res["quad"], "NS")
    counts = {c: (q == c).mean() * 100 for c in ["HH", "LL", "HL", "LH", "NS"]}
    print(f"   FDR-BH0.05: HH={counts['HH']:.1f}% LL={counts['LL']:.1f}% NS={counts['NS']:.1f}%")
    results_db[r] = res

np.save("distband_lisa_results.npy", results_db, allow_pickle=True)

COLORS = {"HH": "#C44E52", "LL": "#4C72B0", "HL": "#F2A65A", "LH": "#8172B2", "NS": "#dddddd"}
fig, axes = plt.subplots(1, len(radii), figsize=(4.2*len(radii), 4.5), dpi=140)
for ax, r in zip(axes, radii):
    res = results_db[r]
    sig = bh_fdr(res["p"], 0.05)
    q = np.where(sig, res["quad"], "NS")
    colors = np.array([COLORS[c] for c in q])
    order = np.argsort(q != "NS")
    ax.scatter(x[order], y[order], c=colors[order], s=1.1, marker='s', linewidths=0)
    ax.set_title(f"distance-band r={r}m", fontsize=10)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
plt.suptitle("Grid-level LISA, Euclidean distance-band weights (2030, FDR-BH 0.05)", fontweight='bold')
plt.tight_layout()
plt.savefig("distband_sensitivity_2030.png", dpi=140, bbox_inches="tight")
print("saved")

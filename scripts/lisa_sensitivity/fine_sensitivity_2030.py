"""
Grid-level LISA, 2030 only, p<=0.001, two neighbor schemes:
  - KNN: K = 4, 8, 12, 16, 24
  - Distance band (Euclidean): r = 500, 1000, 1500, 2000 m
nperm=999 so p=0.001 is resolvable ( (ge+1)/(nperm+1), min = 0.001 ).
Each setting saved as its own titled PNG.
"""
import numpy as np
from scipy.spatial import cKDTree
import scipy.sparse as sp
import matplotlib.pyplot as plt
import time

np.random.seed(42)
NPERM = 999
PTHRESH = 0.001

d = np.load("../grid_level_arrays.npz")
P30, H30 = d["P30"], d["H30"]
coords = np.load("grid_coords.npz")
x, y = coords["x"], coords["y"]
n = len(x)
tree = cKDTree(np.column_stack([x, y]))

vals = np.log1p(P30 * H30)
z = vals - vals.mean()
m2 = np.mean(z ** 2)


def knn_W(k):
    _, idx = tree.query(np.column_stack([x, y]), k=k + 1)
    idx = idx[:, 1:]
    rows = np.repeat(np.arange(n), k)
    cols = idx.ravel()
    data = np.full(n * k, 1.0 / k)
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n)), k


def distband_W(r):
    pairs = tree.query_pairs(r=r, output_type="ndarray")
    rows = np.concatenate([pairs[:, 0], pairs[:, 1]])
    cols = np.concatenate([pairs[:, 1], pairs[:, 0]])
    data = np.ones(len(rows))
    W = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    deg = np.asarray(W.sum(axis=1)).ravel()
    deg_safe = deg.copy(); deg_safe[deg_safe == 0] = 1
    Dinv = sp.diags(1.0 / deg_safe)
    return Dinv @ W, deg


def local_moran_sparse(Wmat, nperm=NPERM):
    lag = Wmat @ z
    I_obs = z * lag / m2
    I_sim = np.empty((nperm, n), dtype=np.float32)
    for p in range(nperm):
        zp = np.random.permutation(z)
        I_sim[p] = z * (Wmat @ zp) / m2
    ge = (np.abs(I_sim) >= np.abs(I_obs)).sum(axis=0)
    p_sim = (ge + 1) / (nperm + 1)
    quad = np.full(n, "NS", dtype=object)
    hh = (z > 0) & (lag > 0); ll = (z < 0) & (lag < 0)
    hl = (z > 0) & (lag < 0); lh = (z < 0) & (lag > 0)
    quad[hh] = "HH"; quad[ll] = "LL"; quad[hl] = "HL"; quad[lh] = "LH"
    return dict(I=I_obs, p=p_sim, quad=quad, lag=lag)


COLORS = {"HH": "#C44E52", "LL": "#4C72B0", "HL": "#F2A65A", "LH": "#8172B2", "NS": "#dddddd"}


def plot_one(res, title, fname):
    sig = res["p"] <= PTHRESH
    q = np.where(sig, res["quad"], "NS")
    counts = {c: (q == c).mean() * 100 for c in ["HH", "LL", "HL", "LH", "NS"]}
    fig, ax = plt.subplots(figsize=(6.5, 7), dpi=160)
    colors = np.array([COLORS[c] for c in q])
    order = np.argsort(q != "NS")
    ax.scatter(x[order], y[order], c=colors[order], s=1.6, marker='s', linewidths=0)
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
    subtitle = f"HH {counts['HH']:.1f}%  ·  LL {counts['LL']:.1f}%  ·  significant {100-counts['NS']:.1f}%  ·  n={n:,}"
    ax.text(0.5, -0.03, subtitle, transform=ax.transAxes, ha='center', va='top', fontsize=9, color="#555555")
    handles = [plt.Line2D([0], [0], marker='s', color='w', markerfacecolor=COLORS[c], markersize=9, label=c)
               for c in ["HH", "LL", "HL", "LH", "NS"]]
    ax.legend(handles=handles, loc='lower left', fontsize=8, frameon=False, bbox_to_anchor=(-0.02, -0.01))
    plt.tight_layout()
    plt.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {fname}  (sig={100-counts['NS']:.1f}%, HH={counts['HH']:.1f}%, LL={counts['LL']:.1f}%)")


print("=== KNN ===")
for k in [4, 8, 12, 16, 24]:
    t0 = time.time()
    W, _ = knn_W(k)
    res = local_moran_sparse(W)
    title = f"2030 (KNN:{k}; p-value≤0.001)"
    fname = f"png_knn_{k}.png"
    print(f"K={k} ({time.time()-t0:.1f}s)", end="  ")
    plot_one(res, title, fname)

print("\n=== Distance band ===")
for r in [500, 1000, 1500, 2000]:
    t0 = time.time()
    W, deg = distband_W(r)
    res = local_moran_sparse(W)
    title = f"2030 (Distance Band:{r}m; p-value≤0.001)"
    fname = f"png_db_{r}.png"
    print(f"r={r}m avg_deg={deg.mean():.1f} ({time.time()-t0:.1f}s)", end="  ")
    plot_one(res, title, fname)

print("\nall done")

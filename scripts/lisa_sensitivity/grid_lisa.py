"""
Grid-level Local Moran's I (LISA) sensitivity analysis.
Varies: K (number of KNN neighbors) and significance threshold (raw p vs FDR-BH),
to check whether the original K=8 / FDR-corrected setup is masking smaller,
regional clusters.
"""
import numpy as np
from scipy.spatial import cKDTree
import time

np.random.seed(42)

d = np.load("../grid_level_arrays.npz")
final_mask = d["final_mask"]  # (610, 642)
P30, P60, H30, H60 = d["P30"], d["P60"], d["H30"], d["H60"]

POP_X0, POP_Y0, POP_CS = 746611.0313, 2067943.9535, 1000.0
H, W = final_mask.shape
rows, cols = np.where(final_mask)
x = POP_X0 + (cols + 0.5) * POP_CS
y = POP_Y0 - (rows + 0.5) * POP_CS
n = len(x)
print("n valid cells:", n)

exposure30 = P30 * H30
exposure60 = P60 * H60
ln30 = np.log1p(exposure30)
ln60 = np.log1p(exposure60)

tree = cKDTree(np.column_stack([x, y]))


def local_moran(vals, k, nperm=199):
    z = vals - vals.mean()
    m2 = np.mean(z ** 2)
    # observed: true KNN neighbors (k+1 to drop self)
    _, idx = tree.query(np.column_stack([x, y]), k=k + 1)
    idx = idx[:, 1:]  # drop self
    lag = z[idx].mean(axis=1)
    I_obs = z * lag / m2

    # permutation null: free sampling (random k-draws from whole pool, self-inclusion
    # probability ~k/n is negligible at this n) -- standard large-n approximation
    I_sim = np.empty((nperm, n), dtype=np.float32)
    for p in range(nperm):
        samp_idx = np.random.randint(0, n, size=(n, k))
        lag_sim = z[samp_idx].mean(axis=1)
        I_sim[p] = z * lag_sim / m2

    # two-sided empirical p-value
    ge = (np.abs(I_sim) >= np.abs(I_obs)).sum(axis=0)
    p_sim = (ge + 1) / (nperm + 1)

    # quadrant
    quad = np.full(n, "NS", dtype=object)
    hh = (z > 0) & (lag > 0)
    ll = (z < 0) & (lag < 0)
    hl = (z > 0) & (lag < 0)
    lh = (z < 0) & (lag > 0)
    quad[hh] = "HH"; quad[ll] = "LL"; quad[hl] = "HL"; quad[lh] = "LH"

    return dict(I=I_obs, p=p_sim, quad=quad, lag=lag, z=z)


def bh_fdr(p, alpha=0.05):
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    thresh = (np.arange(1, n + 1) / n) * alpha
    below = ranked <= thresh
    if not below.any():
        return np.zeros(n, dtype=bool)
    max_rank = np.max(np.where(below)[0])
    cutoff_p = ranked[max_rank]
    return p <= cutoff_p


def summarize(res, label):
    quad = res["quad"]
    p = res["p"]
    out = {}
    for name, sig_mask in [
        ("raw_p05", p < 0.05),
        ("raw_p01", p < 0.01),
        ("fdr_bh05", bh_fdr(p, 0.05)),
    ]:
        q = np.where(sig_mask, quad, "NS")
        counts = {c: (q == c).mean() * 100 for c in ["HH", "LL", "HL", "LH", "NS"]}
        out[name] = counts
        print(f"  [{label}] {name:10s} HH={counts['HH']:5.1f}% LL={counts['LL']:5.1f}% "
              f"HL={counts['HL']:4.1f}% LH={counts['LH']:4.1f}% NS={counts['NS']:5.1f}%  "
              f"(sig={100-counts['NS']:.1f}%)")
    return out


all_results = {}
for k in [4, 8, 16, 24]:
    print(f"\n=== K = {k} ===")
    t0 = time.time()
    res30 = local_moran(ln30, k)
    res60 = local_moran(ln60, k)
    print(f"  (computed in {time.time()-t0:.1f}s)")
    s30 = summarize(res30, f"2030,K={k}")
    s60 = summarize(res60, f"2060,K={k}")
    all_results[k] = dict(res30=res30, res60=res60, s30=s30, s60=s60)

np.save("grid_lisa_results.npy", all_results, allow_pickle=True)
np.savez("grid_coords.npz", x=x, y=y, rows=rows, cols=cols)
print("\nsaved.")

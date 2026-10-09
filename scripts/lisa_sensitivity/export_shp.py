import sys
sys.path.insert(0, '.')
import numpy as np
from scipy.spatial import cKDTree
import scipy.sparse as sp
from shp_writer import write_point_shapefile

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
    return sp.csr_matrix((data, (rows, cols)), shape=(n, n))

def distband_W(r):
    pairs = tree.query_pairs(r=r, output_type="ndarray")
    rows = np.concatenate([pairs[:, 0], pairs[:, 1]])
    cols = np.concatenate([pairs[:, 1], pairs[:, 0]])
    data = np.ones(len(rows))
    W = sp.csr_matrix((data, (rows, cols)), shape=(n, n))
    deg = np.asarray(W.sum(axis=1)).ravel()
    deg_safe = deg.copy(); deg_safe[deg_safe == 0] = 1
    Dinv = sp.diags(1.0 / deg_safe)
    return Dinv @ W

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
    return I_obs, p_sim, quad, lag

PRJ_WKT = 'PROJCS["KGD2002_Unified_Coordinate_System",GEOGCS["KGD2002",DATUM["D_Korea_Geodetic_Datum_2002",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",1000000.0],PARAMETER["False_Northing",2000000.0],PARAMETER["Central_Meridian",127.5],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",38.0],UNIT["Meter",1.0]]'

fields = [("QUAD", "C", 2, 0), ("LMI_I", "N", 14, 6), ("P_VALUE", "N", 10, 6),
          ("SIG001", "N", 1, 0), ("LAG_Z", "N", 14, 6), ("Z", "N", 14, 6)]

def export(label, Wmat, outname):
    I_obs, p_sim, quad, lag = local_moran_sparse(Wmat)
    sig = (p_sim <= PTHRESH).astype(int)
    quad_out = np.where(sig == 1, quad, "NS")
    rows = list(zip(quad_out.tolist(), I_obs.tolist(), p_sim.tolist(), sig.tolist(), lag.tolist(), z.tolist()))
    write_point_shapefile(outname, x, y, fields, rows, prj_wkt=PRJ_WKT)
    n_hh = (quad_out == "HH").sum(); n_ll = (quad_out == "LL").sum()
    print(f"{label}: wrote {outname}.shp  (n={n}, HH={n_hh}, LL={n_ll}, sig={sig.sum()})")

export("KNN:4, p<=0.001", knn_W(4), "grid_LISA_2030_KNN4_p001")
export("Distance Band:1000m, p<=0.001", distband_W(1000), "grid_LISA_2030_DistBand1000m_p001")
print("done")

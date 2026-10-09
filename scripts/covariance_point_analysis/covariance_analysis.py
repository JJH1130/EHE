"""
Province-level Cov(population, heatdays) / Pearson r, computed from the
500m population point layer, then compared against each province's
Fig2 relative bias (%) (provincial-scale Method A vs 1km-grid ground truth).

This empirically tests the exact identity Bias = -n * Cov(p, h) that
governs count-based zonal aggregation (MAUP bias direction/magnitude).
"""
import numpy as np
from read_points import read_shp_points, read_dbf

HEAT_X0, HEAT_Y0, HEAT_CS = 746403.5065026443, 2068142.6506664562, 1046.7390550674

# ---------------------------------------------------------------------
# 1. Load points (coords + attributes)
# ---------------------------------------------------------------------
xs, ys = read_shp_points("point_data.shp")
fields, records = read_dbf("point_data.dbf")
assert len(records) == len(xs)

sigungu_full = np.array([r['SIGUNGU_NM'] for r in records])
pop30 = np.array([r['KU_30'] if r['KU_30'] is not None else np.nan for r in records])
pop60 = np.array([r['KU_60'] if r['KU_60'] is not None else np.nan for r in records])

sido = np.array([s.split(' ', 1)[0] for s in sigungu_full])

print("n points:", len(xs))
print("unique sido:", sorted(set(sido)))

# ---------------------------------------------------------------------
# 2. Load heatdays grids (previously decoded + cached as .npy)
# ---------------------------------------------------------------------
heat30 = np.load("../heat2030.npy")
heat60 = np.load("../heat2060.npy")
Hh, Wh = heat30.shape
print("heat grid shape:", heat30.shape)

heat30_mask = (heat30 > -1e30) & (heat30 < 1e6) & np.isfinite(heat30)
heat60_mask = (heat60 > -1e30) & (heat60 < 1e6) & np.isfinite(heat60)

# nearest-neighbor lookup: which heat cell does each point fall into
hc = np.floor((xs - HEAT_X0) / HEAT_CS).astype(int)
hr = np.floor((HEAT_Y0 - ys) / HEAT_CS).astype(int)
in_bounds = (hc >= 0) & (hc < Wh) & (hr >= 0) & (hr < Hh)

hc_c = np.clip(hc, 0, Wh - 1)
hr_c = np.clip(hr, 0, Hh - 1)

h30_pt = np.full(len(xs), np.nan)
h60_pt = np.full(len(xs), np.nan)
valid30 = in_bounds & heat30_mask[hr_c, hc_c]
valid60 = in_bounds & heat60_mask[hr_c, hc_c]
h30_pt[valid30] = heat30[hr_c[valid30], hc_c[valid30]]
h60_pt[valid60] = heat60[hr_c[valid60], hc_c[valid60]]

print("points with valid heat30:", valid30.sum(), "/", len(xs))
print("points with valid heat60:", valid60.sum(), "/", len(xs))

# ---------------------------------------------------------------------
# 3. Per-province Cov(p,h) and Pearson r, for 2030 and 2060
# ---------------------------------------------------------------------
KOR_TO_EN = {
    "강원도": "Gangwon-do", "강원특별자치도": "Gangwon-do",
    "경기도": "Gyeonggi-do",
    "경상남도": "Gyeongsangnam-do",
    "경상북도": "Gyeongsangbuk-do",
    "광주광역시": "Gwangju",
    "대구광역시": "Daegu",
    "대전광역시": "Daejeon",
    "부산광역시": "Busan",
    "서울특별시": "Seoul",
    "세종특별시": "Sejong", "세종특별자치시": "Sejong",
    "울산광역시": "Ulsan",
    "인천광역시": "Incheon",
    "전라남도": "Jeollanam-do",
    "전라북도": "Jeollabuk-do",
    "제주도": "Jeju-do", "제주특별자치도": "Jeju-do",
    "충청남도": "Chungcheongnam-do",
    "충청북도": "Chungcheongbuk-do",
}

results = []
for prov in sorted(set(sido)):
    m30 = (sido == prov) & valid30 & np.isfinite(pop30)
    m60 = (sido == prov) & valid60 & np.isfinite(pop60)

    n30, n60 = m30.sum(), m60.sum()
    if n30 < 3 or n60 < 3:
        continue

    p30v, h30v = pop30[m30], h30_pt[m30]
    p60v, h60v = pop60[m60], h60_pt[m60]

    cov30 = np.cov(p30v, h30v, ddof=1)[0, 1]
    cov60 = np.cov(p60v, h60v, ddof=1)[0, 1]
    r30 = np.corrcoef(p30v, h30v)[0, 1]
    r60 = np.corrcoef(p60v, h60v)[0, 1]

    results.append(dict(
        sido=prov, sido_en=KOR_TO_EN.get(prov, prov),
        n30=int(n30), n60=int(n60),
        cov30=cov30, cov60=cov60, r30=r30, r60=r60,
        pop30_sum=float(np.nansum(p30v)), pop60_sum=float(np.nansum(p60v)),
    ))

import json
with open("province_covariance.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n{'Province':<14} {'n30':>7} {'Cov30':>14} {'r30':>7}   {'n60':>7} {'Cov60':>14} {'r60':>7}")
for r in results:
    print(f"{r['sido']:<14} {r['n30']:>7} {r['cov30']:>14.4f} {r['r30']:>7.3f}   "
          f"{r['n60']:>7} {r['cov60']:>14.4f} {r['r60']:>7.3f}   ({r['sido_en']})")

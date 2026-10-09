import numpy as np

# --- population grids (642x610, 1000m cells) ---
pop30 = np.load('pop2030.npy')
pop60 = np.load('pop2060.npy')
pop30_mask = (pop30 > -1e30) & (pop30 < 1e15) & np.isfinite(pop30)
pop60_mask = (pop60 > -1e30) & (pop60 < 1e15) & np.isfinite(pop60)

# pop tfw: cellsize 1000, origin (upper-left corner) x=746611.0313, y=2067943.9535
POP_X0, POP_Y0, POP_CS = 746611.0313, 2067943.9535, 1000.0
H, W = pop30.shape  # 610, 642

# --- heatdays grids (614x583? actually shape (583,614), 1046.739... m cells) ---
heat30 = np.load('heat2030.npy')
heat60 = np.load('heat2060.npy')
HEAT_X0, HEAT_Y0, HEAT_CS = 746403.5065026443, 2068142.6506664562, 1046.7390550674
Hh, Wh = heat30.shape  # 583, 614

heat30_mask = (heat30 > -1e30) & (heat30 < 1e6) & np.isfinite(heat30)
heat60_mask = (heat60 > -1e30) & (heat60 < 1e6) & np.isfinite(heat60)

# build resampled heatdays onto population grid via nearest-neighbor (same method validated previously)
rows = np.arange(H)
cols = np.arange(W)
cc, rr = np.meshgrid(cols, rows)
x_center = POP_X0 + (cc + 0.5) * POP_CS
y_center = POP_Y0 - (rr + 0.5) * POP_CS

hc = np.floor((x_center - HEAT_X0) / HEAT_CS).astype(int)
hr = np.floor((HEAT_Y0 - y_center) / HEAT_CS).astype(int)

valid_idx = (hc >= 0) & (hc < Wh) & (hr >= 0) & (hr < Hh)

heat30_rs = np.full((H, W), np.nan)
heat60_rs = np.full((H, W), np.nan)
hc_c = np.clip(hc, 0, Wh - 1)
hr_c = np.clip(hr, 0, Hh - 1)

h30_valid_grid = heat30_mask[hr_c, hc_c] & valid_idx
h60_valid_grid = heat60_mask[hr_c, hc_c] & valid_idx

heat30_rs[h30_valid_grid] = heat30[hr_c[h30_valid_grid], hc_c[h30_valid_grid]]
heat60_rs[h60_valid_grid] = heat60[hr_c[h60_valid_grid], hc_c[h60_valid_grid]]

# final valid mask: population valid (both years) AND heatdays resampled valid (both years)
final_mask = pop30_mask & pop60_mask & np.isfinite(heat30_rs) & np.isfinite(heat60_rs)
print("valid grid cells:", final_mask.sum())

P30 = pop30[final_mask]
P60 = pop60[final_mask]
H30 = heat30_rs[final_mask]
H60 = heat60_rs[final_mask]

dP = P60 - P30
dH = H60 - H30

climate = (P30 * dH).sum()
population = (H30 * dP).sum()
interaction = (dP * dH).sum()
total = climate + population + interaction

E30 = (P30 * H30).sum()
E60 = (P60 * H60).sum()
print("E30 sum:", E30, "E60 sum:", E60, "actual delta:", E60 - E30)
print("Climate effect:", climate)
print("Population effect:", population)
print("Interaction effect:", interaction)
print("Sum of 3 effects (check):", total)

np.savez('grid_level_arrays.npz', P30=P30, P60=P60, H30=H30, H60=H60,
         final_mask=final_mask, heat30_rs=heat30_rs, heat60_rs=heat60_rs)

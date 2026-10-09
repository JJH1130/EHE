import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

df = pd.read_csv("merged_full.csv")

fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=300)

# palette: two-hue categorical (2030 vs 2060), colorblind-safe pair
c30 = "#4C72B0"   # blue
c60 = "#C44E52"   # red

x30, y30 = df["pred_bias_2030"], df["bias_2030"]
x60, y60 = df["pred_bias_2060"], df["bias_2060"]

ax.scatter(x30, y30, s=70, color=c30, edgecolor="white", linewidth=0.8, label="2030", zorder=3)
ax.scatter(x60, y60, s=70, color=c60, edgecolor="white", linewidth=0.8, label="2060", marker="^", zorder=3)

# 1:1 reference line
lims = [min(x30.min(), x60.min(), y30.min(), y60.min()) - 4,
        max(x30.max(), x60.max(), y30.max(), y60.max()) + 4]
ax.plot(lims, lims, linestyle="--", linewidth=1.2, color="#888888", zorder=1, label="1:1 (theoretical)")
ax.set_xlim(lims); ax.set_ylim(lims)

# direct labels for each province (use 2030 point); manual offsets to dodge
# the crowded cluster around x=-30..-35
LABEL_OFFSETS = {
    "Gangwon-do": (6, 4),
    "Gyeonggi-do": (6, -12),
    "Gyeongsangnam-do": (6, 4),
    "Gyeongsangbuk-do": (-8, -14),
    "Jeollanam-do": (6, 4),
    "Jeollabuk-do": (6, 4),
    "Jeju-do": (6, 4),
    "Chungcheongnam-do": (6, 6),
    "Chungcheongbuk-do": (8, 8),
}
for _, row in df.iterrows():
    dx, dy = LABEL_OFFSETS.get(row["sido_en"], (5, 4))
    ha = "right" if dx < 0 else "left"
    ax.annotate(row["sido_en"], (row["pred_bias_2030"], row["bias_2030"]),
                xytext=(dx, dy), textcoords="offset points", fontsize=8.5,
                color="#333333", ha=ha)

# regression fit stats (pooled 2030+2060)
xall = pd.concat([x30, x60]); yall = pd.concat([y30, y60])
r, p = stats.pearsonr(xall, yall)
r2 = r ** 2

ax.text(0.03, 0.97, f"Pearson r = {r:.3f}\nR² = {r2:.3f}\np < 0.001",
        transform=ax.transAxes, fontsize=10.5, va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cccccc"))

ax.set_xlabel("Theoretical bias, predicted from grid-cell Cov(population, heatdays)\n"
              "$-\\mathrm{Cov}(p,h)\\,/\\,(\\bar p \\bar h + \\mathrm{Cov}(p,h)) \\times 100$  (%)", fontsize=10)
ax.set_ylabel("Observed provincial-scale relative bias, Method A vs. 1 km grid (%)", fontsize=10)
ax.set_title("Grid-cell population–heat covariance predicts MAUP bias direction and magnitude\n"
              "(9 provinces, 2030 & 2060)", fontsize=11.5, fontweight="bold", pad=12)

ax.axhline(0, color="#dddddd", linewidth=0.8, zorder=0)
ax.axvline(0, color="#dddddd", linewidth=0.8, zorder=0)
ax.grid(True, linestyle=":", alpha=0.4)

ax.legend(loc="lower right", fontsize=9.5, frameon=True)

plt.tight_layout()
plt.savefig("covariance_bias_scatter.png", dpi=300, bbox_inches="tight")
plt.savefig("covariance_bias_scatter.pdf", bbox_inches="tight")
print("saved")
print(f"pooled r={r:.4f}, R2={r2:.4f}, p={p:.2e}")

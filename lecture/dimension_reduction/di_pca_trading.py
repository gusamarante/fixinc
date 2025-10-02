from utils import figure_path, BLUE, RED, GREEN
from data.readers import raw_di, di_curve
from scipy.interpolate import interp1d
from matplotlib.pylab import Slider
import matplotlib.pyplot as plt
from fixinc import CurvePCA
import pandas as pd
import numpy as np

size = 5

# DATA - Principal Components
curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)
pca = CurvePCA(curve, n_components=3)
loadings = pca.loadings.copy()
loadings.index *= 21


# DATA - Get the January maturities of the lastest available curve
di = raw_di()
cond_latest_date = di["reference_date"] == di["reference_date"].max()
cond_fmat = di["contract"].str[0] == "F"
di = di[cond_latest_date & cond_fmat]

# Filter volume AFTER date and maturities are selected
cond_volume = di["volume"] >= di["volume"].quantile(0.3)
di = di[cond_volume].sort_values(by="du")

for i in range(1, 4):
    fun = interp1d(loadings.index.values, loadings[f'PC {i}'].values)
    di[f"PCDV {i}"] = di['du'].apply(fun) * di['dv01']

di = di.set_index("du")

# ======================================
# ===== Charts - Factor timeseries =====
# ======================================
# plt.figure(figsize=(size * (16 / 7.3), size))
#
# ax = plt.subplot2grid((1, 1), (0, 0))
# ax.plot(di.index/252, di[["PCDV 1", "PCDV 2", "PCDV 3"]], label=["PCDV 1", "PCDV 2", "PCDV 3"], linewidth=2)
# ax.axhline(0, color='black', linewidth=0.5)
# ax.set_title("PCA-DV01 for DI Futures (January Maturities)")
# ax.set_xlabel("Years to Maturity")
# ax.tick_params(rotation=90, axis='x')
# ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
# ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
# ax.legend(frameon=True, loc='lower left')
#
#
# plt.tight_layout()
# plt.savefig(figure_path.joinpath("Dimensionality Reduction - DI PCDV01.pdf"))
# plt.show()
# plt.close()


# Seleção de contratos
c1, c2, c3 = di.index[1], di["PCDV 3"].idxmax(), di.index[-2]

A = di.loc[[c1, c2, c3], ["PCDV 1", "PCDV 2", "PCDV 3"]].T
B = np.array([0, 0, 1000])
q = pd.Series(data=np.linalg.inv(A) @ B, index=A.columns)

print(A)
print(q)

# Trade
start_pc1, start_pc2, start_pc3 = pca.factors.values[-1, :]
max_pcs = pca.factors.max()
min_pcs = pca.factors.min()

def pus(pc1, pc2, pc3):
    new_curve = pca.reconstruct(np.array([[pc1, pc2, pc3]]))  # TODO allow for 1d-arrays
    new_curve = new_curve.loc[0]
    new_curve.index *= 21
    interp = interp1d(new_curve.index, new_curve.values)
    du = np.array([c1, c2, c3])
    y = interp(du)
    return 100_000 / (1 + y)**(du/252)


start_pus = pus(start_pc1, start_pc2, start_pc3)

def pnl(pc1, pc2, pc3):
    new_pus = pus(pc1, pc2, pc3)
    cpnl = new_pus - start_pus
    return cpnl.dot(q)


# =================
# ===== CHART =====
# =================
fig = plt.figure(figsize=(size * (16 / 7.3), size))

# Curves
ax = plt.subplot2grid((1, 2), (0, 0))
ax.scatter([0], [0], color=BLUE)
ax.axvline(0, color="black", lw=0.5)
ax.axhline(0, color="black", lw=0.5)
ax.set_title("DI Curve PCA Trading PnL")
ax.set_ylabel("PnL")
ax.set_xlabel("Total Change in PCs")
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)

# Sliders
ax_pc1 = plt.subplot2grid((3, 2), (0, 1))
slide_pc1 = Slider(
    ax=ax_pc1,
    label=r"$PC_1$",
    valmin=min_pcs["PC 1"],
    valinit=start_pc1,
    valmax=max_pcs["PC 1"],
    valstep=(max_pcs["PC 1"] - min_pcs["PC 1"]) / 100,
)

ax_pc2 = plt.subplot2grid((3, 2), (1, 1))
slide_pc2 = Slider(
    ax=ax_pc2,
    label=r"$PC_2$",
    valmin=min_pcs["PC 2"],
    valinit=start_pc2,
    valmax=max_pcs["PC 2"],
    valstep=(max_pcs["PC 2"] - min_pcs["PC 2"]) / 100,
)

ax_pc3 = plt.subplot2grid((3, 2), (2, 1))
slide_pc3 = Slider(
    ax=ax_pc3,
    label=r"$PC_3$",
    valmin=min_pcs["PC 3"],
    valinit=start_pc3,
    valmax=max_pcs["PC 3"],
    valstep=(max_pcs["PC 3"] - min_pcs["PC 3"]) / 100,
)

def update_pc1(val):
    new_pc1 = slide_pc1.val
    new_pc2 = slide_pc2.val
    new_pc3 = slide_pc3.val
    pc_change = (new_pc1 - start_pc1) + (new_pc2 - start_pc2) + (new_pc3 - start_pc3)
    ax.scatter(pc_change, pnl(new_pc1, new_pc2, new_pc3), color=BLUE)
    # ax.relim()
    # ax.autoscale_view()
    fig.canvas.draw_idle()

def update_pc2(val):
    new_pc1 = slide_pc1.val
    new_pc2 = slide_pc2.val
    new_pc3 = slide_pc3.val
    pc_change = (new_pc1 - start_pc1) + (new_pc2 - start_pc2) + (new_pc3 - start_pc3)
    ax.scatter(pc_change, pnl(new_pc1, new_pc2, new_pc3), color=RED)
    # ax.relim()
    # ax.autoscale_view()
    fig.canvas.draw_idle()

def update_pc3(val):
    new_pc1 = slide_pc1.val
    new_pc2 = slide_pc2.val
    new_pc3 = slide_pc3.val
    pc_change = (new_pc1 - start_pc1) + (new_pc2 - start_pc2) + (new_pc3 - start_pc3)
    ax.scatter(pc_change, pnl(new_pc1, new_pc2, new_pc3), color=GREEN)
    # ax.relim()
    # ax.autoscale_view()
    fig.canvas.draw_idle()


slide_pc1.on_changed(update_pc1)
slide_pc2.on_changed(update_pc2)
slide_pc3.on_changed(update_pc3)

plt.tight_layout()
plt.show()

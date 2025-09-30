"""
Widget to play with PCA on the DI futures curve
"""
import numpy as np

from data.readers import di_curve
from fixinc import CurvePCA
import matplotlib.pyplot as plt
from utils import BLUE, RED
from matplotlib.pylab import Slider

size = 5

curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)

pca = CurvePCA(curve, n_components=4)
start_pc1, start_pc2, start_pc3, start_pc4 = pca.factors.values[-1, :]
max_pcs = pca.factors.max()
min_pcs = pca.factors.min()

# Functions
def recon(pc1, pc2, pc3, pc4):
    return pca.reconstruct(np.array([pc1, pc2, pc3, pc4]))


# =================
# ===== CHART =====
# =================
fig = plt.figure(figsize=(size * (16 / 7.3), size))

# Curves
ax = plt.subplot2grid((1, 2), (0, 0))
ax.plot(curve.iloc[-1], label="Latest", color=BLUE, lw=2)
c_recon, = ax.plot(recon(start_pc1, start_pc2, start_pc3, start_pc4), label="Reconstructed", color=RED, lw=2)
ax.set_title("DI Curve PCA Reconstruction")
ax.set_ylabel("Yields (%)")
ax.set_xlabel("Maturity (Months)")
ax.set_ylim(0.08, 0.18)
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best')

# Sliders
ax_pc1 = plt.subplot2grid((4, 2), (0, 1))
slide_pc1 = Slider(
    ax=ax_pc1,
    label=r"$PC_1$",
    valmin=min_pcs["PC 1"],
    valinit=start_pc1,
    valmax=max_pcs["PC 1"],
    valstep=(max_pcs["PC 1"] - min_pcs["PC 1"]) / 100,
)

ax_pc2 = plt.subplot2grid((4, 2), (1, 1))
slide_pc2 = Slider(
    ax=ax_pc2,
    label=r"$PC_2$",
    valmin=min_pcs["PC 2"],
    valinit=start_pc2,
    valmax=max_pcs["PC 2"],
    valstep=(max_pcs["PC 2"] - min_pcs["PC 2"]) / 100,
)

ax_pc3 = plt.subplot2grid((4, 2), (2, 1))
slide_pc3 = Slider(
    ax=ax_pc3,
    label=r"$PC_3$",
    valmin=min_pcs["PC 3"],
    valinit=start_pc3,
    valmax=max_pcs["PC 3"],
    valstep=(max_pcs["PC 3"] - min_pcs["PC 3"]) / 100,
)

ax_pc4 = plt.subplot2grid((4, 2), (3, 1))
slide_pc4 = Slider(
    ax=ax_pc4,
    label=r"$PC_4$",
    valmin=min_pcs["PC 4"],
    valinit=start_pc4,
    valmax=max_pcs["PC 4"],
    valstep=(max_pcs["PC 4"] - min_pcs["PC 4"]) / 100,
)

def update(val):
    new_pc1 = slide_pc1.val
    new_pc2 = slide_pc2.val
    new_pc3 = slide_pc3.val
    new_pc4 = slide_pc4.val
    c_recon.set_ydata(recon(new_pc1, new_pc2, new_pc3, new_pc4))

    # ax.relim()
    # ax.autoscale_view()
    fig.canvas.draw_idle()

slide_pc1.on_changed(update)
slide_pc2.on_changed(update)
slide_pc3.on_changed(update)
slide_pc4.on_changed(update)

plt.tight_layout()
plt.show()

from fixinc import nss
import matplotlib.pyplot as plt
from utils import BLUE, RED
from matplotlib.pylab import Slider
import numpy as np


# DI Curve from 2025-10-21
b1 = 0.127
b2 = -0.016
b3 = -0.012
b4 = -0.022

l1 = 1.994
l2 = 0.771

t_range = np.arange(15 * 252 + 1) / 252


# =================
# ===== CHART =====
# =================
size = 6
fig = plt.figure(figsize=(size * (16 / 7.3), size))

# Curves
ax = plt.subplot2grid((1, 2), (0, 0))
ax.plot(
    t_range,
    [nss(t, b1, b2, b3, b4, l1, l2) for t in t_range],
    label="2025-10-21",
    color=BLUE,
)
c_recon, = ax.plot(
    t_range,
    [nss(t, b1, b2, b3, b4, l1, l2) for t in t_range],
    label="Reconstructed",
    color=RED,
)
ax.set_title("NSS ANBIMA Nominal Curve")
ax.set_ylabel("Nominal Zero Yields (%)")
ax.set_xlabel("Maturity (Years)")
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best')

# Sliders
ax_b1 = plt.subplot2grid((6, 2), (0, 1))
slide_b1 = Slider(
    ax=ax_b1,
    label=r"$\beta_1$",
    valmin=0.05,
    valinit=b1,
    valmax=0.25,
    valstep=0.001,
)

ax_b2 = plt.subplot2grid((6, 2), (1, 1))
slide_b2 = Slider(
    ax=ax_b2,
    label=r"$\beta_2$",
    valmin=-0.08,
    valinit=b2,
    valmax=0.03,
    valstep=0.001,
)

ax_b3 = plt.subplot2grid((6, 2), (2, 1))
slide_b3 = Slider(
    ax=ax_b3,
    label=r"$\beta_3$",
    valmin=-0.2,
    valinit=b3,
    valmax=0.12,
    valstep=0.001,
)

ax_b4 = plt.subplot2grid((6, 2), (3, 1))
slide_b4 = Slider(
    ax=ax_b4,
    label=r"$\beta_4$",
    valmin=-0.22,
    valinit=b4,
    valmax=0.2,
    valstep=0.001,
)

ax_l1 = plt.subplot2grid((6, 2), (4, 1))
slide_l1 = Slider(
    ax=ax_l1,
    label=r"$\lambda_1$",
    valmin=0,
    valinit=l1,
    valmax=10,
    valstep=0.001,
)

ax_l2 = plt.subplot2grid((6, 2), (5, 1))
slide_l2 = Slider(
    ax=ax_l2,
    label=r"$\lambda_2$",
    valmin=0,
    valinit=l2,
    valmax=4,
    valstep=0.001,
)

def update(val):
    nb1 = slide_b1.val
    nb2 = slide_b2.val
    nb3 = slide_b3.val
    nb4 = slide_b4.val
    nl1 = slide_l1.val
    nl2 = slide_l2.val

    c_recon.set_ydata([nss(t, nb1, nb2, nb3, nb4, nl1, nl2) for t in t_range])

    # ax.relim()
    # ax.autoscale_view()
    fig.canvas.draw_idle()


slide_b1.on_changed(update)
slide_b2.on_changed(update)
slide_b3.on_changed(update)
slide_b4.on_changed(update)
slide_l1.on_changed(update)
slide_l2.on_changed(update)

plt.tight_layout()
plt.show()






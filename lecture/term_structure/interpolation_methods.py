from utils import BLUE, RED, GREEN
import matplotlib.pyplot as plt
from utils import figure_path
from fixinc import ZeroCurve
import pandas as pd
import numpy as np


zc_data = pd.DataFrame(
    data={
        1: 0.0526,
        2: 0.0770,
        3: 0.1236,
    },
    index=[pd.to_datetime("2025-01-01")]
)
zc = ZeroCurve(
    zc_data,
    yc="compound",
)


# interp = zc.interpolate(
#     ref_date="2025-01-01",
#     mat=2.5,
#     # method="linear",
#     # method="flat-forward",
#     method="cubic spline",
# )
# print(interp)

mat_range = np.arange(1, 3.01, 0.01)
zc_all_methods = pd.DataFrame(
    {
        "Linear": [zc.interpolate("2025-01-01", t, method="linear") for t in mat_range],
        "Flat Forward": [zc.interpolate("2025-01-01", t, method="flat forward") for t in mat_range],
        "Cubic Spline": [zc.interpolate("2025-01-01", t, method="cubic spline") for t in mat_range],
    },
    index=mat_range,
)

fras = pd.DataFrame(columns=zc_all_methods.columns)
for t2, t1 in zip(zc_all_methods.index[1:], zc_all_methods.index[:-1]):
    fras.loc[t2] = (((1 + zc_all_methods.loc[t2]) ** t2) / ((1 + zc_all_methods.loc[t1]) ** t1)) ** (1 / (t2 - t1)) - 1

# =================
# ===== CHART =====
# =================
size = 6

fig = plt.figure(figsize=(size * (16 / 7.3), size))

# Curves
ax = plt.subplot2grid((1, 2), (0, 0))
ax.plot(
    zc_all_methods["Linear"],
    label="Linear",
    color=BLUE,
    lw=2,
)
ax.plot(
    zc_all_methods["Flat Forward"],
    label="Flat Forward",
    color=RED,
    lw=2,
)
ax.plot(
    zc_all_methods["Cubic Spline"],
    label="Cubic Spline",
    color=GREEN,
    lw=2,
)

ax.set_title("Interpolated Zero Curve")
ax.set_ylabel("Yields")
ax.set_xlabel("Maturity (Years)")
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best')


# Forward Curve
ax = plt.subplot2grid((1, 2), (0, 1))
ax.plot(
    fras["Linear"],
    label="Linear",
    color=BLUE,
    lw=2,
)
ax.plot(
    fras["Flat Forward"],
    label="Flat Forward",
    color=RED,
    lw=2,
)
ax.plot(
    fras["Cubic Spline"],
    label="Cubic Spline",
    color=GREEN,
    lw=2,
)

ax.set_title("FRAs of Interpolated Zero Curve")
ax.set_ylabel("Yields")
ax.set_xlabel("Maturity (Years)")
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best')

plt.savefig(figure_path.joinpath("TSIR - Interpolation Methods Example.pdf"))
plt.tight_layout()
plt.show()

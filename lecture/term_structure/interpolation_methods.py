import matplotlib.pyplot as plt
from fixinc import ZeroCurve
from utils import BLUE, RED, GREEN
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


# =================
# ===== CHART =====
# =================
mat_range = np.arange(1, 3, 0.01)
size = 6
fig = plt.figure(figsize=(size * (16 / 7.3), size))

# Curves
ax = plt.subplot2grid((1, 1), (0, 0))
ax.plot(
    mat_range,
    [zc.interpolate("2025-01-01", t, method="linear") for t in mat_range],
    label="Linear",
    color=BLUE,
    lw=2,
)
ax.plot(
    mat_range,
    [zc.interpolate("2025-01-01", t, method="flat forward") for t in mat_range],
    label="Flat Forward",
    color=RED,
    lw=2,
)
ax.plot(
    mat_range,
    [zc.interpolate("2025-01-01", t, method="cubic spline") for t in mat_range],
    label="Cubic Spline",
    color=GREEN,
    lw=2,
)

ax.set_title("Zero Curve Interpolation Methods")
ax.set_ylabel("Yields")
ax.set_xlabel("Maturity (Years)")
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best')

plt.tight_layout()
plt.show()

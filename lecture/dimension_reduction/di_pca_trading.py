# TODO widget with "draw and persist" sliders for PnL

from utils import figure_path, BLUE, RED, GREEN
from data.readers import raw_di, di_curve
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from fixinc import CurvePCA
import numpy as np
import pandas as pd

size = 5

# DATA - Principal Components
curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)
pca = CurvePCA(curve, n_components=3)
loadings = pca.loadings.copy()
loadings.index = loadings.index * 21


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


c1, c2, c3 = di.index[1], di["PCDV 3"].idxmax(), di.index[-2]

A = di.loc[[c1, c2, c3], ["PCDV 1", "PCDV 2", "PCDV 3"]].T
B = np.array([0, 0, 1000])
q = pd.Series(data=np.linalg.inv(A) @ B, index=A.columns)

print(A)
print(q)
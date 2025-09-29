"""
PCA applied to the DI Curve
"""
from data.readers import di_curve
from fixinc import CurvePCA
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from utils import figure_path, BLUE, RED

size = 5

curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)

pca = CurvePCA(curve, n_components=4)


# =====================================
# ===== Charts - Curve timeseries =====
# =====================================
df2plot = curve[[12 * a for a in range(1, 11)]] * 100
df2plot.columns = [f"{a}y" for a in range(1, 11)]


plt.figure(figsize=(size * (16 / 7.3), size))
ax = plt.subplot2grid((1, 1), (0, 0))
ax.plot(df2plot, label=df2plot.columns)
ax.set_title("DI Curve Yields")
ax.set_ylabel("Yields (%)")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best', ncol=2)

plt.tight_layout()

plt.savefig(figure_path.joinpath("Dimensionality Reduction - DI PCA Yields.pdf"))
plt.show()
plt.close()


# ======================================
# ===== Charts - Factor timeseries =====
# ======================================
plt.figure(figsize=(size * (16 / 7.3), size))
ax = plt.subplot2grid((1, 1), (0, 0))
ax.plot(pca.factors, label=pca.factors.columns)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title("DI Curve Principal Components")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best')

plt.tight_layout()

plt.savefig(figure_path.joinpath("Dimensionality Reduction - DI PCA Factor.pdf"))
plt.show()
plt.close()


# =============================
# ===== Charts - Loadings =====
# =============================
plt.figure(figsize=(size * (16 / 7.3), size))
ax = plt.subplot2grid((1, 1), (0, 0))
ax.plot(pca.loadings, label=pca.loadings.columns)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title("DI Curve Loadings")
ax.set_ylabel("Loadings")
ax.set_xlabel("Maturity (Months)")
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best')

plt.tight_layout()

plt.savefig(figure_path.joinpath("Dimensionality Reduction - DI PCA Loadings.pdf"))
plt.show()
plt.close()


# =======================================
# ===== Charts - Explained Variance =====
# =======================================
plt.figure(figsize=(size * (16 / 7.3), size))
ax = plt.subplot2grid((1, 1), (0, 0))
bar_container = ax.bar(pca.exp_var_ration.index, pca.exp_var_ration.values * 100, color=BLUE, label="Individual")
ax.plot(pca.exp_var_ration.index, pca.exp_var_ration.values.cumsum() * 100, color=RED, label="Cumulative", lw=3)
ax.bar_label(bar_container, fmt=lambda x: f'{x:.2f}')
ax.set_title("DI Curve - Explained Variance")
ax.set_ylabel("Explained Variance (%)")
ax.set_xlabel("Principal Component")
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)

ax.legend(frameon=True, loc='best')

plt.tight_layout()

plt.savefig(figure_path.joinpath("Dimensionality Reduction - DI PCA Explained Variance.pdf"))
plt.show()
plt.close()


# TODO gráfico da variância explicada
"""
Estimates a VAR(1) model for the PCA factors of the DI curve and simulates
future curves.
"""
import pandas as pd
from data.readers import di_curve
from fixinc import CurvePCA
import matplotlib.pyplot as plt
from utils import figure_path, BLUE, RED
from statsmodels.tsa.vector_ar.var_model import VAR
from tqdm import tqdm

size = 5
n_simul = 1000

curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)
curve = curve.resample("M").last()

pca = CurvePCA(curve, n_components=3)

var = VAR(endog=pca.factors)
res = var.fit(1)
print(res.summary())


# TODO this could go inside the CurvePCA class
sim_curves = pd.DataFrame(columns=curve.columns)
for i in tqdm(range(n_simul)):
    sim = res.simulate_var(steps=2, initial_values=pca.factors.values[-1:])
    aux_sim = pca.reconstruct(sim[-1])
    sim_curves.loc[i] = aux_sim


# =================================
# ===== Charts - Curve Ranges =====
# =================================
plt.figure(figsize=(size * (16 / 7.3), size))
ax = plt.subplot2grid((1, 1), (0, 0))

ax.plot(curve.iloc[-1], label="Latest", color=BLUE, lw=2)
ax.plot(sim_curves.quantile(0.5), label="Median", color=RED, lw=2, ls='--')
ax.fill_between(
    x=curve.columns,
    y1=sim_curves.quantile(0.1),
    y2=sim_curves.quantile(0.9),
    color=RED,
    alpha=0.3,
    label="10-90%",
    edgecolor=None,
)
ax.fill_between(
    x=curve.columns,
    y1=sim_curves.quantile(0.01),
    y2=sim_curves.quantile(0.99),
    color=RED,
    alpha=0.1,
    label="1-99%",
    edgecolor=None,
)

ax.set_title("DI Curve PCA Simulation - 1 Month Ahead")
ax.set_ylabel("Yields (%)")
ax.set_xlabel("Maturity (Months)")
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='best', ncol=2)

plt.tight_layout()

plt.savefig(figure_path.joinpath("Dimensionality Reduction - DI PCA Simulation.pdf"))
plt.show()
plt.close()
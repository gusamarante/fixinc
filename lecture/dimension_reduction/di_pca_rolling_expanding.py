from utils import figure_path, BLUE, RED, GREEN
from data.readers import di_curve
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from fixinc import CurvePCA
from tqdm import tqdm
import pandas as pd


size = 6
n_simul = 1000


curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)
curve = curve.resample("ME").last()

pca_full = CurvePCA(curve, n_components=4)
df_expanding = pd.DataFrame(columns=pca_full.factors.columns)
df_rolling = pd.DataFrame(columns=pca_full.factors.columns)

dates2loop = curve.index[12:]
for d in tqdm(dates2loop):
    aux_curve = curve.loc[:d]
    pca_exp = CurvePCA(aux_curve, n_components=4)
    df_expanding.loc[d] = pca_exp.factors.iloc[-1]

    aux_curve = aux_curve.tail(12 * 5)
    pca_roll = CurvePCA(aux_curve, n_components=4)
    df_rolling.loc[d] = pca_roll.factors.iloc[-1]


# ======================================
# ===== Charts - Factor timeseries =====
# ======================================
plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((2, 2), (0, 0))
ax.plot(pca_full.factors["PC 1"], label="Full Sample", color=BLUE, linewidth=2)
ax.plot(df_expanding["PC 1"], label="Expanding", color=GREEN, linewidth=2)
ax.plot(df_rolling["PC 1"], label="Rolling 5y", color=RED, linewidth=2)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title("PC 1")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='lower left')

ax = plt.subplot2grid((2, 2), (0, 1))
ax.plot(pca_full.factors["PC 2"], label="Full Sample", color=BLUE, linewidth=2)
ax.plot(df_expanding["PC 2"], label="Expanding", color=GREEN, linewidth=2)
ax.plot(df_rolling["PC 2"], label="Rolling 5y", color=RED, linewidth=2)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title("PC 2")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='lower left')

ax = plt.subplot2grid((2, 2), (1, 0))
ax.plot(pca_full.factors["PC 3"], label="Full Sample", color=BLUE, linewidth=2)
ax.plot(df_expanding["PC 3"], label="Expanding", color=GREEN, linewidth=2)
ax.plot(df_rolling["PC 3"], label="Rolling 5y", color=RED, linewidth=2)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title("PC 3")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='lower left')

ax = plt.subplot2grid((2, 2), (1, 1))
ax.plot(pca_full.factors["PC 4"], label="Full Sample", color=BLUE, linewidth=2)
ax.plot(df_expanding["PC 4"], label="Expanding", color=GREEN, linewidth=2)
ax.plot(df_rolling["PC 4"], label="Rolling 5y", color=RED, linewidth=2)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title("PC 4")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(rotation=90, axis='x')
ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
ax.legend(frameon=True, loc='lower left')

plt.tight_layout()
plt.savefig(figure_path.joinpath("Dimensionality Reduction - DI PCA Rolling Expanding.pdf"))
plt.show()
plt.close()

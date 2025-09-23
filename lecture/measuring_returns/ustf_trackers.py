from matplotlib.ticker import ScalarFormatter
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from data.readers import trackers_ustf
from utils import figure_path
import numpy as np


size = 5

df, _ = trackers_ustf()
vol = df.pct_change(1).ewm(com=252, min_periods=126).std() * np.sqrt(252)


# =================
# ===== Index =====
# =================
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))
ax.set_title("UST Futures Excess Return Index")
ax.plot(df, label=df.columns, lw=2)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("Index")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Measuring Returns - UST Futures Excess Return Indexes.pdf"))
plt.show()
plt.close()


# ================
# ===== Vols =====
# ================
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))
ax.set_title("UST Futures Index Volatilities")
ax.plot(vol, label=vol.columns, lw=2)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("Volatility")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Measuring Returns - UST Futures Excess Return Vol.pdf"))
plt.show()
plt.close()

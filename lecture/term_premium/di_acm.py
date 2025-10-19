from pyacm import NominalACM
from data.readers import di_curve
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import matplotlib.dates as mdates
from utils import figure_path


curve = di_curve()
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)

acm = NominalACM(curve)


# --- Chart - Yields ---
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 2), (0, 0))
mat = 24
ax.set_title("2-year yields")
ax.plot(curve[mat], label="Observed")
ax.plot(acm.rny[mat], label="Risk-Neutral")
# ax.axhline(0, color="black", lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

ax = plt.subplot2grid((1, 2), (0, 1), sharey=ax)
mat = 60
ax.set_title("5-year yields")
ax.plot(curve[mat], label="Observed")
ax.plot(acm.rny[mat], label="Risk-Neutral")
# ax.axhline(0, color="black", lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Term Premium - DI ACM Observed VS Risk Neutral.pdf"))
plt.show()
plt.close()


# --- Chart - Term Premium ---
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))
ax.set_title("ACM Term Premium DI Futures")
ax.plot(acm.tp[24], label="2-year")
ax.plot(acm.tp[60], label="5-year")
ax.axhline(0, color="black", lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Term Premium - DI ACM Term Premium.pdf"))
plt.show()
plt.close()


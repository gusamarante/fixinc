# TODO Compute
#  Money Carry
#  Breakeven
#  Academic
#  For timeseries and cross section

from data.readers import di_raw, di_curve
from fixinc.apis import SGS
from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from utils import figure_path, BLUE

data = di_raw()
curve = di_curve()

# Money Carry
mc_data = data[data["contract"] == "F28"].set_index("reference_date").sort_index()
cdi = SGS().fetch({12: "CDI"}, start_date=mc_data.index.min())["CDI"] / 100
partial_du = - mc_data["theoretical_price"] * np.log(1 + mc_data["rate"]) / 252
money_carry = - partial_du - (mc_data["theoretical_price"] * cdi).dropna()

# Breakeven
be_yield = - money_carry / mc_data["dv01"]

# --- Chart ---
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 2), (0, 0))
ax.set_title("Money Carry - F28")
ax.plot(money_carry, color=BLUE)
ax.axhline(0, color="black", lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("Carry in R$ per day")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")

ax = plt.subplot2grid((1, 2), (0, 1))
ax.set_title("Breakeven Yield - F28")
ax.plot(be_yield, color=BLUE)
ax.axhline(0, color="black", lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("Change in yield to break even")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")


plt.tight_layout()

plt.savefig(figure_path.joinpath("Characteristics - DI Money Carry and Yield Breakeven Timeseries.pdf"))
plt.show()
plt.close()


# --- Academic Carry 5y-1m ---
carry = ((((1 + curve["60m"]) ** 5) / ((1 + curve["59m"]) ** (59 / 12))) / (1 + cdi) - 1).dropna()


# --- Chart ---
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))
ax.set_title("Academic Carry - 5y/1m")
ax.plot(carry * 100, color=BLUE)
# ax.axhline(0, color="black", lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("Carry (%)")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Characteristics - DI Academic Carry Timeseries.pdf"))
plt.show()
plt.close()

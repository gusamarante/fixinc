from data.readers import cds_idx
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from utils import figure_path

df = cds_idx()

df = 100 * df / df.bfill().iloc[0]


# =================
# ===== Index =====
# =================
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))
ax.set_title("CDS Indices - Excess Return Index")
ax.plot(df, label=df.columns, lw=2)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("Index")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

plt.tight_layout()

plt.savefig(figure_path.joinpath("CDS Index - Excess Return Indexes.pdf"))
plt.show()
plt.close()
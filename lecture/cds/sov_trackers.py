from data.readers import cds_sov
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from utils import BLUE, figure_path, GREEN, RED

df = cds_sov()


# =================
# ===== Index =====
# =================
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))
ax.set_title("Sovereign CDS - Excess Return Index")
ax.plot(df['Brazil'], label="Brazil", color=BLUE, lw=2)
ax.plot(df['Mexico'], label="Mexico", color=RED, lw=2)
ax.plot(df['Italy'], label="Italy", color=GREEN, lw=2)
# TODO add more
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("Index")
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

plt.tight_layout()

plt.savefig(figure_path.joinpath("CDS - Excess Return Indexes.pdf"))
plt.show()
plt.close()
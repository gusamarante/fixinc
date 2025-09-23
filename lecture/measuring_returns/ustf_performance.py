from fixinc import Performance
from data.readers import trackers_ustf
import matplotlib.pyplot as plt
from utils import BLUE, figure_path
from plottable import ColDef, Table


size = 5


# Grab data and compute performance
df, dur = trackers_ustf()
df = df.drop("10y Note Ultra", axis=1)  # Small sample
dur = dur.drop("10y Note Ultra")
perf = Performance(df, skip_dd=True)


# =================
# ===== Chart =====
# =================
fig = plt.figure(figsize=(size * (16 / 7.3), size))


# Excess Returns VS Volatility
ax = plt.subplot2grid((1, 2), (0, 0))
ax.scatter(perf.table.loc["Vol"], perf.table.loc["Return"], color=BLUE)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.set_title("UST Futures")
ax.set_xlabel("Volatility")
ax.set_ylabel("Excess Return")

for val in perf.table.T[["Return", "Vol"]].iterrows():
    ax.annotate(
        text=val[0],
        xy=(
            val[1].loc["Vol"] + 0.002,
            val[1].loc["Return"],
        ),
    )


# Sharpe VS Duration
ax = plt.subplot2grid((1, 2), (0, 1))

ax.scatter(dur, perf.table.loc["Sharpe"], color=BLUE)
ax.axhline(0, color='black', lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.set_title("UST Futures")
ax.set_xlabel("Duration")
ax.set_ylabel("Sharpe Ratio")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Measuring Returns - USTF Performance.pdf"))
plt.show()
plt.close()


# =============================
# ===== Performance Table =====
# =============================
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))

df2plot = perf.table.copy().T
df2plot = df2plot.drop(["Start Date", "Sortino"], axis=1)
df2plot = df2plot.astype(float)
df2plot.index.name = "Duration"


tab = Table(
    df2plot,
    ax=ax,
    footer_divider=True,
    textprops={"fontsize": 12},
    column_definitions=[
        ColDef(name="Duration", textprops={"ha": "left", "weight": "bold"}),
        ColDef(name="Return", textprops={"ha": "center"}, formatter="{:.2%}"),
        ColDef(name="Vol", textprops={"ha": "center"}, formatter="{:.2%}"),
        ColDef(name="Sharpe", textprops={"ha": "center"}, formatter="{:.2f}"),
        ColDef(name="Skew", textprops={"ha": "center"}, formatter="{:.2f}"),
        ColDef(name="Kurt", textprops={"ha": "center"}, formatter="{:.2f}"),
        ColDef(name="Max DD", textprops={"ha": "center"}, formatter="{:.2%}"),
    ],
)

for col in range(tab.col_label_row.get_xrange()[1]):
    tab.col_label_row.cells[col].text.set_weight("bold")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Measuring Returns - USTF Performance Table.pdf"))
plt.show()
plt.close()

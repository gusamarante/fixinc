import pandas as pd
import matplotlib.pyplot as plt
from data.readers import di_curve, trackers_di1
import numpy as np
from utils import BLUE, RED, figure_path
from fixinc import Performance
from plottable import ColDef, Table


start_date = "2009-01-01"

# Grab Data
trackers = trackers_di1()
trackers.columns = trackers.columns.str.replace("DI ", "").str.replace("y", "").astype(float)

curve = di_curve()
curve.columns = curve.columns.str.replace("m", "").astype(float) / 12

mats = np.intersect1d(curve.columns, trackers.columns)

trackers = trackers[mats]
curve = curve[mats]

# True Returns
rets_true = trackers.pct_change(1)
rets_true = rets_true[rets_true.index >= start_date]
track_true = (1 + rets_true).cumprod()
track_true = 100 * track_true / track_true.iloc[0]

# Approximated returns
moddur = - curve.columns / (1 + curve)
rets_approx = curve.diff(1) * moddur
rets_approx = rets_approx[rets_approx.index >= start_date]
track_approx = (1 + rets_approx).cumprod()
track_approx = 100 * track_approx / track_approx.iloc[0]

# Same index
new_idx = rets_approx.index.intersection(rets_true.index)
rets_approx = rets_approx.reindex(new_idx)
rets_true = rets_true.reindex(new_idx)



# =================
# ===== Chart =====
# =================
x1, y1 = 0.02, 0.02
x2, y2 = 0.035, 0.035
width = x2 - x1
height = y2 - y1

size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 2), (0, 0))
ax.scatter(rets_approx[10.], rets_true[10.], color=BLUE, alpha=0.3, label="Daily Returns")
ax.axhline(0, color="black", lw=0.5)
ax.axvline(0, color="black", lw=0.5)
ax.axline((0, 0), slope=1, color=RED, lw=1, ls="--", label="45-degree line")
rect = plt.Rectangle((x1, y1), width, height, facecolor=RED, alpha=0.3)
ax.add_patch(rect)
ax.xaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
ax.set_title("DI 10y")
ax.set_xlabel("Duration-approximated returns")
ax.set_ylabel("Full-Valuation Returns")
ax.legend(frameon=True, loc="upper left")


ax = plt.subplot2grid((1, 2), (0, 1))
ax.scatter(rets_approx[10.], rets_true[10.], color=BLUE, alpha=0.3, label="Daily Returns")
ax.axhline(0, color="black", lw=0.5)
ax.axvline(0, color="black", lw=0.5)
ax.axline((0, 0), slope=1, color=RED, lw=1, ls="--", label="45-degree line")
ax.xaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
rect = plt.Rectangle((x1, y1), width, height, facecolor=RED, alpha=0.1)
ax.add_patch(rect)
ax.set(xlim=(x1, x2), ylim=(y1, y2))
ax.set_title("DI 10y (ZOOMED in the red square)")
ax.set_xlabel("Duration-approximated returns")
ax.set_ylabel("Full-Valuation Returns")
ax.legend(frameon=True, loc="upper left")

plt.tight_layout()
plt.savefig(figure_path.joinpath("Measuring Returns - DI Duration Approximated Scatter.pdf"))
plt.show()


# --- Performance ---
perf_true = Performance(track_true, skip_dd=True).table
perf_approx = Performance(track_approx, skip_dd=True).table


df_perf = pd.DataFrame(
    {
        "Return Approx": perf_approx.loc["Return"],
        "Return True": perf_true.loc["Return"],
        "Return Delta": perf_true.loc["Return"] - perf_approx.loc["Return"],
        "Vol Approx": perf_approx.loc["Vol"],
        "Vol True": perf_true.loc["Vol"],
        "Vol Delta": perf_true.loc["Vol"] - perf_approx.loc["Vol"],
        "Sharpe Approx": perf_approx.loc["Sharpe"],
        "Sharpe True": perf_true.loc["Sharpe"],
        "Sharpe Delta": perf_true.loc["Sharpe"] - perf_approx.loc["Sharpe"],
    }
)

# =============================
# ===== Performance Table =====
# =============================
size = 6
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))

tab = Table(
    df_perf,
    ax=ax,
    footer_divider=True,
    textprops={"fontsize": 10},
    column_definitions=[
        ColDef(name="index", title="Duration", textprops={"ha": "left", "weight": "bold"}),

        ColDef(name="Return Approx", title="Approximated", group="Annual Excess Return", formatter="{:.2%}"),
        ColDef(name="Return True", title="Full Valuation", group="Annual Excess Return",formatter="{:.2%}"),
        ColDef(name="Return Delta", title="Delta", group="Annual Excess Return",formatter="{:.2%}"),

        ColDef(name="Vol Approx", title="Approximated", group="Volatility", formatter="{:.2%}"),
        ColDef(name="Vol True", title="Full Valuation", group="Volatility", formatter="{:.2%}"),
        ColDef(name="Vol Delta", title="Delta", group="Volatility", formatter="{:.2%}"),

        ColDef(name="Sharpe Approx", title="Approximated", group="Sharpe", formatter="{:.2}"),
        ColDef(name="Sharpe True", title="Full Valuation", group="Sharpe", formatter="{:.2}"),
        ColDef(name="Sharpe Delta", title="Delta", group="Sharpe", formatter="{:.2}"),
    ],
)

for col in range(tab.col_label_row.get_xrange()[1]):
    tab.col_label_row.cells[col].text.set_weight("bold")

plt.tight_layout()
plt.savefig(figure_path.joinpath("Measuring Returns - DI Duration Approximated Performance.pdf"))
plt.show()

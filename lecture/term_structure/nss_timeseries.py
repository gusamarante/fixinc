import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from utils import figure_path, BLUE


# ===== READ DATA =====
DB_PATH = "../../data/nss_parameters.db"

con = sqlite3.connect(DB_PATH)
df = pd.read_sql(
    "SELECT * FROM nss_parameters WHERE curve_id = 'ntnb'",
    con,
    index_col="date",
    parse_dates=["date"],
)
con.close()

df = df.drop(columns="curve_id")
df = df.sort_index()


# ===== CHART =====
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

vars2plot = {
    "b1": {
        "title": r"$\beta_1$",
        "pos": (0, 0),
        "colspan": 1,
    },
    "b2": {
        "title": r"$\beta_2$",
        "pos": (0, 1),
        "colspan": 1,
    },
    "b3": {
        "title": r"$\beta_3$",
        "pos": (0, 2),
        "colspan": 1,
    },
    "b4": {
        "title": r"$\beta_4$",
        "pos": (0, 3),
        "colspan": 1,
    },
    "l1": {
        "title": r"$\lambda_1$",
        "pos": (1, 0),
        "colspan": 2,
    },
    "l2": {
        "title": r"$\lambda_2$",
        "pos": (1, 2),
        "colspan": 2,
    },
    "sse": {
        "title": "NSS Sum of Squarred Error",
        "pos": (2, 0),
        "colspan": 4,
    },
}


for var in vars2plot.keys():
    ax = plt.subplot2grid((3, 4), vars2plot[var]["pos"], colspan=vars2plot[var]["colspan"])
    ax.set_title(vars2plot[var]["title"])
    ax.plot(df[var], color=BLUE)
    # ax.axhline(0, color="black", lw=0.5)
    ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
    ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
    locators = mdates.YearLocator()
    ax.xaxis.set_major_locator(locators)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(rotation=90, axis="x")

plt.tight_layout()

plt.savefig(figure_path.joinpath("NSS - Brazil NTNB Parameters.pdf"))
plt.show()
plt.close()

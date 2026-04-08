import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fixinc.nss import nss

DB_PATH = "../../data/nss_parameters.db"

con = sqlite3.connect(DB_PATH)
params = pd.read_sql_query(
    "SELECT * FROM nss_parameters WHERE curve_id = 'ntnb2' ORDER BY date",
    con, parse_dates=["date"]
)
con.close()

# Keep last observation of each month
params = params.set_index("date").groupby(pd.Grouper(freq="ME")).last().dropna()

# Maturities from 1 to 30 years
maturities = np.linspace(1, 30, 60)

# Build yield surface
yields = np.zeros((len(params), len(maturities)))
for i, (date, row) in enumerate(params.iterrows()):
    beta = (row["b1"], row["b2"], row["b3"], row["b4"])
    lam = (row["l1"], row["l2"])
    yields[i, :] = nss(maturities, beta, lam)

# 3D surface plot
dates_num = np.arange(len(params))
X, Y = np.meshgrid(maturities, dates_num)

fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(111, projection="3d")
ax.plot_surface(X, Y, yields * 100, cmap="viridis", edgecolor="none", alpha=0.9)

ax.set_xlabel("Maturity (years)")
ax.set_ylabel("Date")
ax.set_zlabel("Yield (%)")
ax.set_title("NTN-B Yield Curve (NSS)")

# Label y-axis with dates
tick_step = max(1, len(params) // 8)
ax.set_yticks(dates_num[::tick_step])
ax.set_yticklabels([d.strftime("%Y-%m") for d in params.index[::tick_step]], rotation=45, fontsize=7)

plt.tight_layout()
plt.show()
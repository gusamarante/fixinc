import sqlite3
import pandas as pd
from fixinc.bond import NTNB
from fixinc.nss import BootstrapNSS
from data.readers import raw_ntnb
from fixinc.daycount import DayCount
from tqdm import tqdm

CURVE_ID = "ntnb"
DB_PATH = "../data/nss_parameters.db"

# Connect to (or create) the database and ensure the table exists
con = sqlite3.connect(DB_PATH)
con.execute("""
    CREATE TABLE IF NOT EXISTS nss_parameters (
        curve_id  TEXT    NOT NULL,
        date      TEXT    NOT NULL,
        b1        REAL    NOT NULL,
        b2        REAL    NOT NULL,
        b3        REAL    NOT NULL,
        b4        REAL    NOT NULL,
        l1        REAL    NOT NULL,
        l2        REAL    NOT NULL,
        sse       REAL    NOT NULL,
        PRIMARY KEY (curve_id, date)
    )
""")
con.commit()

BETA0 = (0.06, 0.03, 0.0, 0.0)
LAM0 = (1.2, 0.5)

# Find the earliest stored date to know where to resume
earliest_date = con.execute(
    "SELECT MIN(date) FROM nss_parameters WHERE curve_id = ?",
    (CURVE_ID,)
).fetchone()[0]

df = raw_ntnb()
ntnb = NTNB()
dc = DayCount(calendar="anbima", dcc="bus/252", adj="following")

dates2loop = pd.DatetimeIndex(df["reference date"].unique()).sort_values(ascending=False)
# dates2loop = dates2loop[dates2loop >= "2020-01-01"]
if earliest_date:
    dates2loop = dates2loop[dates2loop < earliest_date]

for t in tqdm(dates2loop):
    print(t)
    aux_raw = df[df["reference date"] == t].sort_values("du").dropna(subset="yield")
    all_cashflows = []
    prices = pd.Series()
    duration = pd.Series()
    for mat in aux_raw["maturity"].to_list():
        aux_cf = ntnb.get_cashflows(t, mat.year)
        all_cashflows.append(aux_cf.rename(mat.year))
        prices.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["price"].iloc[-1]
        duration.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["modified duration"].iloc[-1]

    all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0)
    bnss = BootstrapNSS(prices, all_cashflows, 1/duration, t, dc, beta0=BETA0, lam0=LAM0, verbose=False)

    con.execute(
        "INSERT OR REPLACE INTO nss_parameters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (CURVE_ID, t.date().isoformat(), *bnss.beta, *bnss.lam, bnss.sse)
    )
    con.commit()

con.close()

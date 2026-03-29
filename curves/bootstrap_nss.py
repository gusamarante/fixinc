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

# Use the last stored entry as the warm start, if available
row = con.execute(
    "SELECT date, b1, b2, b3, b4, l1, l2 FROM nss_parameters WHERE curve_id = ? ORDER BY date DESC LIMIT 1",
    (CURVE_ID,)
).fetchone()

if row:
    last_date, *params = row
    bm1 = tuple(params[:4])
    lm1 = tuple(params[4:])
else:
    last_date = None
    bm1 = (0.2, 0.2, 0.2, 0.2)
    lm1 = (1, 1)

df = raw_ntnb()
ntnb = NTNB()
dc = DayCount(calendar="anbima", dcc="bus/252", adj="following")

dates2loop = pd.DatetimeIndex(df["reference date"].unique()).sort_values()
dates2loop = dates2loop[dates2loop >= "2020-01-01"]
if last_date:
    dates2loop = dates2loop[dates2loop > last_date]

for t in tqdm(dates2loop):
    aux_raw = df[df["reference date"] == t].sort_values("du")
    all_cashflows = []
    prices = pd.Series()
    duration = pd.Series()
    for mat in aux_raw["maturity"].to_list():
        aux_cf = ntnb.get_cashflows(t, mat.year)
        all_cashflows.append(aux_cf.rename(mat.year))
        prices.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["price"].iloc[-1]
        duration.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["modified duration"].iloc[-1]

    all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0)
    bnss = BootstrapNSS(prices, all_cashflows, 1/duration, t, dc, beta0=bm1, lam0=lm1, verbose=False)

    con.execute(
        "INSERT OR REPLACE INTO nss_parameters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (CURVE_ID, t.date().isoformat(), *bnss.beta, *bnss.lam, bnss.sse)
    )
    con.commit()
    bm1 = bnss.beta
    lm1 = bnss.lam

con.close()

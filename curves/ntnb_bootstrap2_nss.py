import sqlite3
import numpy as np
import pandas as pd
from fixinc.bond import NTNB
from fixinc.nss import BootstrapNSS2
from data.readers import raw_ntnb
from fixinc.daycount import DayCount

CURVE_ID = "ntnb2"
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

BETA0 = (0.06, 0.0, 0.0, 0.0)
LAM0 = (1.2, 0.5)

df = raw_ntnb()
ntnb = NTNB()
dc = DayCount(calendar="anbima", dcc="bus/252", adj="following")

# Find which dates are already in the database
stored_dates = pd.read_sql_query(
    "SELECT date FROM nss_parameters WHERE curve_id = ?",
    con, params=(CURVE_ID,), parse_dates=["date"]
)["date"]

all_dates = pd.DatetimeIndex(df["reference date"].unique())
dates2loop = all_dates.difference(stored_dates).sort_values(ascending=False)
dates2loop = dates2loop[dates2loop >= "2005-01-01"]

beta0_run = BETA0
lam0_run = LAM0

for t in dates2loop:
    aux_raw = df[df["reference date"] == t].sort_values("du").dropna(subset="yield")
    aux_raw = aux_raw[aux_raw["maturity"].dt.month.isin([5, 8])]  # Remove weird maturities
    aux_raw = aux_raw[aux_raw["price"] != 0]
    aux_raw = aux_raw[~np.isclose(aux_raw["yield"], 0, atol=1e-6)]

    all_cashflows = []
    prices = pd.Series()
    duration = pd.Series()
    for mat in aux_raw["maturity"].to_list():
        try:
            aux_cf = ntnb.get_cashflows(t, mat.year)
            all_cashflows.append(aux_cf.rename(mat.year))

            if (aux_raw[aux_raw["maturity"] == mat]["coupon"].sum() != 0) and (t.day == 15):
                # If there is a coupon payment on the 15th
                prices.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["price"].iloc[-1] + aux_raw[aux_raw["maturity"] == mat]["coupon"].iloc[-1]
            else:
                prices.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["price"].iloc[-1]

            duration.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["modified duration"].iloc[-1]
        except AssertionError:
            # If weird maturity appears, skip this one
            continue

    all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0)
    bnss = BootstrapNSS2(prices, all_cashflows, 1/duration, t, dc, beta0=beta0_run, lam0=lam0_run, verbose=False, alpha_lam=0.0001, alpha_beta=0.00001)
    print(f"Date: {t:%Y-%m-%d}, SSE={bnss.sse:.6f}, Beta={bnss.beta}, Lambda={bnss.lam}")

    beta0_run = tuple(bnss.beta)
    lam0_run = tuple(bnss.lam)

    con.execute(
        "INSERT OR REPLACE INTO nss_parameters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (CURVE_ID, t.date().isoformat(), *bnss.beta, *bnss.lam, bnss.sse)
    )
    con.commit()

con.close()

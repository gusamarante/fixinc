import sqlite3
import numpy as np
import pandas as pd
from fixinc.bond import NTNB
from fixinc.nss import BootstrapNSS
from data.readers import raw_ntnb
from fixinc.daycount import DayCount

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
    bnss = BootstrapNSS(prices, all_cashflows, 1/duration, t, dc, beta0=beta0_run, lam0=lam0_run, verbose=False)
    print(f"Date: {t:%Y-%m-%d}, SSE={bnss.sse:.2f}, Beta={bnss.beta}, Lambda={bnss.lam}")

    beta0_run = tuple(bnss.beta)
    lam0_run = tuple(bnss.lam)

    con.execute(
        "INSERT OR REPLACE INTO nss_parameters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (CURVE_ID, t.date().isoformat(), *bnss.beta, *bnss.lam, bnss.sse)
    )
    con.commit()


# ==============================
# ===== Deal with bad days =====
# ==============================
all_days = pd.read_sql_query(
    "SELECT * FROM nss_parameters WHERE curve_id = ? ORDER BY date",
    con, params=(CURVE_ID,), parse_dates=["date"]
)

bad_sse = all_days.nlargest(10, "sse")
bad_params = [all_days.iloc[all_days[col].abs().nlargest(10).index] for col in ["b1", "b2", "b3", "b4", "l1", "l2"]]
bad_days = pd.concat([bad_sse] + bad_params).drop_duplicates(subset="date").reset_index(drop=True)
print(bad_days)

all_days = all_days.set_index("date").sort_index().copy()

for _, row in bad_days.iterrows():
    t = row["date"]

    # Get the next day's parameters as starting point
    future = all_days.loc[all_days.index > t]
    if future.empty:
        continue
    next_day = future.iloc[0]
    beta0_new = (next_day["b1"], next_day["b2"], next_day["b3"], next_day["b4"])
    lam0_new = (next_day["l1"], next_day["l2"])
    # beta0_new = BETA0
    # lam0_new = LAM0

    aux_raw = df[df["reference date"] == t].sort_values("du").dropna(subset="yield")
    aux_raw = aux_raw[aux_raw["maturity"].dt.month.isin([5, 8])]
    aux_raw = aux_raw[aux_raw["price"] != 0]
    aux_raw = aux_raw[~np.isclose(aux_raw["yield"], 0, atol=1e-8)]

    all_cashflows = []
    prices = pd.Series()
    duration = pd.Series()
    for mat in aux_raw["maturity"].to_list():
        try:
            aux_cf = ntnb.get_cashflows(t, mat.year)
            all_cashflows.append(aux_cf.rename(mat.year))
            prices.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["price"].iloc[-1] + aux_raw[aux_raw["maturity"] == mat]["coupon"].iloc[-1]
            duration.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["modified duration"].iloc[-1]
        except AssertionError:
            continue

    all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0)
    bnss = BootstrapNSS(prices, all_cashflows, 1/duration, t, dc, beta0=beta0_new, lam0=lam0_new, verbose=False)

    if bnss.sse < row["sse"]:
        print(f"Date: {t:%Y-%m-%d}, SSE improved: {row['sse']:.2f} -> {bnss.sse:.2f}")
        con.execute(
            "INSERT OR REPLACE INTO nss_parameters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (CURVE_ID, t.date().isoformat(), *bnss.beta, *bnss.lam, bnss.sse)
        )
        con.commit()
    else:
        print(f"Date: {t:%Y-%m-%d}, no improvement (old={row['sse']:.2f}, new={bnss.sse:.2f})")

con.close()

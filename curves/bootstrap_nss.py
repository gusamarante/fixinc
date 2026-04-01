import sqlite3
import pandas as pd
from fixinc.bond import NTNB
from fixinc.nss import BootstrapNSS
from data.readers import raw_ntnb
from fixinc.daycount import DayCount

CURVE_ID = "ntnb"
DB_PATH = "../data/nss_parameters.db"

# TODO logic to "fill" dates, starting from the most recent.
# TODO Logic to "correct" bad estimates.

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

for t in dates2loop:
    aux_raw = df[df["reference date"] == t].sort_values("du").dropna(subset="yield")
    aux_raw = aux_raw[aux_raw["maturity"].dt.month.isin([5, 8])]  # Remove weird maturities

    all_cashflows = []
    prices = pd.Series()
    duration = pd.Series()
    for mat in aux_raw["maturity"].to_list():
        try:
            aux_cf = ntnb.get_cashflows(t, mat.year)
            all_cashflows.append(aux_cf.rename(mat.year))
            prices.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["price"].iloc[-1]
            duration.loc[mat.year] = aux_raw[aux_raw["maturity"] == mat]["modified duration"].iloc[-1]
        except AssertionError:
            # If weird maturity appears, skip this one
            continue

    all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0)
    bnss = BootstrapNSS(prices, all_cashflows, 1/duration, t, dc, beta0=BETA0, lam0=LAM0, verbose=False)
    print(f"Date: {t:%Y-%m-%d}, SSE={bnss.sse:.2f}")

    con.execute(
        "INSERT OR REPLACE INTO nss_parameters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (CURVE_ID, t.date().isoformat(), *bnss.beta, *bnss.lam, bnss.sse)
    )
    con.commit()


# Deal with bad days
bad_days = pd.read_sql_query(
    "SELECT * FROM nss_parameters WHERE curve_id = ? ORDER BY sse DESC",
    con, params=(CURVE_ID,), parse_dates=["date"]
)
con.close()
print(bad_days)

import sqlite3
import numpy as np
import pandas as pd
from fixinc import nss
from utils import data_output

maturities_ntnf = [6, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120]
maturities_ntnb = [24, 36, 48, 60, 72, 84, 96, 108, 120]

DB_PATH = "../data/nss_parameters.db"

# --- Load NSS parameters from the database ---
conn = sqlite3.connect(DB_PATH)

params_ntnf = pd.read_sql(
    "SELECT date, b1, b2, b3, b4, l1, l2, sse FROM nss_parameters WHERE curve_id = 'ntnf2' ORDER BY date",
    conn,
    parse_dates=["date"],
    index_col="date",
)

params_ntnb = pd.read_sql(
    "SELECT date, b1, b2, b3, b4, l1, l2, sse FROM nss_parameters WHERE curve_id = 'ntnb2' ORDER BY date",
    conn,
    parse_dates=["date"],
    index_col="date",
)

conn.close()

# --- Reconstruct zero curves ---
mat_ntnf_years = np.array(maturities_ntnf) / 12
mat_ntnb_years = np.array(maturities_ntnb) / 12

nominal_yields = pd.DataFrame(
    [nss(mat_ntnf_years, row[["b1", "b2", "b3", "b4"]].values, row[["l1", "l2"]].values)
     for _, row in params_ntnf.iterrows()],
    index=params_ntnf.index,
    columns=maturities_ntnf,
)

real_yields = pd.DataFrame(
    [nss(mat_ntnb_years, row[["b1", "b2", "b3", "b4"]].values, row[["l1", "l2"]].values)
     for _, row in params_ntnb.iterrows()],
    index=params_ntnb.index,
    columns=maturities_ntnb,
)

# --- Fitting errors (SSE from the bootstrap optimization) ---
nominal_errors = params_ntnf[["sse"]].rename(columns={"sse": "fitting_error"})
real_errors = params_ntnb[["sse"]].rename(columns={"sse": "fitting_error"})

# --- Save to Excel ---
output_path = data_output / "nss_zero_curves.xlsx"

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    nominal_yields.to_excel(writer, sheet_name="nominal_yields")
    real_yields.to_excel(writer, sheet_name="real_yields")
    nominal_errors.to_excel(writer, sheet_name="nominal_errors")
    real_errors.to_excel(writer, sheet_name="real_errors")


print(f"Nominal yields: {nominal_yields.shape}")
print(f"Real yields: {real_yields.shape}")
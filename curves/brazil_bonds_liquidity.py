import pandas as pd

from data.readers import raw_ntnb, raw_ltn_ntnf
import matplotlib.pyplot as plt
from utils import data_output

ntnb = raw_ntnb()
ntnf = raw_ltn_ntnf()


ntnb["total risk"] = ntnb["volume"] * ntnb["dv01"].abs()
ntnb_dv01_stock = ntnb.groupby("reference date").sum(numeric_only=True)["total risk"].rolling(5).mean()

ntnf["total risk"] = ntnf["volume"] * ntnf["dv01"].abs()
ntnf_dv01_stock = ntnf.groupby("reference date").sum(numeric_only=True)["total risk"].rolling(5).mean()


ntnf_dv01_stock.rename("ntnf").plot(legend=True, alpha=0.5)
ntnb_dv01_stock.rename("ntnb").plot(legend=True, alpha=0.5)
plt.show()

df = pd.concat([ntnf_dv01_stock, ntnb_dv01_stock], axis=1).dropna(how="all")

# --- Save to Excel ---
output_path = data_output / "ntn_dv01_volume.xlsx"

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="dv01 stock")

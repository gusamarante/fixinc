import pandas as pd
from fixinc.bond import NTNB
from fixinc.nss import BootstrapNSS
from data.readers import raw_ntnb
from fixinc.daycount import DayCount
from tqdm import tqdm


df = raw_ntnb()
ntnb = NTNB()
dc = DayCount(calendar="anbima", dcc="bus/252", adj="following")

dates2loop = pd.DatetimeIndex(df["reference date"].unique()).sort_values()
dates2loop = dates2loop[dates2loop >= "2004-01-01"]
bm1 = (0.2, 0.2, 0.2, 0.2)
lm1 = (1, 1)

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

    print(t, bnss.beta, bnss.lam, bnss.sse)
    bm1 = bnss.beta
    lm1 = bnss.lam

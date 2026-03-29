import pandas as pd
from fixinc.nss import nss
from fixinc.bond import NTNB
from data.readers import raw_ntnb
from fixinc.daycount import DayCount

# Custom Functions
def get_nss(prices, cashflows, weights, ref_date, beta0=(0.2, 0.2, 0.2, 0.2), lam0=(0.5, 0.5)):

    T = dc.year_fraction(ref_date, cashflows.index)

    # TODO optimize over lambda
    # TODO optimize over beta
    yc = pd.Series(data=nss(T, beta0, lam0), index=cashflows.index)
    discf = (1 + yc) ** (-T)
    prices_dcf = cashflows.multiply(discf, axis=0).sum()
    sse = (((prices - prices_dcf) ** 2) * weights).sum()
    return sse

# Read data and generate instances
df = raw_ntnb()
ntnb = NTNB()
dc = DayCount(calendar="anbima", dcc="bus/252", adj="following")

# Manipulate data
dt = df["reference date"].max()
df = df[df["reference date"] == dt].sort_values("du")

all_cashflows = []
prices = pd.Series()
duration = pd.Series()
for mat in df["maturity"].to_list():
    aux_cf = ntnb.get_cashflows(dt, mat.year)
    all_cashflows.append(aux_cf.rename(mat.year))
    prices.loc[mat.year] = df[df["maturity"] == mat]["price"].iloc[-1]
    duration.loc[mat.year] = df[df["maturity"] == mat]["modified duration"].iloc[-1]

all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0)

print(get_nss(prices, all_cashflows, 1/duration, dt))
import pandas as pd
from fixinc.bond import NTNB
from fixinc.nss import BootstrapNSS, nss
from data.readers import raw_ntnb
from fixinc.daycount import DayCount


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

bnss = BootstrapNSS(prices, all_cashflows, 1/duration, dt, dc, verbose=True)
print(bnss.beta, bnss.lam, bnss.sse)
du = dc.days(dt, all_cashflows.index)
yc = pd.Series(
    data=nss(
        t=dc.year_fraction(dt, all_cashflows.index),
        beta=bnss.beta,
        lam=bnss.lam,
    ),
    index=du,
)

print(yc)
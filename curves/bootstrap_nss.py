import pandas as pd

from fixinc.bond import NTNB
from data.readers import raw_ntnb

df = raw_ntnb()
ntnb = NTNB()

dt = df["reference date"].max()
df = df[df["reference date"] == dt].sort_values("du")

all_cashflows = []
for year in df["maturity"].dt.year.to_list():
    aux_cf = ntnb.get_cashflows(dt, year)
    all_cashflows.append(aux_cf.rename(year))

all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0)
print(all_cashflows)

lambdas0 = 1.26, 0.55
beta0 = 0.06, 0.0305, -0.0398, 0.0483

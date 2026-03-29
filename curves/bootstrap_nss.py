import pandas as pd
from scipy.optimize import minimize
from fixinc.nss import nss
from fixinc.bond import NTNB
from data.readers import raw_ntnb
from fixinc.daycount import DayCount

# Custom Functions
def get_nss(prices, cashflows, weights, ref_date, beta, lam, dc):
    T = dc.year_fraction(ref_date, cashflows.index)
    yc = pd.Series(data=nss(T, beta, lam), index=cashflows.index)
    discf = (1 + yc) ** (-T)
    prices_dcf = cashflows.multiply(discf, axis=0).sum()
    sse = (((prices - prices_dcf) ** 2) * weights).sum()
    return sse


def fit_beta(prices, cashflows, weights, ref_date, lam, dc, beta0=(0.2, 0.2, 0.2, 0.2)):
    objective = lambda beta: get_nss(prices, cashflows, weights, ref_date, beta, lam, dc)
    result = minimize(objective, x0=list(beta0))
    return result.x, result.fun


def fit_nss(prices, cashflows, weights, ref_date, dc, beta0=(0.2, 0.2, 0.2, 0.2), lam0=(0.5, 0.5), verbose=False):
    step = [0]

    def objective(lam):
        _, sse = fit_beta(prices, cashflows, weights, ref_date, lam, dc, beta0)
        if verbose:
            step[0] += 1
            print(f"Step {step[0]:>4d} | λ₁={lam[0]:.6f}  λ₂={lam[1]:.6f} | SSE={sse:.6f}")
        return sse

    result = minimize(objective, x0=list(lam0), bounds=[(1e-8, None), (1e-8, None)])
    beta, sse = fit_beta(prices, cashflows, weights, ref_date, result.x, dc, beta0)
    return beta, result.x, sse

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

print(fit_nss(prices, all_cashflows, 1/duration, dt, dc, verbose=True))
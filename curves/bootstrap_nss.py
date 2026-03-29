import pandas as pd
from scipy.optimize import minimize
from fixinc.nss import nss
from fixinc.bond import NTNB
from data.readers import raw_ntnb
from fixinc.daycount import DayCount

class BootstrapNSS:

    def __init__(self, prices, cashflows, weights, ref_date, dc, beta0=(0.2, 0.2, 0.2, 0.2), lam0=(0.5, 0.5), verbose=False):
        """
        Fit a Nelson-Siegel-Svensson curve by bootstrapping from bond prices.

        Runs a nested optimization: the outer loop searches over decay parameters
        λ, while the inner loop solves for the best-fit beta loadings given each λ.
        Fitted parameters are stored as instance attributes upon instantiation.

        Parameters
        ----------
        prices : pd.Series
            Observed market prices, indexed by bond identifier.

        cashflows : pd.DataFrame
            Cashflow matrix with payment dates as index and bond identifiers
            as columns.

        weights : pd.Series
            Per-bond weights applied to the squared pricing errors in the SSE
            objective (e.g. inverse modified duration).

        ref_date : date-like
            Reference (settlement) date used to compute time fractions.

        dc : DayCount
            Day count instance used to compute year fractions from `ref_date`
            to each cashflow date.

        beta0 : array_like of shape (4,), optional
            Initial guess for [β₁, β₂, β₃, β₄]. Default is (0.2, 0.2, 0.2, 0.2).

        lam0 : array_like of shape (2,), optional
            Initial guess for [λ₁, λ₂]. Default is (0.5, 0.5).

        verbose : bool, optional
            If True, prints λ and SSE at each outer optimization step.
            Default is False.

        Attributes
        ----------
        beta : numpy.ndarray of shape (4,)
            Optimal NSS beta coefficients [β₁, β₂, β₃, β₄].

        lam : numpy.ndarray of shape (2,)
            Optimal NSS decay parameters [λ₁, λ₂].

        sse : float
            Weighted sum of squared pricing errors at the optimum.
        """
        self.step = 0
        self.prices = prices
        self.cashflows = cashflows
        self.weights = weights
        self.ref_date = ref_date
        self.dc = dc
        self.verbose = verbose

        result = minimize(lambda l: self._fit_lam(l, beta0), x0=list(lam0), bounds=[(1e-8, None), (1e-8, None)])
        self.lam = result.x
        self.beta, self.sse = self._fit_beta(self.lam, beta0)

    def _fit_lam(self, lam, b0):
        _, sse = self._fit_beta(lam, b0)
        if self.verbose:
            self.step += 1
            print(f"Step {self.step:>4d} | λ₁={lam[0]:.6f}  λ₂={lam[1]:.6f} | SSE={sse:.6f}")
        return sse

    def _fit_beta(self, lam, b0):
        result = minimize(lambda beta: self._sse(beta, lam), x0=list(b0))
        return result.x, result.fun

    def _sse(self, beta, lam):
        T = self.dc.year_fraction(self.ref_date, self.cashflows.index)
        yc = pd.Series(data=nss(T, beta, lam), index=self.cashflows.index)
        discf = (1 + yc) ** (-T)
        prices_dcf = self.cashflows.multiply(discf, axis=0).sum()
        return (((self.prices - prices_dcf) ** 2) * self.weights).sum()







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
import numpy as np
import pandas as pd
from scipy.optimize import minimize


def nss(t, beta, lam):
    """
    Nelson-Siegel-Svensson (NSS) yield curve model.

    Computes the interest rate at one or more maturities using the NSS
    parametric form:

        i(t) = β₁ + β₂ * [(1 - exp(-λ₁t)) / (λ₁t)]
                  + β₃ * [(1 - exp(-λ₁t)) / (λ₁t) - exp(-λ₁t)]
                  + β₄ * [(1 - exp(-λ₂t)) / (λ₂t) - exp(-λ₂t)]

    Parameters
    ----------
    t : float or array_like
        Time to maturity in years. Scalar or array. At t=0 the analytical
        limit i(0) = β₁ + β₂ is returned.
    beta : array_like of shape (4,)
        Factor loadings [β₁, β₂, β₃, β₄]:
          β₁ — long-term level factor.
          β₂ — short-term slope factor.
          β₃ — first curvature (hump) factor, governed by λ₁.
          β₄ — second curvature (hump) factor, governed by λ₂.
    lam : array_like of shape (2,)
        Decay rates [λ₁, λ₂]:
          λ₁ — decay rate for the first hump.
          λ₂ — decay rate for the second hump.

    Returns
    -------
    numpy.ndarray
        Interest rates corresponding to each maturity in `t`.
    """
    b1, b2, b3, b4 = beta
    l1, l2 = lam

    t = np.atleast_1d(np.asarray(t, dtype=float))
    zero = t == 0

    # Use safe denominators to avoid division by zero; results at t=0 are overwritten
    t_safe = np.where(zero, 1.0, t)

    f2 = (1 - np.exp(-l1 * t_safe)) / (l1 * t_safe)
    f3 = f2 - np.exp(-l1 * t_safe)
    f4 = (1 - np.exp(-l2 * t_safe)) / (l2 * t_safe) - np.exp(-l2 * t_safe)

    result = b1 + b2 * f2 + b3 * f3 + b4 * f4

    # At t=0: f2→1, f3→0, f4→0, so i(0) = b1 + b2
    result[zero] = b1 + b2

    return result


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
        self.verbose = verbose

        # Precompute arrays used on every SSE evaluation
        self._T = dc.year_fraction(ref_date, cashflows.index)
        self._cf = cashflows.to_numpy()
        self._prices = prices.to_numpy()
        self._weights = weights.to_numpy()

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
        base = np.maximum(1 + nss(self._T, beta, lam), 1e-8)  # Avoids numerical warnings during the optimization
        discf = base ** (-self._T)
        prices_dcf = self._cf.T @ discf
        return (((self._prices - prices_dcf) ** 2) * self._weights).sum()

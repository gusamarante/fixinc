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

        # Track the best solution seen across outer iterations
        self._best_beta = None
        self._best_lam = None
        self._best_sse = np.inf

        # Precompute arrays used on every SSE evaluation
        self._T = dc.year_fraction(ref_date, cashflows.index)
        self._cf = cashflows.to_numpy()
        self._prices = prices.to_numpy()
        self._weights = weights.to_numpy()

        lam0_sorted = (max(lam0), min(lam0))
        minimize(
            lambda l: self._fit_lam(l, beta0),
            x0=list(lam0_sorted),
            bounds=[(1e-8, 30), (1e-8, 30)],
            constraints={"type": "ineq", "fun": lambda l: l[0] - l[1] - 0.2},
            method="SLSQP",
        )
        self.beta = self._best_beta
        self.lam = self._best_lam
        self.sse = self._best_sse

    def _fit_lam(self, lam, b0):
        beta, sse = self._fit_beta(lam, b0)
        if np.isfinite(sse) and sse < self._best_sse:
            self._best_beta = beta
            self._best_lam = lam.copy()
            self._best_sse = sse
        if self.verbose:
            self.step += 1
            print(f"Step {self.step:>4d} | λ₁={lam[0]:.6f}  λ₂={lam[1]:.6f} | SSE={sse:.6f}")
        return sse

    def _fit_beta(self, lam, b0):
        result = minimize(lambda beta: self._sse(beta, lam), x0=list(b0),
                          bounds=[(0.0, 0.5), (None, None), (None, None), (None, None)])
        return result.x, result.fun

    def _sse(self, beta, lam, alpha=0.5):
        base = np.maximum(1 + nss(self._T, beta, lam), 1e-8)  # Avoids numerical warnings during the optimization
        discf = base ** (-self._T)
        prices_dcf = self._cf.T @ discf
        pricing_error = (((self._prices - prices_dcf) ** 2) * self._weights).sum()
        regularization = alpha * (beta[1] ** 2 + beta[2] ** 2 + beta[3] ** 2 + lam[0] ** 2 + lam[1] ** 2)
        return pricing_error + regularization


class BootstrapNSS2:

    _eps = 1e-4  # Regularization denominator floor

    def __init__(self, prices, cashflows, weights, ref_date, dc,
                 beta0=(0.06, 0.0, 0.0, 0.0), lam0=(1.0, 0.3),
                 verbose=False, alpha_beta=0.01, alpha_lam=0.05,
                 lam1_grid=None, lam2_grid=None, lam_gap=0.2, polish=True):
        """
        Fit a Nelson-Siegel-Svensson curve by bootstrapping from bond prices
        using grid search over decay parameters and percent price errors.

        The optimization uses a two-stage approach recommended by BIS/ECB
        literature for handling NSS multicollinearity:
          1. Grid search over (λ₁, λ₂) with L-BFGS-B for betas at each point
          2. Optional joint polish over all 6 parameters

        The objective function measures fit in percent price differences and
        includes regularization that penalizes percent deviations from the
        initial guess, enabling stable warm-starting from previous estimates.

        Parameters
        ----------
        prices : pd.Series
            Observed market prices, indexed by bond identifier.

        cashflows : pd.DataFrame
            Cashflow matrix with payment dates as index and bond identifiers
            as columns.

        weights : pd.Series
            Per-bond weights applied to the squared pricing errors
            (e.g. inverse modified duration).

        ref_date : date-like
            Reference (settlement) date used to compute time fractions.

        dc : DayCount
            Day count instance used to compute year fractions from `ref_date`
            to each cashflow date.

        beta0 : array_like of shape (4,), optional
            Initial guess and regularization anchor for [β₁, β₂, β₃, β₄].

        lam0 : array_like of shape (2,), optional
            Initial guess and regularization anchor for [λ₁, λ₂].
            Automatically sorted so that λ₁ ≥ λ₂.

        verbose : bool, optional
            If True, prints objective at each grid point. Default is False.

        alpha_beta : float, optional
            Regularization weight for beta parameters. Default is 0.01.

        alpha_lam : float, optional
            Regularization weight for lambda parameters. Default is 0.05.

        lam1_grid : array_like, optional
            Grid values for λ₁. Default is np.arange(0.3, 3.1, 0.3).

        lam2_grid : array_like, optional
            Grid values for λ₂. Default is np.arange(0.1, 1.5, 0.2).

        lam_gap : float, optional
            Minimum separation: λ₁ > λ₂ + lam_gap. Default is 0.2.

        polish : bool, optional
            If True, refine the best grid solution with joint optimization
            over all 6 parameters. Default is True.

        Attributes
        ----------
        beta : numpy.ndarray of shape (4,)
            Optimal NSS beta coefficients [β₁, β₂, β₃, β₄].

        lam : numpy.ndarray of shape (2,)
            Optimal NSS decay parameters [λ₁, λ₂].

        sse : float
            Objective value at the optimum (percent price errors +
            regularization).
        """
        self.verbose = verbose
        self._alpha_beta = alpha_beta
        self._alpha_lam = alpha_lam
        self._beta0 = np.asarray(beta0, dtype=float)
        self._lam0 = np.array([max(lam0), min(lam0)], dtype=float)
        self._lam_gap = lam_gap

        # Build grids
        self._lam1_grid = np.asarray(lam1_grid) if lam1_grid is not None else np.arange(0.3, 3.1, 0.3)
        self._lam2_grid = np.asarray(lam2_grid) if lam2_grid is not None else np.arange(0.1, 1.5, 0.2)

        # Precompute arrays
        self._T = dc.year_fraction(ref_date, cashflows.index)
        self._cf = cashflows.to_numpy()
        self._prices = prices.to_numpy()
        self._weights = weights.to_numpy()
        self._inv_prices = 1.0 / self._prices

        # Stage 1: Grid search
        best_beta, best_lam, best_obj = self._grid_search()

        # Stage 2: Polish
        if polish and best_beta is not None:
            p_beta, p_lam, p_obj = self._polish(best_beta, best_lam)
            if p_obj < best_obj:
                best_beta, best_lam, best_obj = p_beta, p_lam, p_obj

        self.beta = best_beta
        self.lam = best_lam
        self.sse = best_obj

    def _objective(self, beta, lam):
        """Full objective: percent price errors + regularization."""
        base = np.maximum(1.0 + nss(self._T, beta, lam), 1e-8)
        discf = base ** (-self._T)
        p_model = self._cf.T @ discf

        pct_err = (p_model - self._prices) * self._inv_prices
        pricing = (self._weights * pct_err ** 2).sum()

        reg_b = self._alpha_beta * np.sum(
            ((np.asarray(beta) - self._beta0) / (np.abs(self._beta0) + self._eps)) ** 2
        )
        reg_l = self._alpha_lam * np.sum(
            ((np.asarray(lam) - self._lam0) / (np.abs(self._lam0) + self._eps)) ** 2
        )
        return pricing + reg_b + reg_l

    def _fit_betas(self, lam, beta_init):
        """Optimize betas for fixed lambda via L-BFGS-B."""
        result = minimize(
            lambda b: self._objective(b, lam),
            x0=list(beta_init),
            method='L-BFGS-B',
            bounds=[(0.0, 0.5), (-1.0, 1.0), (-1.0, 1.0), (-1.0, 1.0)],
        )
        return result.x, result.fun

    def _grid_search(self):
        """Search over lambda grid, optimizing betas at each point."""
        best_obj = np.inf
        best_beta = None
        best_lam = None

        for l1 in self._lam1_grid:
            for l2 in self._lam2_grid:
                if l1 <= l2 + self._lam_gap:
                    continue
                lam = np.array([l1, l2])
                beta, obj = self._fit_betas(lam, self._beta0)
                if obj < best_obj:
                    best_obj = obj
                    best_beta = beta
                    best_lam = lam
                if self.verbose:
                    print(f"Grid: λ₁={l1:.2f}  λ₂={l2:.2f} | obj={obj:.6f}")

        return best_beta, best_lam, best_obj

    def _polish(self, beta_init, lam_init):
        """Joint optimization over all 6 parameters."""
        x0 = np.concatenate([beta_init, lam_init])
        result = minimize(
            lambda x: self._objective(x[:4], x[4:]),
            x0=x0,
            method='L-BFGS-B',
            bounds=[
                (0.0, 0.5), (-1.0, 1.0), (-1.0, 1.0), (-1.0, 1.0),
                (1e-2, 30.0), (1e-2, 30.0),
            ],
        )
        beta_out = result.x[:4]
        lam_out = result.x[4:]
        if lam_out[0] <= lam_out[1] + self._lam_gap:
            return beta_init, lam_init, self._objective(beta_init, lam_init)
        return beta_out, lam_out, result.fun

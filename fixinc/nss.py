import numpy as np


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

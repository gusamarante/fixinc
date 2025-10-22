import numpy as np


def nss(t, b1, b2, b3, b4, l1, l2):
    """
    i_t = β₁ + β₂ * [(1 - exp(-λ₁ * t)) / (λ₁ * t)]
        + β₃ * [(1 - exp(-λ₁ * t)) / (λ₁ * t) - exp(-λ₁ * t)]
        + β₄ * [(1 - exp(-λ₂ * t)) / (λ₂ * t) - exp(-λ₂ * t)]
    """
    f2 = (1 - np.exp(- l1 * t)) / (l1 * t)
    f3 = ((1 - np.exp(- l1 * t)) / (l1 * t)) - np.exp(- l1 * t)
    f4 = ((1 - np.exp(- l2 * t)) / (l2 * t)) - np.exp(- l2 * t)
    return b1 + b2 * f2 + b3 * f3 + b4 * f4

"""
replicates the fama-bliss study for DI futures
"""
import pandas as pd

from data.readers import di_curve
from fixinc import CurvePCA
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from utils import figure_path, BLUE, RED
import numpy as np
import statsmodels.api as sm

size = 5

curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)

curve = curve.resample("YE").last()
columns2keep = [12 * y for y in range(1, 11)]
curve = curve[columns2keep]

pu = 1 / ((1 + curve) ** (curve.columns.astype(int) * 21 / 252))
lnpu = np.log(pu)
rf = - lnpu[12]
fra = ((pu / pu.shift(-1, axis=1)) - 1).shift(1, axis=1)  # No exponent adjustment because rates are 1y apart

hpr = (lnpu - lnpu.shift(1, axis=0).shift(-1, axis=1)).shift(1, axis=1)
ehpr = hpr.sub(rf.shift(1), axis=0)  # Dependent variables of table 1
framrf = fra.sub(rf, axis=0).shift(1)  # Independent variables of table 1


outreg = pd.DataFrame()
for mat in columns2keep[1:]:
    X = sm.add_constant(framrf[mat])
    res = sm.OLS(
        endog=ehpr[mat],
        exog=X,
        missing='drop',
    ).fit()
    res = res.get_robustcov_results(
        cov_type="HAC",
        maxlags=2,
        kernel="bartlett",
    )

    outreg.loc[mat, "a"] = res.params[0]
    outreg.loc[mat, "a se"] = res.bse[0]
    outreg.loc[mat, "a t-stat"] = res.tvalues[0]
    outreg.loc[mat, "a p-value"] = res.pvalues[0]

    outreg.loc[mat, "b"] = res.params[1]
    outreg.loc[mat, "b se"] = res.bse[1]
    outreg.loc[mat, "b t-stat"] = res.tvalues[1]
    outreg.loc[mat, "b p-value"] = res.pvalues[1]

    outreg.loc[mat, "R2"] = res.rsquared

outreg.to_clipboard()
print(outreg)

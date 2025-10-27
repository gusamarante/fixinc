import pandas as pd
import matplotlib.pyplot as plt
from data.readers import di_curve, trackers_di1
import numpy as np


start_date = "2009-01-01"

# Grab Data
trackers = trackers_di1()
trackers.columns = trackers.columns.str.replace("DI ", "").str.replace("y", "").astype(float)

curve = di_curve()
curve.columns = curve.columns.str.replace("m", "").astype(float) / 12

mats = np.intersect1d(curve.columns, trackers.columns)

trackers = trackers[mats]
curve = curve[mats]

# True Returns
rets_true = trackers.pct_change(1)
rets_true = rets_true[rets_true.index >= start_date]

# Approximated returns
moddur = - curve.columns / (1 + curve)
rets_approx = (curve.diff(1) * moddur).dropna()
rets_approx = rets_approx[rets_approx.index >= start_date]

# Chart
# TODO Scatter plot of daily returns (is deceiving)
plt.plot(rets_approx[10.], rets_true[10.], lw=0, ls=None, marker="o", alpha=0.4)
plt.show()

# TODO performance table of reconstructed indexes
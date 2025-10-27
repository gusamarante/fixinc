import pandas as pd

from data.readers import di_curve, trackers_di1
import numpy as np


start_date = "2009-01-01"

# True Returns
trackers = trackers_di1()
trackers.columns = trackers.columns.str.replace("DI ", "").str.replace("y", "").astype(float)
rets_true = trackers.pct_change(1)
rets_true = rets_true[rets_true.index >= start_date]

# Approximated returns
curve = di_curve()
curve.columns = curve.columns.str.replace("m", "").astype(float) / 12
moddur = - curve.columns / (1 + curve)
rets_approx = curve.diff(1) * moddur
rets_approx = rets_approx[rets_approx.index >= start_date]

# TODO retornos aproximados estão zuados

mats = np.intersect1d(curve.columns, trackers.columns)
rets_true, rets_approx = rets_true[mats], rets_approx[mats]

compare_means = pd.DataFrame(
    {
        "True": rets_true.mean(),
        "Approx": rets_approx.mean()
    }
)
print(compare_means)
import numpy as np
from scipy.interpolate import make_interp_spline, CubicSpline, interp1d

from fixinc.compounder import RateCompounder


class ZeroCurve:

    def __init__(self, yields, yc='compound'):
        # TODO yields ref_date X years to mat
        # TODO assert date types
        self.yields = yields
        self.comp = RateCompounder(yc=yc)

    def interpolate(self, ref_date, mat, method="linear"):
        # TODO Documentation
        curve = self.yields.loc[ref_date].dropna()

        if method == "linear":
            fun = make_interp_spline(curve.index, curve.values, k=1)
            y_interp = fun(mat)

        elif method == "flat forward":
            logfactor = np.log(self.comp.yield_to_factor_yf(curve.values, curve.index))
            factor_interp = np.exp(make_interp_spline(curve.index, logfactor, k=1)(mat))
            y_interp = self.comp.factor_to_yield_yf(factor_interp, mat)

        elif method == "cubic spline":
            fun = CubicSpline(curve.index, curve.values)
            y_interp = fun(mat)

        else:
            raise NotImplementedError(f"Interpolation method {method} not inplemented")

        return y_interp

    def forward(self, t1, t2):
        # TODO Documentation

        # Linear Interpolation
        def get_fra(yc):
            yc = yc.dropna()
            fun = interp1d(yc.index, yc.values, kind="linear", fill_value="extrapolate")
            y1, y2 = fun(t1), fun(t2)
            fra = (((1 + y2) ** t2) / ((1 + y1) ** t1)) ** (1 / (t2 - t1)) - 1  # TODO use the compouder
            return fra

        fras = self.yields.apply(get_fra, axis=1)
        return fras

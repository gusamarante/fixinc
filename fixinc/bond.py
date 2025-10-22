import pandas as pd
from fixinc.daycount import DayCount
from fixinc.compounder import RateCompounder
from scipy.interpolate import interp1d, make_interp_spline


class Bond:
    # TODO Implement:
    #  - LTN, NTNF, NTNB
    #  - US Treasuries
    _1bp = 1 / 10_000  # 1 basis-point
    epsilon = 1e-10

    def __init__(self, cashflows, calendar, dcc, yc):
        """
        Generic bond class for fixed income operations

        Parameters
        ----------
        cashflows: pandas.Series
            Cashflows and their respective dates

        calendar: str
            Holiday calendar to be used by the DayCount class. Supported values
            are the same as the DayCount class

        dcc: str
            Day count convention to be used by the DayCount class. Supported
            values are the same as the DayCount class

        yc: str
            Yield convetion to be used by the RateCompounder class. Supported
            values are the same as the RateCompounder class.
        """
        self.cashflows = cashflows
        self.dc = DayCount(calendar=calendar, dcc=dcc)
        self.rc = RateCompounder(yc=yc)

    def convexity(self, t, y):
        """
        Convexity coefficient, the coefficient of the second term in the taylor
        expansion for the percent change in the bond price, given a change in
        the yield.

        bond % change ~ duration * (delta_y) + convexity * (delta_y ** 2)

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date

        y: float
            Current yield to maturity
        """
        # TODO Definition duration * dy + convexity * (dy**2)
        up = self.yield_to_price(t, y + self._1bp)
        mid = self.yield_to_price(t, y)
        dw = self.yield_to_price(t, y - self._1bp)
        return 0.5 * (up + dw - 2 * mid) / mid

    def duration(self, t, y):
        """
        Modified Duration coefficient, the coefficient of the first term in the
        taylor expansion for the percent change in the bond price, given a
        change in the yield.

        bond % change ~ duration * (delta_y) + convexity * (delta_y ** 2)

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date

        y: float
            Current yield to maturity
        """
        return self.dv01(t, y) / self.yield_to_price(t, y)

    def duration_macaulay(self, t, y):
        """
        Macaulay duration, the weighted average time (in years) until a bond’s
        cash flows are received. Can be intepreted as what is the time until
        maturity of a zero-coupon bond with same sensitivity to changes in
        interest rates.

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date

        y: float
            Current yield to maturity
        """
        cf = self.cashflows[self.cashflows.index >= t]
        yf = self.dc.year_fraction(t, cf.index)
        disc = self.rc.yield_to_disc(y, t, cf.index)
        dcf = cf * disc
        return (dcf * yf).sum() / self.yield_to_price(t, y)

    def dv01(self, t, y):
        """
        DV01 of the bond, the change in price given a 1 basis-point change in
        the yield

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date

        y: float
            Current yield to maturity
        """
        pu = self.yield_to_price(t, y)
        pup = self.yield_to_price(t, y + self.epsilon)
        return (pup - pu) / (10_000 * self.epsilon)

    def yield_to_price(self, t, y):
        """
        Computes the price of bond, as the present value of its future
        cashflows, given the yield to maturity

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date

        y: float
            Current yield to maturity
        """
        # TODO handle negative dates
        cf = self.cashflows[self.cashflows.index >= t]
        disc = self.rc.yield_to_disc(y, t, cf.index)
        return (cf * disc).sum()

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
        elif method == "flat-forward":
            # TODO
            #  get discounts, invert, take logs, interpolate linear, exponential, invert, get rate
            a = 1

        else:
            raise NotImplementedError(f"Interpolation method {method} not inplemented")

        return y_interp

    def forward(self, t1, t2):
        # TODO Documentation
        # TODO assert t1 < t2, "Invalid maturities"

        # Linear Interpolation
        def get_fra(yc):
            yc = yc.dropna()
            fun = interp1d(yc.index, yc.values, kind="linear", fill_value="extrapolate")
            y1, y2 = fun(t1), fun(t2)
            fra = (((1 + y2) ** t2) / ((1 + y1) ** t1)) ** (1 / (t2 - t1)) - 1  # TODO use the compouder
            return fra

        fras = self.yields.apply(get_fra, axis=1)
        return fras
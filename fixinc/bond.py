from fixinc.daycount import DayCount
from fixinc.compounder import RateCompounder
from scipy.optimize import brentq
from data.readers import vna_ntnb
import pandas as pd


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

    def price_to_yield(self, t, price, y0=0.05, tol=1e-6, max_iter=200):
        """
        Solves for the yield to maturity given the bond price, by inverting
        yield_to_price numerically.

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date

        price: float
            Observed market price (same units as yield_to_price returns)

        y0: float
            Initial yield guess, default 0.05

        tol: float
            Convergence tolerance on the price residual, default 1e-10

        max_iter: int
            Maximum Newton-Raphson iterations, default 200
        """
        y = y0
        for _ in range(max_iter):
            p = self.yield_to_price(t, y)
            dp_dy = self.dv01(t, y) * 10_000
            y_new = y - (p - price) / dp_dy
            if abs(self.yield_to_price(t, y_new) - price) < tol:
                return y_new
            y = y_new

        # Fallback to bracketed solver
        try:
            return brentq(lambda y_: self.yield_to_price(t, y_) - price, y0 - 0.5, y0 + 0.5, xtol=tol)
        except ValueError:
            raise RuntimeError(
                f"price_to_yield did not converge for price={price} starting from y0={y0}"
            )

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

class NTNB:

    def __init__(self):
        # TODO Documentation

        self.dc = DayCount(calendar="anbima", dcc="bus/252", adj='following')
        self.vna = vna_ntnb()

    @staticmethod
    def maturity_date(mat):
        year = int(mat)
        if year % 2 == 0:
            return pd.Timestamp(year, 8, 15)
        else:
            return pd.Timestamp(year, 5, 15)

    @staticmethod
    def coupon_dates(mat):
        year = int(mat)
        mat_date = NTNB.maturity_date(mat)
        if year % 2 == 0:
            months = [2, 8]
        else:
            months = [5, 11]
        dates = []
        # go back far enough to cover any issued NTNB
        for y in range(2000, year + 1):
            for m in months:
                dt = pd.Timestamp(y, m, 15)
                if dt <= mat_date:
                    dates.append(dt)
        return pd.DatetimeIndex(dates)

    def get_cashflows(self, t, mat):
        """
        Generates the future cashflow series of an NTN-B bond.

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date, used to fetch the VNA and filter future cashflows

        mat: str, int
            Maturity year of the bond (e.g. "2028" or 2035). Even years
            mature on August 15th, odd years on May 15th.
        """
        fv = self.vna.loc[t]
        dates = self.coupon_dates(mat)
        dates = dates[dates >= t]
        dates = self.dc.adjust(dates)
        assert len(dates) > 0, f"No future coupon dates for maturity {mat} as of {t}"
        coupon = fv * (1.06**0.5 - 1)
        cfs = pd.Series(index=dates, data=coupon)
        cfs.iloc[-1] = cfs.iloc[-1] + fv
        return cfs

if __name__ == "__main__":
    ntnb = NTNB()
    cf = ntnb.get_cashflows("2026-03-25", "2035")
    print(cf)

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
        """
        NTN-B (Nota do Tesouro Nacional - Série B) bond class for Brazilian
        inflation-linked fixed income operations. Uses ANBIMA business day
        calendar with bus/252 day count convention.
        """
        self.dc = DayCount(calendar="anbima", dcc="bus/252", adj='following')
        self.vna = vna_ntnb()

    @staticmethod
    def maturity_date(mat):
        """
        Returns the maturity date of an NTN-B bond given its maturity year.
        Even years mature on August 15th, odd years on May 15th.

        Parameters
        ----------
        mat: str, int
            Maturity year of the bond (e.g. "2028" or 2035)
        """
        year = int(mat)
        if year % 2 == 0:
            return pd.Timestamp(year, 8, 15)
        else:
            return pd.Timestamp(year, 5, 15)

    @staticmethod
    def coupon_dates(mat):
        """
        Generates all semiannual coupon payment dates for an NTN-B bond,
        from the year 2000 up to and including the maturity date. Even year
        bonds pay on February 15th and August 15th, odd year bonds pay on
        May 15th and November 15th.

        Parameters
        ----------
        mat: str, int
            Maturity year of the bond (e.g. "2028" or 2035)
        """
        year = int(mat)
        mat_date = NTNB.maturity_date(mat)
        first_month = 2 if year % 2 == 0 else 5
        return pd.date_range(
            start=pd.Timestamp(2000, first_month, 15),
            end=mat_date,
            freq=pd.DateOffset(months=6),
        )

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


class NTNF:

    fv = 1000

    def __init__(self):
        """
        NTN-F (Nota do Tesouro Nacional - Série F) bond class for Brazilian
        nominal fixed-rate fixed income operations. Uses ANBIMA business day
        calendar with bus/252 day count convention.
        """
        self.dc = DayCount(calendar="anbima", dcc="bus/252", adj='following')

    @staticmethod
    def maturity_date(mat):
        """
        Returns the maturity date of an NTN-F bond given its maturity year.
        NTN-F bonds always mature on January 1st.

        Parameters
        ----------
        mat: str, int
            Maturity year of the bond (e.g. "2029" or 2035)
        """
        return pd.Timestamp(int(mat), 1, 1)

    @staticmethod
    def coupon_dates(mat):
        """
        Generates all semiannual coupon payment dates for an NTN-F bond,
        from the year 2000 up to and including the maturity date. Coupons
        are paid on January 1st and July 1st.

        Parameters
        ----------
        mat: str, int
            Maturity year of the bond (e.g. "2029" or 2035)
        """
        mat_date = NTNF.maturity_date(mat)
        return pd.date_range(
            start=pd.Timestamp(2000, 1, 1),
            end=mat_date,
            freq=pd.DateOffset(months=6),
        )

    def get_cashflows(self, t, mat):
        """
        Generates the future cashflow series of an NTN-F bond, including
        semiannual coupon payments and principal repayment at maturity.
        The coupon is computed as 1000 * (1.10^0.5 - 1).

        Parameters
        ----------
        t: str, pandas.Timestamp
            Current date, used to filter future cashflows

        mat: str, int
            Maturity year of the bond (e.g. "2029" or 2035)
        """
        dates = self.coupon_dates(mat)
        dates = dates[dates >= t]
        dates = self.dc.adjust(dates)
        assert len(dates) > 0, f"No future coupon dates for maturity {mat} as of {t}"
        coupon = round(self.fv * (1.10 ** 0.5 - 1), 2)
        cfs = pd.Series(index=dates, data=coupon)
        cfs.iloc[-1] = cfs.iloc[-1] + self.fv
        return cfs


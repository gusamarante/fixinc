from fixinc.daycount import DayCount
from fixinc.compounder import RateCompounder
from scipy.optimize import brentq


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

class NTNB(Bond):

    def __init__(self, maturity):
        # TODO Documentation
        # TODO Get the VNA somewhere
        # TODO Generate the cashflows based on maturity
        # TODO How to deal with the price?

        super().__init__(
            cashflows=pd.Series(1),  # TODO change this
            calendar='anbima',
            dcc='bus/252',
            yc='compound',
        )


if __name__ == "__main__":
    import pandas as pd

    # Build a simple coupon bond:
    #   - 3 semi-annual coupons of 3.0 + principal of 100.0 at maturity
    #   - Brazilian ANBIMA calendar, act/act isda day count, compound yield
    settlement = pd.Timestamp('2024-01-02')
    cashflows = pd.Series(
        [3.0, 3.0, 103.0],
        index=[
            pd.Timestamp('2024-07-15'),
            pd.Timestamp('2025-01-15'),
            pd.Timestamp('2025-07-15'),
        ]
    )
    bond = Bond(cashflows, calendar='anbima', dcc='bus/252', yc='compound')

    y = 0.06
    price = bond.yield_to_price(settlement, y)
    print(f"Price at y={y:.2%}: {price:.6f}")
    print(f"Modified duration:  {bond.duration(settlement, y):.6f}")
    print(f"Macaulay duration:  {bond.duration_macaulay(settlement, y):.6f}")
    print(f"DV01:               {bond.dv01(settlement, y):.6f}")
    print(f"Convexity:          {bond.convexity(settlement, y):.6f}")

    # Round-trip: recover yield from price
    y_recovered = bond.price_to_yield(settlement, price)
    print(f"\nRound-trip yield:   {y_recovered:.10f}  (error: {abs(y_recovered - y):.2e})")
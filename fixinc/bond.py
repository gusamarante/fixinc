import pandas as pd
from fixinc.daycount import DayCount
from fixinc.compounder import RateCompounder


class Bond:
    # TODO Implement:
    #  - LTN, NTNF, NTNB
    #  - US Treasuries
    _1bp = 1 / 10_000  # 1 basis-point

    def __init__(self, cashflows, calendar, dcc, yc):
        # TODO Documentation
        self.cashflows = cashflows
        self.dc = DayCount(calendar=calendar, dcc=dcc)
        self.rc = RateCompounder(yc=yc)

    def convexity(self, t, y):
        # TODO Definition duration * dy + convexity * (dy**2)
        up = self.yield_to_price(t, y + self._1bp)
        mid = self.yield_to_price(t, y)
        dw = self.yield_to_price(t, y - self._1bp)
        return 0.2 * (up + dw - 2 * mid) / mid

    def duration(self, t, y):
        # TODO documentation (modified duration)
        return self.dv01(t, y) / self.yield_to_price(t, y)

    def duration_macaulay(self, t, y):
        # TODO macaulay duration
        cf = self.cashflows[self.cashflows.index >= t]
        yf = self.dc.year_fraction(t, cf.index)
        disc = self.rc.yield_to_disc(y, t, cf.index)
        dcf = cf * disc
        return (dcf * yf).sum() / self.yield_to_price(t, y)

    def dv01(self, t, y):
        # TODO documentation
        # TODO increase precision
        up = self.yield_to_price(t, y + self._1bp)  # Lower price
        dw = self.yield_to_price(t, y - self._1bp)  # Higher price
        return 0.5 * (up - dw)

    def yield_to_price(self, t, y):
        # TODO Documentation
        # TODO handle negative dates
        cf = self.cashflows[self.cashflows.index >= t]
        disc = self.rc.yield_to_disc(y, t, cf.index)
        return (cf * disc).sum()


# ===== EXAMPLE =====
cft = pd.Series({pd.to_datetime("2026-12-31"): 1000})
b = Bond(
    cashflows=cft,
    calendar="us_trading",
    dcc="act/365",
    yc='compound',
)
today = pd.to_datetime('today').normalize()
print(b.convexity(t=today, y=0.05))

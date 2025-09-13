import pandas as pd
from fixinc.daycount import DayCount


class Bond:

    def __init__(self, cashflows, calendar, dcc, yc):
        # TODO Documentation
        self.cashflows = cashflows
        self.dc = DayCount(calendar=calendar, dcc=dcc)
        self.comp = 1  # TODO Compounder

    def yield2price(self, t, y):
        # TODO Documentation
        yf = self.dc.year_fraction(t, self.cashflows.index)
        disc = 1 / ((1 + y) ** yf)
        pv = (self.cashflows * disc).sum()
        return pv



# ===== EXAMPLE =====
cf = pd.Series({pd.to_datetime("2026-12-31"): 1000})
b = Bond(
    cashflows=cf,
    calendar="us_trading",
    dcc="act/365",
)
print(b.yield2price(t=pd.to_datetime('today').normalize(), y=0.05))




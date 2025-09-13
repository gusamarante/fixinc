import pandas as pd
from fixinc.daycount import DayCount
from fixinc.compounder import RateCompounder


class Bond:
    # TODO Implement:
    #  - Duration
    #  - DV01

    def __init__(self, cashflows, calendar, dcc, yc):
        # TODO Documentation
        self.cashflows = cashflows
        self.dc = DayCount(calendar=calendar, dcc=dcc)
        self.rc = RateCompounder(yc=yc)

    def yield2price(self, t, y):
        # TODO Documentation
        disc = self.rc.yield_to_disc(y, t, self.cashflows.index)
        pv = (self.cashflows * disc).sum()
        return pv



# ===== EXAMPLE =====
cf = pd.Series({pd.to_datetime("2026-12-31"): 1000})
b = Bond(
    cashflows=cf,
    calendar="us_trading",
    dcc="act/365",
    yc='compound',
)
print(b.yield2price(t=pd.to_datetime('today').normalize(), y=0.05))




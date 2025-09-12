import pandas as pd


class Bond:

    def __init__(self, cashflows, reference_date):
        self.cashflows = cashflows

    def yield2price(self, y):
        # TODO Documentation
        # TODO Daycounts
        # TODO Compounding
        pass



# ===== EXAMPLE =====
cf = pd.Series({pd.to_datetime("2026-12-31"): 1000})
b = Bond(cf, pd.to_datetime('today'))
print(b.yield2price(0.05))  # Example usage




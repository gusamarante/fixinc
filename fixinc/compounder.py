from fixinc.daycount import DayCount
from numpy import exp


class RateCompounder:

    def __init__(self, yc='compound', dc=DayCount()):
        """
        Class to deal with rate compounding conventions.

        Parameters
        ----------
        yc: str
            Yield convention. Supported values:
            - 'linear': 1 + y * (dc / dib)
            - 'compound': (1 + y) ** (dc / dib)
            - 'continuous': exp(y * (dc / dib))

        dc: DayCount
            Instance of the DayCount class with day-counting conventions to
            follow
        """
        self.yc = yc
        self.dc = dc

    def yield_to_factor(self, y, d1, d2):
        """
        Generates the yield factor between dates d1 and d2

        Parameters
        ----------
        y: float
            yield

        d1: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Start Date(s)

        d2: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            End Date(s)

        Returns
        -------
        float or numpy.ndarray
        """
        yf = self.dc.year_fraction(d1, d2)
        if self.yc == 'compound':
            return (1 + y) ** yf

        elif self.yc == 'linear':
            return 1 + y * yf

        elif self.yc == 'continuous':
            return exp(y * yf)

        else:
            raise NotImplementedError(f"Yield convention {self.yc} not implemented")

    def yield_to_disc(self, y, d1, d2):
        """
        Generates the discount factor between dates d1 and d2

        Parameters
        ----------
        y: float
            yield

        d1: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Start Date(s)

        d2: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            End Date(s)

        Returns
        -------
        float or numpy.ndarray
        """
        return 1 / self.yield_to_factor(y, d1, d2)

# ===== EXAMPLE =====
rc = RateCompounder()

from fixinc.daycount import DayCount
from numpy import exp, floating, integer, log, ndarray
from pandas import Series


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

    def yield_to_factor_yf(self, y, yf):
        """
        Generates the yield factor between dates d1 and d2

        Parameters
        ----------
        y: float
            yield

        yf: float
            year fraction

        Returns
        -------
        float or numpy.ndarray
        """
        if self.yc == 'compound':
            return (1 + y) ** yf

        elif self.yc == 'linear':
            return 1 + y * yf

        elif self.yc == 'continuous':
            return exp(y * yf)

        else:
            raise NotImplementedError(f"Yield convention {self.yc} not implemented")

    def factor_to_yield_yf(self, f, yf):
        """
        Generates the yield implied by a yield factor over a year fraction

        Parameters
        ----------
        f: float, int, numpy scalar, pandas.Series, or numpy.ndarray
            yield factor

        yf: float, int, numpy scalar, pandas.Series, or numpy.ndarray
            year fraction

        Notes
        -----
        `f` and `yf` are combined element-wise, so they must have the same
        shape - scalars counting as shape () - and, when both are
        pandas.Series, the same index. No broadcasting is performed: pairing a
        scalar with an array is rejected rather than stretched.

        Returns
        -------
        float, pandas.Series, or numpy.ndarray
            Same type and shape as the inputs
        """
        self._assert_same_shape(f, yf)

        if self.yc == 'compound':
            return f ** (1 / yf) - 1

        elif self.yc == 'linear':
            return (f - 1) / yf

        elif self.yc == 'continuous':
            return log(f) / yf

        else:
            raise NotImplementedError(
                f"Yield convention {self.yc} not implemented")

    @staticmethod
    def _assert_same_shape(f, yf):
        """
        Asserts that `f` and `yf` have the same shape, so they can be combined
        element-wise without any broadcasting. Scalars count as shape (). When
        both inputs are pandas.Series, their indexes must also be equal, so that
        values are not silently misaligned.

        Parameters
        ----------
        f: float, int, numpy scalar, pandas.Series, or numpy.ndarray
            yield factor

        yf: float, int, numpy scalar, pandas.Series, or numpy.ndarray
            year fraction
        """
        scalar_types = (int, float, integer, floating)
        array_types = (Series, ndarray)

        shapes = {}
        for name, value in [("f", f), ("yf", yf)]:
            assert isinstance(value, scalar_types + array_types), \
                f"`{name}` must be a float, a pandas.Series or a numpy.ndarray, " \
                f"got {type(value).__name__}"
            shapes[name] = () if isinstance(value, scalar_types) else value.shape

        assert shapes["f"] == shapes["yf"], \
            f"`f` and `yf` must have the same shape, " \
            f"got {shapes['f']} and {shapes['yf']}"

        if isinstance(f, Series) and isinstance(yf, Series):
            assert f.index.equals(yf.index), \
                "`f` and `yf` must share the same index"

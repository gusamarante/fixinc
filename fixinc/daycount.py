from fixinc.holidays import ANBIMA, USTrading
from pandas import to_datetime, Timestamp, Series
from numpy import (
    asarray,
    broadcast,
    busdaycalendar,
    busday_count,
    busday_offset,
    datetime64,
    ndarray,
)

class DayCount:
    # TODO test if daycounts are correct
    dibd = {
        "bus/252": 252,
        "act/365": 365,
        "act/360": 360,
    }
    dc_methods = [  # TODO separate types
        'act/act isda',
        'act/365',
        'act/360',
        'bus/252',
    ]
    roll_methods = ['following', 'preceding', 'modifiedfollowing', 'modifiedpreceding']
    weekmask = "Mon Tue Wed Thu Fri"

    def __init__(self, calendar=None, dcc='act/365', adj=None, adjust_offset=0):
        """
        Day-counting functionalities for fixed income.

        Parameters
        ----------
        calendar : str or None, optional
            Calendar identifier used to determine holidays. Supported values:
            - 'anbima' : Brazilian ANBIMA calendar
            - 'us_trading' : US trading calendar (general, not specific to any
                             exchange)
            - None: No holiday calendar (default)

        dcc: str
            Day count convention. Supported values:
            - 'act/365': Actual days over 365
            - 'act/360': Actual days over 360
            - 'bus/252': Business days over 252

        adj : str, optional
            Adjustment rule for rolling non-business days. If None, no rolling
            is applied. Supported values:
            - 'following': Adjusted date is the following business day
            - 'preceding': Adjusted date is the preceding business day
            - 'modifiedfollowing': Adjusted date is the following business day
                                   unless the day is in the next calendar month,
                                   in which case the adjusted date is the
                                   preceding business day
            - 'modifiedpreceding': Adjusted date is the preceding business day
                                   unless the day is in the previous calendar
                                   month, in which case the adjusted date is the
                                   following business day

        adjust_offset : int, default 0
            Additional offset (in business days) applied during adjustment
        """

        assert dcc.lower() in self.dc_methods, f"day count convention {dcc} not implemented"

        self.calendar = calendar
        self.dcc = dcc.lower()
        self.holidays = self._get_holidays()
        self.adj = adj
        self.adjust_offset = adjust_offset
        self.npcal = busdaycalendar(weekmask=self.weekmask, holidays=self.holidays)

    def adjust(self, d):
        """
        Adjust a given date according to the business day calendar and rolling
        rule

        Parameters
        ----------
        d: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Input date or dates to adjust
        """
        d = self._cast_numpy_date(d)
        if self.adj is None:
            return to_datetime(d)
        else:
            return to_datetime(busday_offset(d, offsets=self.adjust_offset, roll=self.adj, busdaycal=self.npcal))

    def days(self, d1, d2):
        """
        Compute the number of days between two dates under the selected day
        count convention

        Parameters
        ----------
        d1: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Start date(s)

        d2: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            End date(s)

        Returns
        -------
        int or numpy.ndarray
        """

        # Ensure dates are in the right format and properly rolled if necessary
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)

        if self.dcc == 'bus/252':
            d1 = self._cast_numpy_date(d1)
            d2 = self._cast_numpy_date(d2)
            return busday_count(d1, d2, weekmask=self.weekmask, holidays=self.holidays)

        elif self.dcc in ['act/act isda', 'act/360', 'act/365']:
            return self.daysnodc(d1, d2)

        else:
            raise NotImplementedError(f"day count convention not implemented in the `days` method")

    def days_in_base(self, d):
        """
        Number of days in the base of the day count convention.

        Parameters
        ----------
	    d: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Date to query
        """

        # Ensure dates are in the right format and properly rolled if necessary
        d = self.adjust(d)

        try:
            return self.dibd[self.dcc]  # TODO Modify in other places

        except KeyError:
            return self.days_in_year(d)

    def days_in_year(self, d):
        """
        Number of days in the year of the day `d`
        
        Parameters
        ----------
	    d: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Date to query
        """

        # Ensure dates are in the right format and properly rolled if necessary
        d = self.adjust(d)
        leap = self.is_leap_year(d)

        if isinstance(d, Timestamp):
            return 366 * leap + 365 * (not leap)
        else:
            return asarray(366 * leap + 365 * ~leap, dtype="int64")

    def is_leap_year(self, d):
        """
        Checks if the year of the day `d` is a leap year

        Parameters
        ----------
        d: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Date to query
        """

        # Ensure dates are in the right format and properly rolled if necessary
        d = self.adjust(d)

        if isinstance(d, Timestamp):
            year = d.year
            return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        else:
            year = asarray(d.year)
            return (year % 4 == 0) & (year % 100 != 0) | (year % 400 == 0)

    def daysnodc(self, d1, d2):
        """
        Compute the actual number of calendar days between two dates, ignoring
        the day count convention

        Parameters
        ----------
        d1: str, pandas.Timestamp, numpy.datetime64, or array-like
            Start date(s)

        d2: str, pandas.Timestamp, numpy.datetime64, or array-like
            End date(s)

        Returns
        -------
        int or numpy.ndarray
        """
        # Ensure dates are in the right format and properly rolled if necessary
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)

        if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
            return (d2 - d1).days
        else:
            return (d2 - d1).days.values

    def workday(self, d, offset=0):
        """
        Shift a date by a given number of business days, according to the
        configured calendar and rolling rule. Same behavior as the `WORKDAY`
        function from Microsoft Excel.

        Parameters
        ----------
        d: str, pandas.Timestamp, numpy.datetime64, or array-like
            Input date(s) to be shifted

        offset: int, or numpy.ndarray
            Number of business days to shift. If array-like, all values must
            have the same sign.

        Returns
        -------
        pandas.Timestamp or pandas.DatetimeIndex
        """
        d = self._cast_numpy_date(d)

        if self.adj is None and isinstance(offset, int):
            if offset >= 0:
                adj = "preceding"
            else:
                adj = "following"
            nd = busday_offset(d, offsets=offset, busdaycal=self.npcal, roll=adj)

        elif self.adj is None and (isinstance(offset, ndarray) or isinstance(offset, Series)):
            if all(offset >= 0):
                adj = "preceding"
            elif all(offset < 0):
                adj = "following"
            else:
                raise NotImplementedError("If offset is an array like structure, then all values must have the same sign")
            nd = busday_offset(d, offsets=offset, busdaycal=self.npcal, roll=adj)

        else:
            nd = busday_offset(d, offsets=offset, busdaycal=self.npcal, roll=self.adj)

        return to_datetime(nd)

    def year_fraction(self, d1, d2):
        """
        Compute the year fraction between two dates under the selected day
        count convention

        Parameters
        ----------
        d1: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            Start date(s)

        d2: str, pandas.Timestamp, pandas.Series, numpy.datetime64, or array-like
            End date(s)

        Returns
        -------
        float or numpy.ndarray
        """
        # Ensure dates are in the right format and properly rolled if necessary
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)

        if self.dcc == "act/act isda":
            if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
                # Handles the "scalar" case
                assert d1 <= d2, "First date must be smaller or equal to second date"

                if d1.year == d2.year:
                    yf = self.days(d1, d2) / self.days_in_base(d1)

                else:
                    ey1 = to_datetime(str(d1.year) + "-12-31")
                    ey2 = to_datetime(str(d2.year - 1) + "-12-31")
                    yf = (d2.year - d1.year - 1) + (self.days(d1, ey1) / self.days_in_base(d1)) + (self.days(ey2, d2) / self.days_in_base(d2))

            else:
                # Vectorized case is just a recursion calling the scalar case
                result = []
                f = result.append
                for t1, t2 in broadcast(d1, d2):
                    f(self.year_fraction(t1, t2))
                yf = asarray(result, dtype="float64")

        else:
            # Save adjustment state and set it to none, so we can safely use the
            # days and dib functions of "date splits" we produce in for some
            # day counts
            adj_state = self.adj
            self.adj = None
            yf  = self.days(d1, d2) / self.dibd[self.dcc]
            self.adj = adj_state

        return yf

    @staticmethod
    def _cast_numpy_date(d):
        d = to_datetime(d)

        # Convert to numpy format
        if not isinstance(d, Timestamp):
            d = d.values.astype("datetime64[D]")
        else:
            d = datetime64(d).astype("datetime64[D]")

        return d

    def _get_holidays(self):
        if self.calendar == "anbima":
            return list(ANBIMA().holidays().date)

        if self.calendar == "us_trading":
            return list(USTrading().holidays().date)

        elif self.calendar is None:
            return []
        else:
            raise NotImplementedError(f"calendar '{self.calendar}' not implemented")

from fixinc.holidays import ANBIMA, USTrading
from pandas import to_datetime, Timestamp, Series
from numpy import busday_offset, busdaycalendar, busday_count, datetime64, ndarray

class DayCount:
    # TODO document everything
    # TODO test with dates as strings, datetime and timestamp
    dibd = {
        "bus/252": 252,
        "act/365": 365,
        "act/360": 360,
    }
    dc_methods = ['act/365', 'act/360', 'bus/252']
    roll_methods = ['following', 'preceding', 'modifiedfollowing', 'modifiedpreceding']
    weekmask = "Mon Tue Wed Thu Fri"

    def __init__(self, calendar=None, dcc='act/365', adj=None, adjust_offset=0):

        assert dcc in self.dc_methods, f"day count convention {dcc} not implemented"

        self.calendar = calendar
        self.dcc = dcc.lower()
        self.holidays = self._get_holidays()
        self.adj = adj
        self.adjust_offset = adjust_offset
        self.npcal = busdaycalendar(weekmask=self.weekmask, holidays=self.holidays)

    def adjust(self, d):
        if self.adj is None:
            return to_datetime(d)
        else:
            return to_datetime(busday_offset(d, offsets=self.adjust_offset, roll=self.adj, busdaycal=self.npcal))

    def days(self, d1, d2):
        # Ensure dates are in the right format and properly rolled if necessary
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)

        if self.dcc == 'bus/252':
            d1 = self._cast_numpy_date(d1)
            d2 = self._cast_numpy_date(d2)
            return busday_count(d1, d2, weekmask=self.weekmask, holidays=self.holidays)

        elif self.dcc in ['act/360', 'act/365']:
            return self.daysnodc(d1, d2)

        else:
            raise NotImplementedError(f"day count convention not implemented in the `days` method")

    def daysnodc(self, d1, d2):
        # Ensure dates are in the right format and properly rolled if necessary
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)

        if isinstance(d1, Timestamp) and isinstance(d2, Timestamp):
            return (d2 - d1).days
        else:
            return (d2 - d1).days.values

    def workday(self, d, offset=0):
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
        # Ensure dates are in the right format and properly rolled if necessary
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)

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
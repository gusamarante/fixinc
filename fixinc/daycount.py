import pandas as pd

from fixinc.holidays import ANBIMA, USTrading
from pandas import to_datetime
from numpy import busday_offset, busdaycalendar, busday_count, datetime64

class DayCount:
    # TODO document everything
    # TODO test with dates as strings, datetime and timestamp
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
            # Convert to numpy format
            if not isinstance(d1, pd.Timestamp):
                d1 = d1.values.astype("datetime64[D]")
            else:
                d1 = datetime64(d1).astype("datetime64[D]")

            if not isinstance(d2, pd.Timestamp):
                d2 = d2.values.astype("datetime64[D]")
            else:
                d2 = datetime64(d2).astype("datetime64[D]")

            return busday_count(d1, d2, weekmask=self.weekmask, holidays=self.holidays)

        elif self.dcc in ['act/360', 'act/365']:
            return self.daysnodc(d1, d2)

        else:
            raise NotImplementedError(f"day count convention not implemented in the `days` method")

    def daysnodc(self, d1, d2):
        pass

    def _get_holidays(self):
        if self.calendar == "anbima":
            return list(ANBIMA().holidays().date)
        elif self.calendar is None:
            return []
        else:
            raise NotImplementedError(f"calendar '{self.calendar}' not implemented")


# ===== EXAMPLE =====
dct = DayCount(calendar="anbima", dcc='act/360')
# dct = DayCount(calendar=None, dcc='bus/252')
# print(list(dct.holidays))
# print(dct.adjust("2025-09-13"))
print(dct.days("2025-09-13", "2025-12-31"))
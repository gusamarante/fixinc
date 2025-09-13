from fixinc.holidays import ANBIMA, USTrading
from pandas import to_datetime
from numpy import busday_offset, busdaycalendar

class DayCount:
    # TODO document everything
    # TODO test with dates as strings, datetime and timestamp
    dc_methods = ['act/365', 'act/360', 'bus/252']
    roll_methods = ['following', 'preceding', 'modifiedfollowing', 'modifiedpreceding']

    def __init__(self, calendar=None, dcc='act/365', adj=None, adjust_offset=0):

        assert dcc in self.dc_methods, f"day count convention {dcc} not implemented"

        self.calendar = calendar
        self.dcc = dcc.lower()
        self.holidays = self._get_holidays()
        self.adj = adj
        self.adjust_offset = adjust_offset
        self.npcal = busdaycalendar(weekmask="Mon Tue Wed Thu Fri", holidays=self.holidays)

    def adjust(self, d):
        if self.adj is None:
            return to_datetime(d)
        else:
            return to_datetime(busday_offset(d, offsets=self.adjust_offset, roll=self.adj, busdaycal=self.npcal))

    def days(self, d1, d2):
        d1 = self.adjust(d1)
        d2 = self.adjust(d2)
        # TODO PAREI AQUI
        return

    def _get_holidays(self):
        if self.calendar == "anbima":
            return list(ANBIMA().holidays().date)
        elif self.calendar is None:
            return []
        else:
            raise NotImplementedError(f"calendar '{self.calendar}' not implemented")


# ===== EXAMPLE =====
dc = DayCount(calendar="anbima", dcc='bus/252', adj="following")
# dc = DayCount(calendar=None, dcc='bus/252')

# print(list(dc.holidays))

print(dc.adjust("2025-09-13"))
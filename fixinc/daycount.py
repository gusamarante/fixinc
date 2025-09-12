
class DayCount:

    def __init__(self, calendar=None, dcc='act/365'):
        self.calendar = calendar
        self.dcc = dcc.lower()
        self.holidays = self._get_holidays()

    def _get_holidays(self):
        return self.calendar  # TODO implement



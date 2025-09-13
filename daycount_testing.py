from fixinc import DayCount
import pandas as pd

calendars = [None, "anbima", "us_trading"]
conventions = ["act/360", "act/365", "bus/252"]
roll_adjustments = [None, "following", "preceding", "modifiedfollowing"]


for cal in calendars:
    for conv in conventions:
        for roll in roll_adjustments:
            dc = DayCount(calendar=cal, dcc=conv, adj=roll)

            print(f"Calendar {cal}, convention {conv}, roll adjustment {roll}")

            print(f"Adjusting a monday holiday in Brazil, {dc.adjust("2025-04-21")}")
            print(f"Adjusting a monday holiday in Brazil, {dc.adjust(pd.to_datetime("2025-04-21"))}")
            print(f"Adjusting a monday holiday in Brazil, {dc.adjust(pd.to_datetime(["2025-04-21", "2026-01-01"]))}")

            print(f"Days between 2025-12-31 and 2026-12-31, {dc.days("2025-12-31", "2026-12-31")}")
            print(f"Days between 2025-12-31 and 2026-12-31, {dc.days(pd.to_datetime("2025-12-31"), pd.to_datetime("2026-12-31"))}")
            print(f"Days between 2025-12-31 and 2026-12-31, {dc.days(pd.to_datetime(["2025-12-31", "2026-12-31"]), pd.to_datetime("2026-12-31"))}")
            print(f"Days between 2025-12-31 and 2026-12-31, {dc.days(pd.to_datetime("2025-12-31"), pd.to_datetime(["2026-12-31", "2027-12-31"]))}")
            print(f"Days between 2025-12-31 and 2026-12-31, {dc.days(pd.to_datetime(["2025-12-31", "2026-12-31"]), pd.to_datetime(["2026-12-31", "2027-12-31"]))}")

            print(f"year_factor 2025-12-31 and 2026-12-31, {dc.year_fraction("2025-12-31", "2026-12-31")}")
            print(f"year_factor 2025-12-31 and 2026-12-31, {dc.year_fraction(pd.to_datetime("2025-12-31"), pd.to_datetime("2026-12-31"))}")
            print(f"year_factor 2025-12-31 and 2026-12-31, {dc.year_fraction(pd.to_datetime(["2025-12-31", "2026-12-31"]), pd.to_datetime("2026-12-31"))}")
            print(f"year_factor 2025-12-31 and 2026-12-31, {dc.year_fraction(pd.to_datetime("2025-12-31"), pd.to_datetime(["2026-12-31", "2027-12-31"]))}")
            print(f"year_factor 2025-12-31 and 2026-12-31, {dc.year_fraction(pd.to_datetime(["2025-12-31", "2026-12-31"]), pd.to_datetime(["2026-12-31", "2027-12-31"]))}")

            print("\n")
"""
Creates the series the X-years ahead expectation of the selic.
"""
from fixinc.apis import BCBFocusScraper
import pandas as pd
from pandas.tseries.offsets import YearEnd

focus = BCBFocusScraper()
df = focus.run_scraper(
    bcb_table="anual",
    indicator="Selic",
    start_date="2007-01-01",
)

df = df[df["metric"] == 'median']
df = df[df["survey_type"] == 0]
df = df.pivot(index='date', columns='prediction_scope', values='value')

w_current_year = ((df.index + YearEnd(0)) - df.index).days / 365.25
w_next_year = 1 - w_current_year
current_year = df.index.year

selic_ahead = []
years_ahead = 4
for ya in range(1, years_ahead + 1):
    interpolated = pd.DataFrame()
    for t in df.index:
        interpolated.loc[t, "Current"] = df.loc[t, f"{t.year + ya - 1}"]
        interpolated.loc[t, "Next"] = df.loc[t, f"{t.year + ya}"]

    selic_ahead.append((interpolated["Current"] * w_current_year + interpolated["Next"] * w_next_year).rename(f"{ya}y ahead"))

selic_ahead = pd.concat(selic_ahead, axis=1)
selic_ahead.to_csv("facebook_selic_years_ahead.csv")

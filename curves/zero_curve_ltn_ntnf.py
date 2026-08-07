from data.readers import raw_ltn_ntnf
from fixinc import Bootstrap, LTN, NTNF, DayCount
import pandas as pd
from tqdm import tqdm
from utils import data_output


bltn = LTN()
bntn = NTNF()
dc = DayCount(calendar="anbima", dcc="bus/252")

df = raw_ltn_ntnf()

# Add a bond type column
bc = df["bond code"].str[:-3]
bc = bc.map({"BRSTNCNTF": "NTNF", "BRSTNCLTN": "LTN"})
df["bond type"] = bc


all_dates = sorted(df["reference date"].unique())
all_curves = []
for t in tqdm(all_dates):

    df_aux = df[df["reference date"] == t].set_index("bond code")

    all_cashflows = []
    all_prices = pd.Series()
    all_duration = pd.Series()

    for bc in df_aux.index:

        try:
            if df_aux.loc[bc, "bond type"] == "LTN":
                cf = bltn.get_cashflows(
                    t=df_aux.loc[bc, "reference date"],
                    mat=df_aux.loc[bc, "maturity"].strftime("%Y-%m"),
                )

            elif df_aux.loc[bc, "bond type"] == "NTNF":
                cf = bntn.get_cashflows(
                    t=df_aux.loc[bc, "reference date"],
                    mat=df_aux.loc[bc, "maturity"].year,
                )

            else:
                raise ValueError("Unknown bond type")

        except AssertionError:
            continue

        all_cashflows.append(cf.rename(bc))
        all_prices.loc[bc] = df_aux.loc[bc, "price"]
        all_duration.loc[bc] = df_aux.loc[bc, "duration"]

    all_cashflows = pd.concat(all_cashflows, axis=1, sort=False).fillna(0).sort_index()


    boot = Bootstrap(
        cashflows=all_cashflows,
        prices=all_prices,
        ref_date=t,
        durations=all_duration,
    )

    yc = boot.get_zero_curve("anbima", "bus/252", "compound")
    yc.index = dc.days(t, yc.index)
    all_curves.append(yc.rename(t))


all_curves = pd.concat(all_curves, axis=1).sort_index(axis=0).sort_index(axis=1).T

all_curves = all_curves.interpolate(method='index', axis=1, limit_area='inside')
max_months = int(all_curves.columns[-1] / 21)
desired_maturities = [21 * t for t in range(1, max_months)]
all_curves = all_curves[desired_maturities]
all_curves.columns = [f"{int(mat/21)}m" for mat in all_curves.columns]

all_curves.to_csv(data_output.joinpath('zero_ltn_ntnf_monthly_maturities.csv'))

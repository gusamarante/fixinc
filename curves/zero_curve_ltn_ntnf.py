from data.readers import raw_ltn_ntnf
from fixinc import Bootstrap, LTN, NTNF
import pandas as pd
from tqdm import tqdm


bltn = LTN()
bntn = NTNF()


df = raw_ltn_ntnf()

# Add a bond type column
bc = df["bond code"].str[:-3]
bc = bc.map({"BRSTNCNTF": "NTNF", "BRSTNCLTN": "LTN"})
df["bond type"] = bc


all_dates = sorted(df["reference date"].unique())

for t in tqdm(all_dates):

    df_aux = df[df["reference date"] == t].set_index("bond code")

    all_cashflows = []
    all_prices = pd.Series()
    all_duration = pd.Series()

    for bc in df_aux.index:

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

        all_cashflows.append(cf.rename(bc))
        all_prices.loc[bc] = df_aux.loc[bc, "price"]
        all_duration.loc[bc] = df_aux.loc[bc, "duration"]

    all_cashflows = pd.concat(all_cashflows, axis=1).fillna(0).sort_index()


    boot = Bootstrap(
        cashflows=all_cashflows,
        prices=all_prices,
        ref_date=t,
        durations=all_duration,
    )

    yc = boot.get_zero_curve("anbima", "bus/252", "compound")

    a = 1
"""
Builds Excess Return Indexes for the "Cupom Combial"
"""
from data.readers import ddi_raw
from utils import data_output
from tqdm import tqdm
import pandas as pd
import matplotlib.pyplot as plt
from fixinc import DayCount

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# User defined parameters
desired_duration = [0.5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8]  # in years
rebalance_window = 2  # in months  # TODO arrumar nos outros
start_date = '2006-06-01'
end_date = '2025-10-07'  # TODO remove this
index_start = 100

# Read the Data
dc = DayCount(calendar="anbima", dcc="bus/252")
ddi = ddi_raw()

# Set up
dates2loop = pd.to_datetime(ddi['reference_date'].unique())
dates2loop = dates2loop[dates2loop >= start_date]
dates2loop = dates2loop[dates2loop < end_date]  # TODO remove this

df_tracker = pd.DataFrame()  # To save all the final trackers



# ===== Backtests for each fixed duration =====
for dd in desired_duration:
    df_bt = pd.DataFrame()

    # First date
    aux_data = ddi[ddi['reference_date'] == dates2loop[0]]
    aux_data = aux_data.sort_values('du')
    aux_data = aux_data[aux_data["du"] != 0]

    # Select long contract
    aux_long = aux_data[aux_data['contract'].str.contains("F")]
    # aux_long = aux_long[aux_data['du'] >= rebalance_window * 21]
    aux_long = aux_long.set_index('contract')

    dur_idx = aux_long['du'].searchsorted(dd * 252)
    if dur_idx == 0:  # shortest contract is shorter than desired duration
        a = aux_long['du'].iloc[0]
        x = (dd * 252) / a  # Ammount of contract 1
        y = 0  # ammount of contract 2
        current_cont1, current_cont2 = aux_long['du'].index[0], None

    else:
        a = aux_long['du'].iloc[[dur_idx - 1, dur_idx]].values
        x = (dd * 252 - a[1]) / (a[0] - a[1])  # Ammount of contract 1
        y = 1 - x
        current_cont1, current_cont2 = aux_long['du'].iloc[[dur_idx - 1, dur_idx]].index

    df_bt.loc[dates2loop[0], 'contract 1'] = current_cont1
    df_bt.loc[dates2loop[0], 'contract 2'] = current_cont2

    df_bt.loc[dates2loop[0], 'quantity 1'] = (index_start * x) / aux_long['theoretical_price'].get(current_cont1, default=1)
    df_bt.loc[dates2loop[0], 'quantity 2'] = (index_start * y) / aux_long['theoretical_price'].get(current_cont2, default=1)  # Only defaults to 1 when current_cont2 is None and y is 0

    # Short contract
    aux_short = aux_data.iloc[0]
    df_bt.loc[dates2loop[0], 'contract short'] = aux_short.loc["contract"]

    pu_s = aux_short.loc["theoretical_price"]
    dc_s = aux_short.loc["dc"]

    pu_1 = aux_long.loc[current_cont1, "theoretical_price"]
    dc1 = aux_long["dc"].get(current_cont1, default=None) - dc_s
    fra1 = (pu_s / pu_1 - 1) * 360 / dc1
    qs1 = df_bt.loc[dates2loop[0], 'quantity 1'] / (1 + fra1 * (dc1 / 360))

    if current_cont2 is not None:
        pu_2 = aux_long.loc[current_cont2, "theoretical_price"]
        dc2 = aux_long["dc"].get(current_cont2, default=None) - dc_s
        fra2 = (pu_s / pu_2 - 1) * 360 / dc2
        qs2 = df_bt.loc[dates2loop[0], 'quantity 2'] / (1 + fra2 * (dc2 / 360))
    else:
        pu_2 = None
        dc2 = None
        fra2 = None
        qs2 = 0

    df_bt.loc[dates2loop[0], 'quantity short'] = qs1 + qs2

    df_bt.loc[dates2loop[0], 'Notional'] = index_start

    next_rebalance_date = dates2loop[0] + pd.DateOffset(days=dc_s - 3)

    # Loop for other dates
    paired_dates = zip(dates2loop[1:], dates2loop[:-1])
    for date, datem1 in tqdm(paired_dates, f'ERI DDI {dd}y'):
        # Compute PnL before rebalance
        aux_data = ddi[ddi['reference_date'] == date]
        aux_data = aux_data.sort_values('du')
        aux_data = aux_data.set_index('contract')

        pnl = df_bt.loc[datem1, 'quantity 1'] * aux_data['pnl'].get(df_bt.loc[datem1, 'contract 1'], default=0) \
            + df_bt.loc[datem1, 'quantity 2'] * aux_data['pnl'].get(df_bt.loc[datem1, 'contract 2'], default=0) \
            - df_bt.loc[datem1, 'quantity short'] * aux_data['pnl'].get(df_bt.loc[datem1, 'contract short'], default=0)

        df_bt.loc[date, 'Notional'] = df_bt.loc[datem1, 'Notional'] + pnl

        # Rebalance or Hold
        if date >= next_rebalance_date:
            # rebalance to target duration
            aux_data = aux_data.drop(df_bt.loc[datem1, 'contract short'], axis=0, errors="ignore")

            # Short contract
            aux_short = aux_data.iloc[0]
            df_bt.loc[date, 'contract short'] = aux_short.name

            pu_s = aux_short.loc["theoretical_price"]
            dc_s = aux_short.loc["dc"]

            # Select long contract
            aux_long = aux_data[aux_data.index.str.contains("F")]
            aux_long = aux_long[aux_long['dc'] > dc_s]

            dur_idx = aux_long['du'].searchsorted(dd * 252)
            if dur_idx == 0:  # shortest contract is shorter than desired duration
                a = aux_long['du'].iloc[0]
                x = (dd * 252) / a  # Ammount of contract 1
                y = 0  # ammount of contract 2
                current_cont1, current_cont2 = aux_long['du'].index[0], None

            else:
                a = aux_long['du'].iloc[[dur_idx - 1, dur_idx]].values
                x = (dd * 252 - a[1]) / (a[0] - a[1])  # Ammount of contract 1
                y = 1 - x
                current_cont1, current_cont2 = aux_long['du'].iloc[[dur_idx - 1, dur_idx]].index

            df_bt.loc[date, 'contract 1'] = current_cont1
            df_bt.loc[date, 'contract 2'] = current_cont2
            df_bt.loc[date, 'quantity 1'] = (x * df_bt.loc[date, 'Notional']) / aux_long['theoretical_price'].get(current_cont1, default=1)
            df_bt.loc[date, 'quantity 2'] = (y * df_bt.loc[date, 'Notional']) / aux_long['theoretical_price'].get(current_cont2, default=1)

            pu_1 = aux_long.loc[current_cont1, "theoretical_price"]
            dc1 = aux_long["dc"].get(current_cont1, default=None) - dc_s
            fra1 = (pu_s / pu_1 - 1) * (360 / dc1)
            qs1 = df_bt.loc[date, 'quantity 1'] / (1 + fra1 * (dc1 / 360))

            if current_cont2 is not None:
                pu_2 = aux_long.loc[current_cont2, "theoretical_price"]
                dc2 = aux_long["dc"].get(current_cont2, default=None) - dc_s
                fra2 = (pu_s / pu_2 - 1) * 360 / dc2
                qs2 = df_bt.loc[date, 'quantity 2'] / (1 + fra2 * (dc2 / 360))
            else:
                pu_2 = None
                dc2 = None
                fra2 = None
                qs2 = 0

            df_bt.loc[date, 'quantity short'] = qs1 + qs2

            # set next rebalance date
            next_rebalance_date = date + pd.DateOffset(days=dc_s - 3)

        else:
            df_bt.loc[date, 'contract 1'] = df_bt.loc[datem1, 'contract 1']
            df_bt.loc[date, 'contract 2'] = df_bt.loc[datem1, 'contract 2']
            df_bt.loc[date, 'contract short'] = df_bt.loc[datem1, 'contract short']

            df_bt.loc[date, 'quantity 1'] = df_bt.loc[datem1, 'quantity 1']
            df_bt.loc[date, 'quantity 2'] = df_bt.loc[datem1, 'quantity 2']
            df_bt.loc[date, 'quantity short'] = df_bt.loc[datem1, 'quantity short']

    df_bt.index = pd.to_datetime(df_bt.index)
    df_tracker = pd.concat([df_tracker, df_bt['Notional'].rename(f"FRC {dd}y")], axis=1)

# Standardize the tracker
df_tracker = 100 * df_tracker / df_tracker.iloc[0]


# ===== Save Trackers =====
df_tracker.to_csv(data_output.joinpath('trackers_frc.csv'))

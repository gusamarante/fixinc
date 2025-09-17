"""
All the functions in this file only work on my computer. These are outside the
`fixinc` library
"""
from tqdm import tqdm
import pandas as pd
from utils import file_path, data_reader


last_year = 2025  # Year of the last file available

# ======================
# ===== DI Futures =====
# ======================
def raw_di():
    data = pd.DataFrame()
    for year in tqdm(range(2006, last_year + 1), 'Reading DI files'):
        aux = pd.read_csv(file_path.joinpath(f'data_di1 {year}.csv'), sep=';')
        data = pd.concat([data, aux])

    data['reference_date'] = pd.to_datetime(data['reference_date'])
    data['maturity_date'] = pd.to_datetime(data['maturity_date'])
    data = data.drop('Unnamed: 0', axis=1)
    return data


# ================
# ===== NTNB =====
# ================
def raw_ntnb():
    ntnb = pd.DataFrame()
    for year in tqdm(range(2003, last_year + 1), 'Reading NTNB files'):
        aux = pd.read_csv(file_path.joinpath(f'data_ntnb {year}.csv'), sep=';')
        ntnb = pd.concat([ntnb, aux])

    ntnb['reference date'] = pd.to_datetime(ntnb['reference date'])
    ntnb['maturity'] = pd.to_datetime(ntnb['maturity'])
    ntnb = ntnb.drop(['Unnamed: 0', 'index'], axis=1)
    return ntnb


def trackers_ntnb():
    df = pd.read_csv(data_reader.joinpath("trackers_ntnb.csv"), index_col=0)
    # df = pd.read_csv("trackers_ntnb.csv", index_col=0)
    df.index = pd.to_datetime(df.index)
    return df


# ========================
# ===== NTNF and LTN =====
# ========================
def raw_ltn_ntnf():
    # Read the Data - LTN
    ltn = pd.DataFrame()
    for year in tqdm(range(2003, last_year + 1), 'Reading LTN files'):
        aux = pd.read_csv(file_path.joinpath(f'data_ltn {year}.csv'), sep=';')
        ltn = pd.concat([ltn, aux])

    ltn['reference date'] = pd.to_datetime(ltn['reference date'])
    ltn['maturity'] = pd.to_datetime(ltn['maturity'])
    ltn = ltn.drop(['Unnamed: 0', 'index'], axis=1)

    # Read the Data - NTNF
    ntnf = pd.DataFrame()
    for year in tqdm(range(2003, last_year + 1), 'Reading NTNF files'):
        aux = pd.read_csv(file_path.joinpath(f'data_ntnf {year}.csv'), sep=';')
        ntnf = pd.concat([ntnf, aux])

    ntnf['reference date'] = pd.to_datetime(ntnf['reference date'])
    ntnf['maturity'] = pd.to_datetime(ntnf['maturity'])
    ntnf = ntnf.drop(['Unnamed: 0', 'index'], axis=1)

    # Put both bonds together
    ntnf = pd.concat([ntnf, ltn])

    return ntnf

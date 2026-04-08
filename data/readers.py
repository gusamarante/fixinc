"""
All the functions in this file only work on my computer. These are outside the
`fixinc` library
"""
from tqdm import tqdm
import pandas as pd
from utils import file_path, data_reader, dropbox_path  # TODO Deal with the right level to call


last_year = 2026  # Year of the last file available

# ======================
# ===== DI Futures =====
# ======================
def di_raw():
    data = pd.DataFrame()
    for year in tqdm(range(2006, last_year + 1), 'Reading DI files'):
        aux = pd.read_csv(file_path.joinpath(f'data_di1 {year}.csv'), sep=';')
        data = pd.concat([data, aux])

    data['reference_date'] = pd.to_datetime(data['reference_date'])
    data['maturity_date'] = pd.to_datetime(data['maturity_date'])
    data['du'] = data['du'].astype(int)
    data = data.drop('Unnamed: 0', axis=1)
    return data

def trackers_di1():
    df = pd.read_csv(data_reader.joinpath("trackers_di1.csv"), index_col=0)
    df.index = pd.to_datetime(df.index)
    return df

def di_curve():
    df = pd.read_csv(
        data_reader.joinpath("di_monthly_maturities.csv"),
        index_col=0,
    )
    df.index = pd.to_datetime(df.index)
    return df


# =========================
# ===== Cupom Cambial =====
# =========================
def ddi_raw():
    data = pd.DataFrame()
    for year in tqdm(range(2006, last_year + 1), 'Reading DDI files'):
        aux = pd.read_csv(file_path.joinpath(f'data_ddi {year}.csv'), sep=';')
        data = pd.concat([data, aux])

    data['reference_date'] = pd.to_datetime(data['reference_date'])
    data['maturity_date'] = pd.to_datetime(data['maturity_date'])
    data['du'] = data['du'].astype(int)
    data["dc"] = (data["maturity_date"] - data["reference_date"]).dt.days
    data = data.drop('Unnamed: 0', axis=1)
    return data

def trackers_ddi():
    df = pd.read_csv(data_reader.joinpath("trackers_ddi.csv"), index_col=0)
    df.index = pd.to_datetime(df.index)
    return df


# ========================
# ===== FRA de Cupom =====
# ========================
def trackers_frc():
    df = pd.read_csv(data_reader.joinpath("trackers_frc.csv"), index_col=0)
    df.index = pd.to_datetime(df.index)
    return df


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

def vna_ntnb():
    df = raw_ntnb()
    df = df.pivot_table(index="reference date", values='vna', aggfunc='mean')['vna'].rename("VNA NTNB")
    return df

def trackers_ntnb():
    df = pd.read_csv(data_reader.joinpath("trackers_ntnb.csv"), index_col=0)
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


# ===============
# ===== LFT =====
# ===============
def raw_lft():
    lft = pd.DataFrame()
    for year in tqdm(range(2003, last_year + 1), 'Reading LFT files'):
        aux = pd.read_csv(file_path.joinpath(f'data_lft {year}.csv'), sep=';')
        lft = pd.concat([lft, aux])

    lft['reference date'] = pd.to_datetime(lft['reference date'])
    lft['maturity'] = pd.to_datetime(lft['maturity'])
    lft = lft.drop(['Unnamed: 0', 'index'], axis=1)
    return lft



# =======================
# ===== UST Futures =====
# =======================
def trackers_ustf():
    df = pd.read_csv(data_reader.joinpath("UST Futures.csv"), index_col=0, sep=';')
    df.index = pd.to_datetime(df.index)
    df = df[['2y Note', '5y Note', '10y Note', '10y Note Ultra', '30y Bond', '30y Bond Ultra']]

    dur = pd.Series(  # Average Duration
        data={
            '2y Note': 1.9,
            '5y Note': 4.1,
            '10y Note': 6,
            '10y Note Ultra': 7.8,
            '30y Bond': 12,
            '30y Bond Ultra': 15.3
        },
    )
    return df, dur


# =====================
# ===== BCB Focus =====
# =====================
def selic_years_ahead():
    data = pd.read_csv(
        data_reader.joinpath(f'focus_selic_years_ahead.csv'),
        index_col="Date",
    )
    data.index = pd.to_datetime(data.index)
    return data


# ===============
# ===== CDS =====
# ===============
def cds_sov():
    data = pd.read_csv(
        dropbox_path.joinpath(f'data_cds.csv'),
        sep=";",
        index_col="date",
    )
    data.index = pd.to_datetime(data.index)
    data.columns = data.columns.str.replace("CDS ", "")
    return data

def cds_idx():
    data = pd.read_csv(
        dropbox_path.joinpath(f'data_cds_index.csv'),
        sep=";",
        index_col=0,
    )
    data.index = pd.to_datetime(data.index)
    return data

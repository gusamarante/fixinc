from getpass import getuser
from pathlib import Path
import pandas as pd
from tqdm import tqdm

file_path = Path(f"/Users/{getuser()}/Dropbox/Lectures/Fixed Income/Data")

df = pd.DataFrame()

for year in tqdm(range(2003, 2026)):
    aux = pd.read_csv(file_path.joinpath(f"data_ntnb {year}.csv"), sep=";")
    df = pd.concat([df, aux])

df = df[['maturity', 'bond code']].drop_duplicates(keep='last').sort_values(by='maturity')
df.to_clipboard()
print(df)

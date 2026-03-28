from getpass import getuser
from pathlib import Path

file_path = Path(f"/Users/{getuser()}/PycharmProjects/fixinc/data/inputs")
figure_path = Path(f"/Users/{getuser()}/Dropbox/Lectures/Fixed Income/figures")
dropbox_path = Path(f"/Users/{getuser()}/Dropbox/Lectures/Data")
data_output = Path("../data/")
data_reader = Path("../../data/")

BLUE = "#3333B2"
RED = "#FB4D3D"
GREEN = "#6CAE75"
YELLOW = "#F0A202"

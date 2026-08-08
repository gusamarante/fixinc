from pathlib import Path

# Root of the repository, taken from the location of this file, so that the
# paths below do not depend on the directory the calling script is run from
root_path = Path(__file__).resolve().parent

# Paths inside the repository
file_path = root_path.joinpath("data", "inputs")
data_output = root_path.joinpath("data")
data_reader = root_path.joinpath("data")

# Paths outside the repository, on the user's home directory
figure_path = Path.home().joinpath("Dropbox", "Lectures", "Fixed Income", "figures")
dropbox_path = Path.home().joinpath("Dropbox", "Lectures", "Data")  # TODO This folder does not exist, `cds_sov` and `cds_idx` readers are broken

BLUE = "#3333B2"
RED = "#FB4D3D"
GREEN = "#6CAE75"
YELLOW = "#F0A202"

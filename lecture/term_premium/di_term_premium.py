import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import ScalarFormatter

from data.readers import selic_years_ahead, di_curve
from fixinc import ZeroCurve
from utils import figure_path


# =========================
# ===== Survey Method =====
# =========================
exp_selic = selic_years_ahead() / 100
exp_selic.columns = exp_selic.columns.str.replace("y ahead", "").astype(int)

zc_data = di_curve()
zc_data.columns = zc_data.columns.str.replace("m", "").astype(int) / 12

zc = ZeroCurve(zc_data)
fra = pd.concat(
    [
        zc.forward(t1=(y * 12 - 1) / 12, t2=y).rename(y)
        for y in range(1, 5)
    ],
    axis=1,
)

tp_survey = (fra - exp_selic).dropna()
tp_survey.columns = tp_survey.columns.astype(str) + "y"

# --- Chart ---
size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))
ax.set_title("Survey-Based Term Premium - Brazilian Focus Survey")
ax.plot(tp_survey, label=tp_survey.columns)
ax.axhline(0, color="black", lw=0.5)
ax.xaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", linestyle="-", linewidth=0.5, alpha=0.5, which="both")
ax.set_ylabel("DI FRAs minus expected Selic")
ax.get_yaxis().set_major_formatter(ScalarFormatter())
locators = mdates.YearLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(rotation=90, axis="x")
ax.legend(frameon=True, loc="best")

plt.tight_layout()

plt.savefig(figure_path.joinpath("Term Premium - DI Survey.pdf"))
plt.show()
plt.close()

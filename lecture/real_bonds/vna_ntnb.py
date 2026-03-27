import pandas as pd
from data.readers import vna_ntnb
import matplotlib.pyplot as plt
from utils import BLUE, RED, figure_path
import matplotlib.dates as mdates


vna = vna_ntnb()


# =================
# ===== CHART =====
# =================
start_date = mdates.date2num(pd.to_datetime("2017-01-01"))
end_date = mdates.date2num(pd.to_datetime("2017-12-31"))
width = end_date - start_date

y1 = vna[("2017-01-01" <= vna.index) & (vna.index <= "2017-12-31")].min() * 0.998
y2 = vna[("2017-01-01" <= vna.index) & (vna.index <= "2017-12-31")].max() * 1.002
height = y2 - y1

size = 5
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 2), (0, 0))
ax.plot(vna, color=BLUE, label="VNA NTN-B")
rect = plt.Rectangle((start_date, y1), width, height, facecolor=RED, alpha=0.5)
ax.add_patch(rect)
ax.xaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
ax.set_title("VNA - NTN-B")


ax = plt.subplot2grid((1, 2), (0, 1))
ax.plot(vna[("2017-01-01" <= vna.index) & (vna.index <= "2017-12-31")], color=BLUE, label="VNA NTN-B")
rect = plt.Rectangle((start_date, y1), width, height, facecolor=RED, alpha=0.2)
ax.add_patch(rect)
ax.set(xlim=(start_date, end_date), ylim=(y1, y2))
locators = mdates.MonthLocator()
ax.xaxis.set_major_locator(locators)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
ax.tick_params(rotation=90, axis="x")
ax.xaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
ax.yaxis.grid(color="grey", ls="-", lw=0.5, alpha=0.5)
ax.set_title("VNA - NTN-B (Zoomed in)")

plt.tight_layout()
plt.savefig(figure_path.joinpath("NTNB - VNA and Zoom.pdf"))
plt.show()
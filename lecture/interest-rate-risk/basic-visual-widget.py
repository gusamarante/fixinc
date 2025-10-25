"""
Basic visualizations of interest rate risk
"""

import matplotlib.pyplot as plt
from matplotlib.pylab import Slider
import pandas as pd
import numpy as np
from utils import RED, BLUE


start_coupon = 120
start_face_value = 1000
start_years = 5
start_ytm = 0.05

def cf(coupon, face_value, years, ytm):
    cfs = {
        t + 1: coupon for t in range(years)
    }
    cfs[years] = cfs[years] + face_value
    cfs = pd.Series(cfs)

    disc = (1 + ytm) ** (-cfs.index)
    macdur = (cfs * disc * cfs.index).sum() / (cfs * disc).sum()

    cfs.loc[0] = - (cfs * disc).sum()
    cfs = cfs.sort_index()

    return cfs.index, cfs.values, macdur


def make_cf_plot(mpl_ax, coupon, face_value, years, ytm):
    Tplot, CFplot, MacDur = cf(coupon, face_value, years,ytm)
    bars = mpl_ax.bar(Tplot, CFplot, width=0.5, color=BLUE, label="Cashflows")
    mpl_ax.axhline(0, color="black", lw=0.5)
    mpl_ax.bar_label(bars, padding=1)
    mpl_ax.axvline(MacDur, ls='--', color=RED, label=f"Macaulay Duration = {MacDur:.2f}", lw=2)
    mpl_ax.yaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
    mpl_ax.xaxis.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
    mpl_ax.set_ylabel("Cashflows")
    mpl_ax.set_xlabel("Years")
    mpl_ax.legend(frameon=True, loc='upper left')

def make_dv_plot(mpl_ax, coupon, face_value, years, ytm):
    pass


# =================
# ===== Chart =====
# =================
size = 8
fig = plt.figure(figsize=(size * 1.61, size))

# Curves
ax1 = plt.subplot2grid((8, 4), (0, 0), rowspan=4, colspan=2)
make_cf_plot(ax1, start_coupon, start_face_value, start_years,start_ytm)

# Price-yield + DV01


# Sliders
ax_T = plt.subplot2grid((8, 4), (4, 1), colspan=2)
slide_T = Slider(
    ax=ax_T,
    label=r"Years to Maturity  $T$",
    valmin=1,
    valinit=start_years,
    valmax=20,
    valstep=1,
)

ax_coupon = plt.subplot2grid((8, 4), (5, 1), colspan=2)
slide_coupon = Slider(
    ax=ax_coupon,
    label=r"Yearly Coupon",
    valmin=0,
    valinit=start_coupon,
    valmax=1000,
    valstep=1,
)

ax_fv = plt.subplot2grid((8, 4), (6, 1), colspan=2)
slide_fv = Slider(
    ax=ax_fv,
    label=r"Face Value",
    valmin=0,
    valinit=start_face_value,
    valmax=2000,
    valstep=1,
)

ax_ytm = plt.subplot2grid((8, 4), (7, 1), colspan=2)
slide_ytm = Slider(
    ax=ax_ytm,
    label=r"Yield to Maturity $y$",
    valmin=-0.1,
    valinit=start_ytm,
    valmax=0.5,
    valstep=0.005,
)

def update(val):
    new_T = slide_T.val
    new_coupon = slide_coupon.val
    new_fv = slide_fv.val
    new_ytm = slide_ytm.val

    ax1.cla()
    make_cf_plot(ax1, new_coupon, new_fv, new_T, new_ytm)


slide_T.on_changed(update)
slide_coupon.on_changed(update)
slide_fv.on_changed(update)
slide_ytm.on_changed(update)


plt.tight_layout()
plt.show()


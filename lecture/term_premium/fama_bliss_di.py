"""
replicates the fama-bliss study for DI futures
"""
from data.readers import di_curve
from fixinc import CurvePCA
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from utils import figure_path, BLUE, RED
import numpy as np

size = 5

curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)

curve = curve.resample("YE").last()  # TODO maybe change to ME?
columns2keep = [12 * y for y in range(1, 11)]
curve = curve[columns2keep]

pu = 1 / ((1 + curve) ** (curve.columns.astype(int) * 21 / 252))
lnpu = np.log(pu)
rf = - lnpu[12]
fra = ((pu / pu.shift(-1, axis=1)) - 1).shift(1, axis=1)  # No exponent adjustment because rates are 1y apart

hpr = (lnpu - lnpu.shift(1, axis=0).shift(-1, axis=1)).shift(1, axis=1)
ehpr = hpr.sub(rf.shift(1), axis=0)  # Dependent variables of table 1
framrf = fra.sub(rf, axis=0).shift(1)  # Independent variables of table 1

for mat in columns2keep[1:]:
    pass
    # TODO run regression of ehpr[mat] on framrf[mat] and constant, store results

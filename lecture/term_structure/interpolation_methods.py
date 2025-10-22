from data.readers import di_curve
from fixinc import ZeroCurve

zc_data = di_curve()
zc_data.columns = zc_data.columns.str.replace("m", "").astype(int) / 12
zc = ZeroCurve(zc_data)
interp = zc.interpolator("2025-08-28", method="linear")

print(interp(10))
# TODO parei aqui
import pandas as pd
from fixinc import ZeroCurve

zc_data = pd.DataFrame(
    data={
        1: 0.0526,
        2: 0.0770,
        3: 0.1236,
    },
    index=[pd.to_datetime("2025-01-01")]
)
zc = ZeroCurve(zc_data)
interp = zc.interpolate(
    ref_date="2025-01-01",
    mat=2.5,
    method="flat-forward",
    # method="linear",
)

print(interp)
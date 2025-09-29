"""
PCA applied to the DI Curve
"""

from data.readers import di_curve

curve = di_curve()
curve = curve[curve.index >= '2007-03-16']  # When the continuous 10y starts
curve = curve.dropna(axis=1)
curve.columns = curve.columns.str.replace("m", "").astype(int)


# TODO Função para PCA na curva de juros
# TODO gráfico dos fatores
# TODO gráfico dos loadings
# TODO gráfico da variância explicada
from data.readers import cds_sov
import matplotlib.pyplot as plt
from utils import figure_path
from fixinc import Performance
from plottable import ColDef, Table

df = cds_sov()

perf = Performance(df, skip_dd=True)

# =============================
# ===== Performance Table =====
# =============================
size = 7
fig = plt.figure(figsize=(size * (16 / 7.3), size))

ax = plt.subplot2grid((1, 1), (0, 0))

df2plot = perf.table.copy().T.sort_values("Sharpe", ascending=False)
df2plot = df2plot.drop(["Start Date", "Sortino"], axis=1)
df2plot = df2plot.astype(float)
df2plot.index.name = "Country"

tab = Table(
    df2plot,
    ax=ax,
    footer_divider=True,
    textprops={"fontsize": 11},
    column_definitions=[
        ColDef(name="Country", textprops={"ha": "left", "weight": "bold"}),
        ColDef(name="Return", textprops={"ha": "center"}, formatter="{:.2%}"),
        ColDef(name="Vol", textprops={"ha": "center"}, formatter="{:.2%}"),
        ColDef(name="Sharpe", textprops={"ha": "center"}, formatter="{:.2f}"),
        ColDef(name="Skew", textprops={"ha": "center"}, formatter="{:.2f}"),
        ColDef(name="Kurt", textprops={"ha": "center"}, formatter="{:.2f}"),
        ColDef(name="Max DD", textprops={"ha": "center"}, formatter="{:.2%}"),
    ],
)

for col in range(tab.col_label_row.get_xrange()[1]):
    tab.col_label_row.cells[col].text.set_weight("bold")

plt.tight_layout()

plt.savefig(figure_path.joinpath("CDS - Sovereign Performance Table.pdf"))
plt.show()
plt.close()
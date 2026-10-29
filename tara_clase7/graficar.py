"""La figura del informe: aciertos, errores y «no sé» por modo, a partir de uno o más CSV de evaluar.py.

    uv run graficar.py                                          # resultados.csv
    uv run graficar.py resultados.csv resultados_sin_null.csv   # base + experimento extra
"""
import sys
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AQUI = Path(__file__).parent
COLORES = {"acierta": "#0ca30c", "no sabe": "#c3c2b7", "se equivoca": "#d03b3b"}   # estados: bien, neutro, mal
ORDEN = ["memoria", "memoria sin null", "web", "mcp"]                              # de arriba hacia abajo
SUPERFICIE, TINTA, TINTA_2, MUTED, GRILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"

archivos = sys.argv[1:] or [AQUI / "resultados.csv"]
res = pd.concat([pd.read_csv(f) for f in archivos], ignore_index=True)
conteo = res.groupby("modo").resultado.value_counts().unstack(fill_value=0)
conteo = conteo.reindex(columns=[c for c in COLORES if c in conteo.columns])
modos = [m for m in ORDEN if m in conteo.index] + sorted(set(conteo.index) - set(ORDEN))
conteo = conteo.loc[modos[::-1]]                       # barh dibuja de abajo hacia arriba
n = conteo.sum(axis=1)
segundos = res.groupby("modo").segundos.mean()

fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150, facecolor=SUPERFICIE)
ax.set_facecolor(SUPERFICIE)
izquierda = pd.Series(0.0, index=conteo.index)
for col in conteo.columns:
    ancho = conteo[col] / n * 100
    ax.barh(range(len(conteo)), ancho, left=izquierda, height=0.55, color=COLORES[col], label=col,
            edgecolor=SUPERFICIE, linewidth=2)
    for i, modo in enumerate(conteo.index):
        if conteo.loc[modo, col] and ancho[modo] >= 8:
            ax.text(izquierda[modo] + ancho[modo] / 2, i, f"{conteo.loc[modo, col]}/{n[modo]}",
                    ha="center", va="center", color=TINTA, fontsize=9)
    izquierda += ancho

ax.set_yticks(range(len(conteo)), [f"{m}\n{segundos[m]:.1f} s por pregunta" for m in conteo.index],
              color=TINTA_2, fontsize=9)
ax.set_xlim(0, 100)
ax.set_xticks(range(0, 101, 25), [f"{x} %" for x in range(0, 101, 25)], color=MUTED, fontsize=8)
ax.xaxis.grid(True, color=GRILLA, linewidth=0.8)
ax.set_axisbelow(True)
ax.tick_params(length=0)
for lado in ax.spines.values():
    lado.set_visible(False)
ax.set_title("¿Acierta Claude (Haiku) cifras oficiales del BCRP?", loc="left", fontsize=12, color=TINTA)
ax.legend(ncol=3, loc="upper left", bbox_to_anchor=(0, -0.14), frameon=False, fontsize=9, labelcolor=TINTA_2)
fig.tight_layout()
fig.savefig(AQUI / "grafico.png", facecolor=SUPERFICIE)
print(conteo.loc[modos].to_string())

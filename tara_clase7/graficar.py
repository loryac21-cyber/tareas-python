"""La figura del informe: aciertos, errores y «no sé» por modo, a partir de resultados.csv.

    uv run graficar.py                       # escribe grafico.png
    uv run graficar.py resultados_base.csv   # otra corrida
"""
import sys
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AQUI = Path(__file__).parent
COLORES = {"acierta": "#2E7D5B", "no sabe": "#B8AE9F", "se equivoca": "#B4441A"}

res = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else AQUI / "resultados.csv")
tabla = res.groupby("modo").resultado.value_counts(normalize=True).unstack(fill_value=0) * 100
tabla = tabla.reindex(columns=[c for c in COLORES if c in tabla.columns])
segundos = res.groupby("modo").segundos.mean()
n = res.groupby("modo").size()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
izquierda = pd.Series(0.0, index=tabla.index)
for col in tabla.columns:
    ax.barh(tabla.index, tabla[col], left=izquierda, color=COLORES[col], label=col)
    for modo, v in tabla[col].items():
        if v >= 8:
            ax.text(izquierda[modo] + v / 2, modo, f"{v:.0f} %", ha="center", va="center", color="white", fontsize=10)
    izquierda += tabla[col]
ax.set_yticks(range(len(tabla)), [f"{m}\n{segundos[m]:.1f} s · {n[m]} preguntas" for m in tabla.index])
ax.set_xlim(0, 100)
ax.set_xlabel("% de preguntas")
ax.set_title("¿Acierta Claude cifras del BCRP? Haiku, mismas preguntas por modo", loc="left", fontsize=12)
ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.32), frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(AQUI / "grafico.png")
print(tabla.round(1).to_string())

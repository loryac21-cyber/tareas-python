"""Imágenes de cada escena del reel (900 x 620 px, fondo oscuro) a partir de los datos procesados.

    uv run python reel/generar_recursos.py

Escribe reel/recursos/escena_*.png. La escena 6 usa la captura del dashboard (figuras/dashboard_kpis.jpg).
"""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageDraw

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
RECURSOS = AQUI / "recursos"
RECURSOS.mkdir(exist_ok=True)

ANCHO, ALTO = 900, 620
FONDO, TEXTO, SUAVE, CAJA = "#1C1A17", "#F7F3EC", "#B8AE9F", "#2A2723"
# Paleta del dashboard en modo oscuro
PRECIO, VOLUMEN, VALOR, REFERENCIA, REJILLA = "#d95926", "#3987e5", "#199e70", "#898781", "#34312c"
COLORES_REGION = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"]
GRUPOS = ["Unión Europea", "Resto de Europa", "Norteamérica", "América Latina y el Caribe", "Asia y Medio Oriente", "Otros"]

P = RAIZ / "datos" / "procesados"
ind = pd.read_csv(P / "indicadores_anuales.csv")
anual = ind.query("periodo == 'anual' and anio >= 2015").set_index(["producto", "anio"])
ventanas = pd.read_csv(P / "descomposicion_ventanas.csv").set_index(["producto", "desde", "hasta"])
mensual = pd.read_csv(P / "precio_y_valor_unitario_mensual.csv")
regiones = pd.read_csv(P / "exportaciones_por_region.csv").query("periodo == 'anual'")
INICIO, FIN = 2015, int(anual.index.get_level_values("anio").max())

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 17, "text.color": TEXTO,
    "axes.facecolor": FONDO, "figure.facecolor": FONDO, "savefig.facecolor": FONDO,
    "axes.edgecolor": REFERENCIA, "axes.labelcolor": SUAVE, "xtick.color": SUAVE, "ytick.color": SUAVE,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": REJILLA, "grid.linewidth": 1, "axes.axisbelow": True,
    "xtick.labelsize": 16, "ytick.labelsize": 16, "legend.frameon": False, "legend.fontsize": 17,
})


def es(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def figura():
    return plt.subplots(figsize=(ANCHO / 100, ALTO / 100), dpi=100)


def guardar(fig, nombre):
    fig.savefig(RECURSOS / nombre, dpi=100)
    plt.close(fig)
    print("ok", nombre)


def indice_valor_volumen(producto, nombre):
    """Valor FOB y volumen con base 2015 = 1, con la etiqueta del múltiplo al final de cada línea."""
    a = anual.loc[producto]
    valor, volumen = a.fob / a.fob.iloc[0], a.kg / a.kg.iloc[0]
    fig, ax = figura()
    for serie, color, etiqueta in ((valor, VALOR, "Valor FOB"), (volumen, VOLUMEN, "Volumen")):
        ax.plot(serie.index, serie, color=color, lw=5, marker="o", ms=9, label=etiqueta)
        ax.annotate(f"x{es(serie.iloc[-1], 1)}", (serie.index[-1], serie.iloc[-1]), xytext=(12, 0), textcoords="offset points",
                    va="center", fontsize=26, fontweight="bold", color=TEXTO)
    ax.axhline(1, color=REFERENCIA, lw=1.5)
    ax.set_xlim(INICIO - 0.4, FIN + 1.6)
    ax.set_ylim(0, valor.max() * 1.15)
    ax.set_xticks(range(INICIO, FIN + 1, 2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: es(v, 1)))
    ax.set_title(f"{producto} exportado ({INICIO} = 1)", loc="left", fontsize=18, color=SUAVE, pad=12)
    ax.legend(loc="upper left")
    fig.tight_layout()
    guardar(fig, nombre)


# Escena 1 · café: valor frente a volumen
indice_valor_volumen("Café", "escena_1_cafe_valor_volumen.png")

# Escena 2 · ¿precio o volumen? 2015 -> FIN, café y cacao
fig, ax = figura()
productos = ["Cacao", "Café"]
for y, prod in enumerate(productos):
    v = ventanas.loc[(prod, INICIO, FIN)]
    precio, volumen = v.efecto_precio / 1e6, v.efecto_volumen / 1e6
    ax.barh(y, precio, color=PRECIO, height=0.55, edgecolor=FONDO, linewidth=2, label="Por precio" if y == 0 else None)
    ax.barh(y, volumen, left=precio, color=VOLUMEN, height=0.55, edgecolor=FONDO, linewidth=2, label="Por volumen" if y == 0 else None)
    ax.text(precio / 2, y, f"{es(v.part_precio)} %", ha="center", va="center", fontsize=24, fontweight="bold", color="#ffffff")
    ax.text(precio + volumen / 2, y, f"{es(100 - v.part_precio)} %", ha="center", va="center", fontsize=24, fontweight="bold", color="#ffffff")
    ax.text(precio + volumen + 25, y, f"+US$ {es(v.cambio_fob / 1e6)} M", va="center", fontsize=19, color=TEXTO)
ax.set_yticks(range(len(productos)), productos, fontsize=21, color=TEXTO)
ax.grid(False)
ax.spines["bottom"].set_visible(False)
ax.set_xticks([])
ax.set_xlim(0, max(ventanas.loc[(p, INICIO, FIN)].cambio_fob for p in productos) / 1e6 * 1.35)
ax.set_title(f"Aumento del valor exportado, {INICIO}–{FIN}", loc="left", fontsize=18, color=SUAVE, pad=12)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), ncols=2)
fig.tight_layout()
guardar(fig, "escena_2_precio_o_volumen.png")

# Escena 3 · cacao: valor frente a volumen
indice_valor_volumen("Cacao", "escena_3_cacao_valor_volumen.png")

# Escena 4 · cacao: precio internacional y valor unitario, 2023 en adelante
s = mensual[(mensual.producto == "Cacao") & (mensual.anio >= 2023)].copy()
s["fecha"] = pd.to_datetime(dict(year=s.anio, month=s.mes, day=15))
fig, ax = figura()
ax.plot(s.fecha, s.precio_int, color=REFERENCIA, lw=4, ls="--", label="Precio internacional (ICCO)")
ax.plot(s.fecha, s.vu_base.where(s.kg_base >= 100_000), color=PRECIO, lw=5, label="Valor unitario del cacao peruano")
pico = s.loc[s.precio_int.idxmax()]
ultimo = s.dropna(subset=["precio_int"]).iloc[-1]
MESES_CORTOS = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "set.", "oct.", "nov.", "dic."]
for fila, xytext, ha in ((pico, (18, 6), "left"), (ultimo, (0, 18), "right")):
    ax.annotate(f"ICCO {MESES_CORTOS[int(fila.mes) - 1]} {int(fila.anio)}: {es(fila.precio_int, 2)}", (fila.fecha, fila.precio_int),
                xytext=xytext, textcoords="offset points", ha=ha, va="bottom", fontsize=19, fontweight="bold", color=TEXTO)
ax.set_ylim(0, s.precio_int.max() * 1.25)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:.0f}"))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_title("Cacao, US$/kg por mes", loc="left", fontsize=18, color=SUAVE, pad=12)
ax.legend(loc="upper left", fontsize=15)
fig.tight_layout()
guardar(fig, "escena_4_cacao_precio.png")

# Escena 5 · regiones de destino, 2015 frente a FIN
reg = regiones.assign(grupo=regiones.region.where(regiones.region.isin(GRUPOS), "Otros")).groupby(["producto", "anio", "grupo"]).fob.sum()
reg = (reg / reg.groupby(level=["producto", "anio"]).transform("sum") * 100).unstack("grupo")[GRUPOS].fillna(0)
filas = [("Cacao", FIN), ("Cacao", INICIO), ("Café", FIN), ("Café", INICIO)]
fig, ax = figura()
izquierda = [0.0] * len(filas)
for g, color in zip(GRUPOS, COLORES_REGION):
    valores = [reg.loc[f, g] for f in filas]
    ax.barh(range(len(filas)), valores, left=izquierda, color=color, height=0.62, edgecolor=FONDO, linewidth=2,
            label=g.replace("América Latina y el Caribe", "América Latina").replace("Asia y Medio Oriente", "Asia"))
    for y, (v, x0) in enumerate(zip(valores, izquierda)):
        if g == "Unión Europea":
            ax.text(x0 + v / 2, y, f"{es(v)} %", ha="center", va="center", fontsize=19, fontweight="bold", color="#ffffff")
    izquierda = [a + b for a, b in zip(izquierda, valores)]
ax.set_yticks(range(len(filas)), [f"{p} {a}" for p, a in filas], fontsize=19, color=TEXTO)
ax.set_xlim(0, 100)
ax.grid(False)
ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.set_title("¿A qué regiones se vende? % del valor FOB", loc="left", fontsize=18, color=SUAVE, pad=12)
ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.01), ncols=3, fontsize=14, handlelength=1, columnspacing=1)
fig.tight_layout()
guardar(fig, "escena_5_regiones.png")

# Escena 6 · captura del dashboard
captura = Image.open(RAIZ / "figuras" / "dashboard_kpis.jpg").convert("RGB")
captura.thumbnail((ANCHO - 24, ALTO - 24))
lienzo = Image.new("RGB", (ANCHO, ALTO), FONDO)
x, y = (ANCHO - captura.width) // 2, (ALTO - captura.height) // 2
mascara = Image.new("L", captura.size, 0)
ImageDraw.Draw(mascara).rounded_rectangle((0, 0, *captura.size), radius=18, fill=255)
lienzo.paste(captura, (x, y), mascara)
lienzo.save(RECURSOS / "escena_6_dashboard.png")
print("ok escena_6_dashboard.png")

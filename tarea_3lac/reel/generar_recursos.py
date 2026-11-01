"""Imágenes de cada escena del reel (900 x 620 px, fondo oscuro) a partir de los datos procesados.

    uv run python reel/generar_recursos.py

Escribe reel/recursos/escena_*.png. El mapa usa Plotly + Kaleido (necesita Chrome instalado).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from PIL import Image, ImageDraw

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
RECURSOS = AQUI / "recursos"
RECURSOS.mkdir(exist_ok=True)

ANCHO, ALTO = 900, 620
FONDO, TEXTO, SUAVE, ACENTO, CAJA = "#1C1A17", "#F7F3EC", "#B8AE9F", "#F08A4B", "#2A2723"
COLOR = {"Café": "#d95926", "Cacao": "#3987e5", "Madera": "#199e70"}
UE, RESTO, REJILLA = "#3987e5", "#6f6d68", "#34312c"

mensual = pd.read_csv(RAIZ / "datos" / "procesados" / "exportaciones_eudr_mensual.csv", dtype={"subpartida": str})
ind = pd.read_csv(RAIZ / "datos" / "procesados" / "indicadores_anuales_producto.csv").query("periodo == 'anual'")
ULTIMO = int(ind.anio.max())

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 17, "text.color": TEXTO,
    "axes.facecolor": FONDO, "figure.facecolor": FONDO, "savefig.facecolor": FONDO,
    "axes.edgecolor": RESTO, "axes.labelcolor": SUAVE, "xtick.color": SUAVE, "ytick.color": SUAVE,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": REJILLA, "grid.linewidth": 1,
    "xtick.labelsize": 16, "ytick.labelsize": 16, "legend.frameon": False, "legend.fontsize": 17,
})


def figura():
    return plt.subplots(figsize=(ANCHO / 100, ALTO / 100), dpi=100)


def guardar(fig, nombre):
    fig.savefig(RECURSOS / nombre, dpi=100)
    plt.close(fig)
    print("ok", nombre)


# Escena 1 · mapa de destinos en la UE (café + cacao + madera, último año completo)
ue = (
    mensual[(mensual.anio == ULTIMO) & mensual.ue27]
    .groupby(["iso3", "pais"], as_index=False).fob_usd.sum().sort_values("fob_usd", ascending=False)
)
# (centro del país, punto de la etiqueta, posición del texto): los países claros llevan la etiqueta afuera, unida por una línea
ETIQUETAS = {
    "DEU": ((51.0, 10.4), (52.6, 19.0), "middle right"), "BEL": ((50.6, 4.6), (49.0, -4.5), "middle left"),
    "NLD": ((52.3, 5.6), (55.0, 3.0), "top center"), "ITA": ((42.6, 12.8), (42.6, 12.8), "middle center"),
    "ESP": ((40.0, -3.8), (40.0, -3.8), "middle center"), "FRA": ((46.4, 2.2), (46.4, 2.2), "middle center"),
}
top = ue[ue.iso3.isin(ETIQUETAS)].head(6)
mapa = go.Figure(go.Choropleth(
    locations=ue.iso3, z=ue.fob_usd / 1e6, locationmode="ISO-3",
    colorscale=[[0, "#143f73"], [0.5, "#2a78d6"], [1, "#86b6ef"]], zmin=0, zmax=float(ue.fob_usd.max() / 1e6),
    marker_line_color=FONDO, marker_line_width=1.2, showscale=False,
))
for iso in top.iso3:
    (lat0, lon0), (lat1, lon1), _ = ETIQUETAS[iso]
    if (lat0, lon0) != (lat1, lon1):
        mapa.add_trace(go.Scattergeo(lat=[lat0, lat1], lon=[lon0, lon1], mode="lines", line=dict(color=SUAVE, width=1.5)))
mapa.add_trace(go.Scattergeo(
    lat=[ETIQUETAS[i][1][0] for i in top.iso3], lon=[ETIQUETAS[i][1][1] for i in top.iso3], mode="text",
    text=[f"<b>{p}</b><br>US$ {v / 1e6:,.0f} M" for p, v in zip(top.pais, top.fob_usd)],
    textposition=[ETIQUETAS[i][2] for i in top.iso3],
    textfont=dict(size=18, color=TEXTO, family="Segoe UI"),
))
mapa.update_geos(
    scope="europe", projection_type="mercator", lataxis_range=[36, 61], lonaxis_range=[-15, 34],
    showland=True, landcolor=CAJA, showcountries=True, countrycolor=FONDO, showcoastlines=False,
    showframe=False, showocean=False, bgcolor=FONDO,
)
mapa.update_layout(width=ANCHO, height=ALTO, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor=FONDO, showlegend=False)
mapa.write_image(RECURSOS / "escena_1_mapa_ue.png", width=ANCHO, height=ALTO)
print("ok escena_1_mapa_ue.png")

# Escena 2 · línea de tiempo del EUDR
hitos = [
    ("Jun 2023", "Entra en\nvigor", False),
    ("Dic 2024", "Primer\naplazamiento", False),
    ("Dic 2025", "Segundo\naplazamiento", False),
    ("30 dic\n2026", "Se aplica a\ngrandes y\nmedianas", True),
]
fig, ax = figura()
ax.axis("off")
ax.set_xlim(-0.6, 3.6)
ax.set_ylim(-1.25, 1.3)
ax.plot([-0.3, 3.3], [0, 0], color=RESTO, lw=3, solid_capstyle="round")
for x, (fecha, texto, clave) in enumerate(hitos):
    color = ACENTO if clave else SUAVE
    ax.scatter([x], [0], s=420 if clave else 220, color=color, zorder=3, edgecolors=FONDO, linewidths=3)
    ax.text(x, 0.35, fecha, ha="center", va="bottom", fontsize=21, fontweight="bold", color=ACENTO if clave else TEXTO)
    ax.text(x, -0.35, texto, ha="center", va="top", fontsize=17, color=color, linespacing=1.25)
ax.text(-0.5, 1.25, "Reglamento (UE) 2023/1115 · productos libres de deforestación", fontsize=16, color=SUAVE, va="top")
guardar(fig, "escena_2_linea_tiempo.png")

# Escena 3 · FOB a la UE por producto (barras apiladas)
tabla = ind.pivot(index="anio", columns="producto", values="fob_ue").loc[2015:ULTIMO] / 1e6
fig, ax = figura()
base = pd.Series(0.0, index=tabla.index)
for prod in ["Café", "Cacao", "Madera"]:
    ax.bar(tabla.index, tabla[prod], bottom=base, color=COLOR[prod], width=0.72, label=prod,
           edgecolor=FONDO, linewidth=2)
    base += tabla[prod]
ax.text(ULTIMO, base.iloc[-1] + 25, f"{base.iloc[-1]:,.0f}", ha="center", va="bottom", fontsize=22, fontweight="bold")
ax.set_ylim(0, base.max() * 1.18)
ax.set_xticks(tabla.index[::2])
ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
ax.set_title("Millones de US$ FOB exportados a la UE-27", loc="left", fontsize=18, color=SUAVE, pad=12)
ax.legend(loc="upper left", ncols=3)
fig.tight_layout()
guardar(fig, "escena_3_fob_ue.png")

# Escena 4 · cacao: valor vs volumen (2023 = 1)
c = ind.query("producto == 'Cacao'").set_index("anio").loc[2019:ULTIMO]
valor, volumen = c.fob_ue / c.fob_ue.loc[2023], c.kg_ue / c.kg_ue.loc[2023]
fig, ax = figura()
ax.plot(valor.index, valor, color=COLOR["Cacao"], lw=5, marker="o", ms=10, label="Valor FOB")
ax.plot(volumen.index, volumen, color=SUAVE, lw=5, marker="o", ms=10, label="Volumen (toneladas)")
for serie, color in ((valor, COLOR["Cacao"]), (volumen, SUAVE)):
    ax.annotate(f"x{serie.iloc[-1]:.1f}".replace(".", ","), (serie.index[-1], serie.iloc[-1]), xytext=(12, 0),
                textcoords="offset points", va="center", fontsize=24, fontweight="bold", color=color)
ax.axhline(1, color=RESTO, lw=1.5)
ax.set_xlim(2018.6, ULTIMO + 0.9)
ax.set_ylim(0, valor.max() * 1.15)
ax.set_title("Cacao vendido a la UE-27 (2023 = 1)", loc="left", fontsize=18, color=SUAVE, pad=12)
ax.legend(loc="upper left")
fig.tight_layout()
guardar(fig, "escena_4_cacao.png")

# Escena 5 · café: parte que va a la UE
p = ind.query("producto == 'Café'").set_index("anio").part_ue_fob.loc[2010:ULTIMO]
fig, ax = figura()
ax.plot(p.index, p, color=COLOR["Café"], lw=5)
for anio in (2015, ULTIMO):
    ax.scatter([anio], [p.loc[anio]], s=260, color=ACENTO if anio == ULTIMO else TEXTO, zorder=3, edgecolors=FONDO, linewidths=3)
    ultimo = anio == ULTIMO
    ax.annotate(f"{p.loc[anio]:.0f} %", (anio, p.loc[anio]), xytext=(-14, -44) if ultimo else (0, 18), textcoords="offset points",
                ha="right" if ultimo else "center",
                fontsize=26, fontweight="bold", color=ACENTO if anio == ULTIMO else TEXTO)
ax.set_ylim(0, 75)
ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f} %")
ax.set_title("Parte del café peruano que compra la UE-27 (valor FOB)", loc="left", fontsize=18, color=SUAVE, pad=12)
fig.tight_layout()
guardar(fig, "escena_5_cafe.png")

# Escena 6 · captura del dashboard
captura = Image.open(RAIZ / "figuras" / "dashboard_kpis_mapa.jpg").convert("RGB")
captura.thumbnail((ANCHO - 24, ALTO - 24))
lienzo = Image.new("RGB", (ANCHO, ALTO), FONDO)
x, y = (ANCHO - captura.width) // 2, (ALTO - captura.height) // 2
mascara = Image.new("L", captura.size, 0)
ImageDraw.Draw(mascara).rounded_rectangle((0, 0, *captura.size), radius=18, fill=255)
lienzo.paste(captura, (x, y), mascara)
lienzo.save(RECURSOS / "escena_6_dashboard.png")
print("ok escena_6_dashboard.png")

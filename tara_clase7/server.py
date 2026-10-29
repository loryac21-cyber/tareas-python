"""Servidor MCP del BCRP: herramientas buscar_series, serie, resumen y comparar_paises; recursos bcrp://serie/{codigo}
y bcrp://series-clave; prompt informe.

    uv run pytest                                           # el contrato: las 8 pruebas deben pasar
    uv run server.py                                        # el servidor, por stdio
    claude mcp add --scope project bcrp -- uv run server.py # conectarlo a Claude Code

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""
import calendar
import json
import re
import time
import unicodedata
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
CATALOGO = AQUI / "datos" / "catalogo_bcrp.csv"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
BANCO_MUNDIAL = "https://api.worldbank.org/v2"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, y serie para los datos. No calcules a mano: "
    "cita siempre el código de la serie y el periodo."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 MB. Se baja una vez y queda en datos/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    # primero las series vigentes y, entre ellas, las de nombre más corto (las más generales)
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


# TODO 1 · serie --------------------------------------------------------------------------------------------------

def _fecha_api(fecha, frecuencia, fin):
    """Lleva "2025-01", "2025-01-15", "2025-T1" o "2025" al formato que pide la API según la frecuencia.

    Si falta el mes o el día, `fin` dice si completar con el final del año o del mes (True) o con el inicio (False).
    """
    m = re.fullmatch(r"(\d{4})(?:-([TQ])?(\d{1,2}))?(?:-(\d{1,2}))?", str(fecha).strip().upper())
    if not m:
        raise ToolError(f"Fecha no válida: {fecha!r}. Usen 2025-01 (mensual), 2025-01-15 (diaria), "
                        "2025-T1 (trimestral) o 2025 (anual).")
    anio, trimestre, n, dia = int(m[1]), m[2], m[3], m[4]
    if frecuencia == "Anual":
        return str(anio)
    if frecuencia == "Trimestral":
        if n is None:
            return f"{anio}-{4 if fin else 1}"
        return f"{anio}-{int(n) if trimestre else (int(n) - 1) // 3 + 1}"
    mes = int(n) if n else (12 if fin else 1)
    if not 1 <= mes <= 12:
        raise ToolError(f"Mes no válido en {fecha!r}.")
    if frecuencia == "Diaria":
        dia = int(dia) if dia else (calendar.monthrange(anio, mes)[1] if fin else 1)
        return f"{anio}-{mes:02d}-{dia:02d}"
    return f"{anio}-{mes}"


def _anio(yy):
    return f"{'19' if int(yy) > 50 else '20'}{yy}"


def _periodo(nombre):
    """ "Ene.2025" -> "2025-01", "01.Oct.26" -> "2026-10-01", "T1.25" -> "2025-T1", "2025" -> "2025"."""
    if m := re.fullmatch(r"(\w{3})\.(\d{4})", nombre):
        return f"{m[2]}-{MESES[m[1].lower()]:02d}"
    if m := re.fullmatch(r"(\d{2})\.(\w{3})\.(\d{2})", nombre):
        return f"{_anio(m[3])}-{MESES[m[2].lower()]:02d}-{m[1]}"
    if m := re.fullmatch(r"T(\d)\.(\d{2})", nombre):
        return f"{_anio(m[2])}-T{m[1]}"
    return nombre


def _numero(texto):
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None   # "n.d." y otros vacíos


@cache
def _bajar(url):
    """Pide JSON a la API. Si limita los pedidos responde HTML: se espera y se reintenta. Lo bajado queda en caché."""
    for intento in range(4):
        try:
            return httpx.get(url, timeout=60).json()
        except (httpx.HTTPError, ValueError):
            time.sleep(2 * (intento + 1))
    raise ToolError("El BCRP no respondió con datos. Esperen unos segundos y reintenten.")


def _serie(codigo, desde, hasta):
    ficha = _ficha(codigo)
    frecuencia = ficha["frecuencia"]
    url = f"{API}/{codigo}/json/{_fecha_api(desde, frecuencia, False)}/{_fecha_api(hasta, frecuencia, True)}"
    datos = [{"periodo": _periodo(p["name"]), "valor": v}
             for p in _bajar(url).get("periods", []) if (v := _numero(p["values"][0])) is not None]
    return {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": frecuencia, "datos": datos, "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Datos de una serie del BCRP entre dos fechas, ambas incluidas.

    Fechas según la frecuencia de la serie: "2025-01" (mensual), "2025-01-15" (diaria), "2025-T1" (trimestral)
    o "2025" (anual). Si no saben el código, búsquenlo antes con buscar_series. Para variaciones, promedios o
    extremos usen resumen. Devuelve [{"periodo", "valor"}] y en "fuente" la URL de la API para verificar la cifra.
    """
    return _serie(codigo, desde, hasta)


# TODO 2 · resumen ------------------------------------------------------------------------------------------------

@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Resumen de una serie del BCRP entre dos fechas: primer y último dato, cambio, variación %, promedio,
    máximo y mínimo (con su periodo).

    Úsenla para cualquier valor puntual, variación, promedio o extremo: así las cuentas las hace Python y no el
    modelo. Mismas fechas que serie, por ejemplo desde="2025-12", hasta="2026-09". Para el dato de un solo
    periodo, pongan la misma fecha en desde y hasta.
    """
    s = _serie(codigo, desde, hasta)
    d = pd.DataFrame(s["datos"])
    if d.empty:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}. Revisen las fechas con serie.")

    def punto(i):
        return {"periodo": d.periodo[i], "valor": round(float(d.valor[i]), 4)}

    primero, ultimo = d.valor.iloc[0], d.valor.iloc[-1]
    return {"codigo": codigo, "nombre": s["nombre"], "frecuencia": s["frecuencia"], "n": len(d),
            "primero": punto(d.index[0]), "ultimo": punto(d.index[-1]),
            "cambio": round(float(ultimo - primero), 4),
            "variacion_pct": round(float((ultimo / primero - 1) * 100), 4) if primero else None,
            "promedio": round(float(d.valor.mean()), 4),
            "maximo": punto(d.valor.idxmax()), "minimo": punto(d.valor.idxmin()), "fuente": s["fuente"]}


# TODO 3 · comparar_paises: el contexto internacional que el BCRP no publica --------------------------------------

@mcp.tool(annotations=SOLO_LECTURA)
def comparar_paises(indicador: str = "NY.GDP.MKTP.KD.ZG", paises: str = "PER;CHL;COL;MEX;BRA",
                    desde: int = 2015, hasta: int = 2025) -> dict:
    """Compara al Perú con otros países con un indicador anual del Banco Mundial.

    Úsenla cuando la pregunta compare países o pida contexto internacional («¿creció el Perú más que Chile?»);
    para cifras del Perú usen las series del BCRP. Indicadores útiles: "NY.GDP.MKTP.KD.ZG" (crecimiento del PBI
    real, %), "FP.CPI.TOTL.ZG" (inflación, %), "NY.GDP.PCAP.CD" (PBI per cápita, US$), "SL.UEM.TOTL.ZS"
    (desempleo, %), "NE.EXP.GNFS.ZS" (exportaciones, % del PBI). paises: códigos ISO3 separados por ";".
    Devuelve por país los datos, el promedio y el último dato; el ranking por promedio; y la URL de la fuente.
    """
    if not re.fullmatch(r"[A-Za-z0-9.]+", indicador) or not re.fullmatch(r"[A-Za-z]{2,3}(;[A-Za-z]{2,3})*", paises):
        raise ToolError(f"Revisen el indicador {indicador!r} y los países {paises!r} (por ejemplo PER;CHL;COL).")
    url = f"{BANCO_MUNDIAL}/country/{paises.upper()}/indicator/{indicador}?format=json&date={desde}:{hasta}&per_page=2000"
    try:
        r = httpx.get(url, timeout=60).json()
    except (httpx.HTTPError, ValueError):
        raise ToolError("El Banco Mundial no respondió. Reintenten en unos segundos.")
    filas = r[1] if len(r) > 1 and r[1] else []
    filas = [f for f in filas if f["value"] is not None]
    if not filas:
        raise ToolError(f"El Banco Mundial no tiene datos de {indicador!r} para {paises!r} entre {desde} y {hasta}.")

    por_pais = {}
    for f in sorted(filas, key=lambda f: f["date"]):
        p = por_pais.setdefault(f["countryiso3code"], {"pais": f["country"]["value"], "codigo": f["countryiso3code"],
                                                       "datos": []})
        p["datos"].append({"periodo": f["date"], "valor": round(f["value"], 4)})
    for p in por_pais.values():
        p["promedio"] = round(sum(x["valor"] for x in p["datos"]) / len(p["datos"]), 4)
        p["ultimo"] = p["datos"][-1]
    ranking = sorted(por_pais.values(), key=lambda p: p["promedio"], reverse=True)
    return {"indicador": indicador, "nombre": filas[0]["indicator"]["value"], "paises": list(por_pais.values()),
            "ranking_promedio": [p["codigo"] for p in ranking], "fuente": url}


# TODO 4 · recursos -----------------------------------------------------------------------------------------------

@mcp.resource("bcrp://serie/{codigo}", mime_type="application/json")
def ficha(codigo: str) -> str:
    """Ficha de una serie del BCRP: nombre, categoría, frecuencia, desde cuándo hay datos y última actualización."""
    return json.dumps(_ficha(codigo), ensure_ascii=False)


@mcp.resource("bcrp://series-clave", mime_type="application/json")
def series_clave() -> str:
    """Los códigos de las series que más se consultan, para no tener que buscarlos."""
    return json.dumps({
        "PN01273PM": "Inflación de Lima Metropolitana, var. % 12 meses (mensual)",
        "PN01271PM": "IPC de Lima Metropolitana, var. % mensual (mensual)",
        "PD04722MM": "Tasa de referencia de la política monetaria, % (mensual)",
        "PD04638PD": "Tipo de cambio interbancario venta, S/ por US$ (diaria)",
        "PN00027MM": "Reservas internacionales netas, millones US$ (mensual)",
        "PN38784BM": "Precio del cobre, ¢US$ por libra (mensual)",
        "PN38714BM": "Exportaciones FOB, millones US$ (mensual)",
        "PN38063GM": "Tasa de desempleo de Lima Metropolitana, % (mensual)",
        "PM04923AA": "PBI real, var. % (anual)",
    }, ensure_ascii=False, indent=1)


# TODO 5 · prompt -------------------------------------------------------------------------------------------------

@mcp.prompt
def informe(tema: str) -> str:
    """Informe de 5 viñetas sobre un tema económico del Perú, con cada cifra verificable."""
    return (f"Escribe un informe de 5 viñetas sobre «{tema}» con datos oficiales del BCRP. "
            "Primero busca los códigos con buscar_series; para cada cifra usa resumen o serie, nunca calcules a mano. "
            "En cada viñeta cita el código de la serie, el periodo y la URL de la fuente. Si hace falta contexto "
            "internacional, usa comparar_paises. Si una cifra no está disponible, dilo en vez de estimarla.")


if __name__ == "__main__":
    mcp.run()

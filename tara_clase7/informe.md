# Informe · ¿Le sirve a Claude un MCP con las series del BCRP?

> **Borrador.** Las secciones marcadas con ⏳ se completan con lo que salga de `uv run evaluar.py`
> (escribe `resultados.csv`) y `uv run graficar.py` (escribe `grafico.png`).

## 1. Qué construí

Un servidor MCP en Python con FastMCP 4 ([server.py](server.py)) sobre la API pública del BCRP:

| Primitiva | Nombre | Qué hace |
|---|---|---|
| Herramienta | `buscar_series` | Busca el código entre las 17,167 series del catálogo |
| Herramienta | `serie` | Baja los datos entre dos fechas y devuelve la URL de la fuente |
| Herramienta | `resumen` | Primero, último, cambio, variación %, promedio, máximo y mínimo, calculados en Python |
| Herramienta (propia) | `comparar_paises` | Compara al Perú con otros países con un indicador anual del Banco Mundial; devuelve datos, promedio, ranking y la URL |
| Recurso (plantilla) | `bcrp://serie/{codigo}` | Ficha de una serie: nombre, frecuencia, inicio, actualización |
| Recurso | `bcrp://series-clave` | Los códigos más consultados |
| Prompt | `informe(tema)` | Cinco viñetas, cada una con código de serie, periodo y fuente |

**Por qué `comparar_paises`:** el BCRP publica solo cifras del Perú, así que preguntas como «¿creció el Perú más que
Chile en 2025?» quedaban fuera. La herramienta usa la API del Banco Mundial (sin clave), valida los códigos antes de
llamar y devuelve la URL consultada, igual que `serie`.

Pruebas: `uv run pytest -q` → **8 passed** (32 s, con datos reales del BCRP).

Ejemplo de `comparar_paises` (crecimiento del PBI real, 2023–2025): Perú −0.35 %, 3.52 % y 3.43 % (promedio 2.20 %),
Chile 1.98 % y Colombia 1.66 % de promedio; el Perú encabeza el ranking del periodo.

## 2. Evaluación

10 preguntas en [preguntas.csv](preguntas.csv): las 8 del curso y 2 mías, con la verdad sacada de la web del BCRP:

| id | Pregunta | Verdad | Serie |
|---|---|---|---|
| `export_ago26` | Exportaciones FOB de agosto de 2026, millones de US$ | 10,815.4 | PN38714BM |
| `desempleo_set26` | Tasa de desempleo de Lima Metropolitana (promedio móvil 3 meses), setiembre de 2026, % | 4.37 | PN38063GM |

### Resultados por modo (Haiku) ⏳

| Modo | Acierta | Se equivoca | No sabe | Segundos promedio |
|---|---|---|---|---|
| memoria | | | | |
| mcp | | | | |

![Aciertos por modo](grafico.png)

### Qué falló y por qué ⏳

- **memoria:** …
- **mcp:** …

### Experimento extra ⏳

Corrida base guardada en `resultados_base.csv`. Luego: *(elegir uno)* quitar de `INSTRUCCION` la frase «Si no puedes
saberlo con certeza, pon valor null: no estimes.», o `uv run evaluar.py --modos memoria web mcp`.

## 3. Dos cifras comprobadas a mano en la web del BCRP

| Cifra | Lo que devolvió el MCP | Lo que muestra la web del BCRP | Tabla |
|---|---|---|---|
| Inflación Lima 12 meses, set-2026 (PN01273PM) | 4.5487 % (`resumen`) | 4.55 % | [ver tabla](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html/2026-1/2026-9/) |
| Exportaciones FOB, ago-2026 (PN38714BM) | 10,815.40 millones de US$ (`resumen`) | 10,815 millones de US$ | [ver tabla](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN38714BM/html/2026-1/2026-9/) |

La tasa de desempleo de setiembre se puede ver en
[esta tabla](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN38063GM/html/2026-1/2026-9/)
(4.4 % redondeado a un decimal).

## 4. Conclusión ⏳

…

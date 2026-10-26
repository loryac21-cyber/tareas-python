# Monitor de Incendios Perú · Retos A y C — informe (texto fuente del reel)

Autora: Lory Acosta · Tarea Clase 5 · Data Science con Python

Texto armado a partir del notebook `monitor_incendios_final (1).ipynb` y de los datos del dashboard `monitor_incendios_retos.html`. Todas las cifras salen de los datos del tablero.

## Corte y periodo
Corte de datos: 21 Oct 2026, 14:19 h (Lima). Periodo analizado: 15/10 – 21/10/2026 (últimos 7 días de NASA FIRMS).

## Focos de calor
Los satélites VIIRS S-NPP, NOAA-20 y NOAA-21 (NASA FIRMS) detectaron 7,145 focos de calor de vegetación en el Perú entre el 15 y el 21 de octubre de 2026, sin contar los de confianza baja. Cada foco es un píxel de 375 m.

Departamentos con más focos: Ucayali (1,965), Junin (942), Huanuco (796), Loreto (521), Cusco (400).

## De focos a incendios
Dos focos son vecinos si están a ≤ 1 km y ≤ 48 h. Un incendio es un grupo conexo de focos vecinos; es activo si tiene ≥ 3 focos y al menos uno en las últimas 24 h. Resultado: 47 incendios activos; 10 de ellos superan las 100 ha de huella VIIRS. El más grande está en Moquegua (Moquegua), con 217 ha de huella.

## Prioridad
Índice 0–100: 0.65 · base + 15 · P(construcciones) + 20 · P(población); base = 100 · [0.4 · P(huella) + 0.3 · P(focos 24 h) + 0.3 · P(FRP)].

Incendios con mayor prioridad:

| Distrito | Región | Huella (ha) | Prioridad | Personas ≤ 1 km | Personas ≤ 5 km | Construcciones ≤ 500 m | Construcciones ≤ 1 km | Acción sugerida |
|---|---|---|---|---|---|---|---|---|
| Paracas | Ica | 107 | 89 | 2,278 | 5,668 | 441 | 543 | Alerta a la población · Proteger cultivos |
| Moquegua | Moquegua | 217 | 88 | 32 | 210 | 156 | 272 | Alerta a la población |
| Moquegua | Moquegua | 214 | 88 | 131 | 2,048 | 48 | 108 | Monitorear |
| Las Piedras | Madre De Dios | 108 | 76 | 15 | 170 | 6 | 11 | Riesgo ganadero |
| Laberinto | Madre De Dios | 108 | 73 | 23 | 291 | 0 | 0 | Monitorear |
| La Joya | Arequipa | 132 | 72 | 35 | 1,222 | 0 | 0 | Monitorear |
| Puerto Bermudez | Pasco | 56 | 72 | 66 | 1,490 | 21 | 28 | Monitorear |
| Mollendo | Arequipa | 85 | 69 | 55 | 1,181 | 69 | 103 | Alerta a la población |
| Pacocha | Moquegua | 66 | 67 | 940 | 1,624 | 111 | 211 | Alerta a la población |
| Tahuamanu | Madre De Dios | 113 | 65 | 4 | 39 | 1 | 2 | Monitorear |

El incendio de Paracas (Pisco, Ica) es el de mayor prioridad (89): tiene 2,278 personas a ≤ 1 km, 441 construcciones a ≤ 500 m y 33 ha de cultivos a ≤ 1 km. Acción sugerida: alerta a la población y proteger cultivos.

En total, alrededor de los incendios prioritarios hay 2,440 construcciones a ≤ 1 km (1,506 a ≤ 500 m), 4,672 personas a ≤ 1 km y 26,024 a ≤ 5 km (WorldPop ajustado al Censo 2025, 34 157 732 habitantes).

## ¿Dónde cae el fuego? (Hansen Global Forest Change)
De los focos de calor: 74.1 % cayó en zonas sin bosque (puna, pastos, costa, cultivos), 14.0 % en deforestación antigua y 11.9 % en deforestación reciente (bosque perdido en los últimos 5 años). La lectura «quema para deforestar» es una hipótesis razonable, no una prueba.

## Reto A · Área quemada con dNBR (Sentinel-2)
NBR = (B8 − B12)/(B8 + B12); dNBR = NBR antes − NBR después. Se pudo calcular en 6 incendios (Río Tambo, Tiquillaca, Juli, Las Piedras y Laberinto fallaron por falta de imágenes limpias).

| Incendio | Huella VIIRS (ha) | Área quemada dNBR (ha) | Focos dentro del área dNBR | Cobertura principal |
|---|---|---|---|---|
| Paracas (Ica) | 107 | 1.9 | 0 % | Suelo desnudo |
| Moquegua (Moquegua) | 217 | 39.0 | 0 % | Suelo desnudo |
| Moquegua (Moquegua) | 214 | 28.9 | 6 % | Suelo desnudo |
| Puerto Bermudez (Pasco) | 56 | 0.0 | 0 % | — |
| La Joya (Arequipa) | 132 | 26.7 | 0 % | Suelo desnudo |
| Mollendo (Arequipa) | 85 | 118.0 | 0 % | Suelo desnudo |

Mollendo (Arequipa) tiene la mayor área quemada dNBR: 118 ha (89.2 ha de severidad baja, 12.7 moderada baja, 11.6 moderada alta y 4.5 alta), frente a 85 ha de huella VIIRS. Pero 0 % de sus focos cae dentro del área dNBR y 102.8 ha son suelo desnudo y 14.5 ha agua según WorldCover: el resultado no está validado (el tablero de clase obtuvo 89 % en Curahuasi).

## Reto C · ¿Qué se quemó?
En los incendios medidos, casi toda el área dNBR cae en suelo desnudo según ESA WorldCover 2021; no aparecen hectáreas importantes de bosque, pastizal ni cultivo.

## Lluvias sobre suelo quemado (CENEPRED)
CENEPRED (21/10/2026, aviso SENAMHI N.° 429) anunció lluvias de moderada a extrema intensidad del 22 al 24 de octubre en la costa de Arequipa, Callao, Ica, Lima, Moquegua y Tacna. Hay 8 incendios activos en regiones con aviso de lluvia. En los medidos, la pendiente mediana del área quemada es de 2 a 6 grados, así que el riesgo de huayco calculado es bajo.

## Limitaciones
Nubes y humo, imágenes posteriores muy recientes en incendios aún activos, WorldCover de 2021, población WorldPop 2020 escalada al Censo 2025. La API de Geobosques no respondió en este corte.

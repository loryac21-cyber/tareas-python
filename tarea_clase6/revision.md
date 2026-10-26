# Revisión del guion contra la fuente

Las filas 1, 2 y 4 son cambios hechos sobre el borrador del guion. Las demás son frases tentadoras que se evitaron desde el borrador porque la fuente no las respalda.

Fuente: `fuente_incendios.md`. Ese texto se armó con los datos del dashboard `monitor_incendios_retos.html` y el notebook de la Tarea 5. `verificar_guion.py` comprueba que cada cifra en pantalla aparezca tal cual en la fuente (resultado: OK). Las afirmaciones se revisaron a mano, frase por frase.

| # | Frase riesgosa (lo que un modelo escribiría fácilmente) | Qué dice la fuente | Cómo quedó en el guion |
|---|---|---|---|
| 1 | «los satélites de la NASA detectaron…» | Los satélites son S-NPP, NOAA-20 y NOAA-21. Dos son de la NOAA; la NASA solo publica los datos en FIRMS. | «tres satélites con datos de la NASA» |
| 2 | «Sentinel-2 marca…» (en la frase hablada) | El verificador marcó el «2»: la voz lee mal los dígitos. | «Sentinel dos» |
| 3 | «en Mollendo se quemaron 118 hectáreas» | Es el dato más llamativo, pero 0 % de los focos VIIRS cae dentro del área dNBR, y 102.8 de las 118 ha son suelo desnudo y 14.5 ha agua según WorldCover. No está validado (el tablero de clase logró 89 % en Curahuasi). | «…marca ciento dieciocho hectáreas…, pero ningún foco cae dentro y casi todo es suelo desnudo. Aún no está validado.» La etiqueta dice «sin validar». |
| 4 | «en Paracas hay 2,278 personas…» | Es una estimación de WorldPop ajustada al Censo 2025, no un conteo censal. | «se estiman dos mil doscientas setenta y ocho personas» |
| 5 | «el incendio más grande es el de Paracas» | Falso: el más grande es Moquegua (217 ha). Paracas (107 ha) es el de mayor prioridad (89) por la gente y las construcciones cercanas. | «El más urgente no es el más grande» |
| 6 | «tres de cada cuatro focos cayeron en chacras y pastos» | La clase «sin bosque» del notebook es puna, pastos, costa y cultivos, no solo chacras. 74.1 % es un poco menos de 3/4. | «casi tres de cada cuatro… en puna, pastos, costa y cultivos» |
| 7 | «las lluvias amenazan con huaycos sobre ocho incendios» | Los 8 incendios están en regiones con aviso, pero el riesgo de huayco calculado es **bajo** (pendiente mediana de 2 a 6°). | Solo se dice que están en regiones con aviso de lluvia; no se afirma riesgo alto. |
| 8 | «343 focos en las últimas 24 h» (cifra descartada) | El notebook imprime 343, pero los datos del tablero dan 413 con el filtro ≤ 24 h. Dos valores para lo mismo. | No se usa en el reel. |

Lección (la misma de la diapositiva): **las cifras estaban bien; las frases podían ser falsas.** Los números se verifican con código. Las afirmaciones las verifica una persona.

# Posts para el reel · Monitor de Incendios Perú 2026

Revisados contra `fuente_incendios.md`. Reemplaza [enlace al tablero] antes de publicar.

## Instagram / TikTok (descripción del reel)

¿Qué está ardiendo en el Perú? 🔥
Del 15 al 21 de octubre de 2026, los satélites VIIRS (NASA FIRMS) detectaron 7,145 focos de calor. Los agrupé en 47 incendios activos y crucé cada uno con población, construcciones, bosques y el aviso de lluvias de CENEPRED.

📍 El de mayor prioridad: Paracas (Ica), con unas 2,278 personas estimadas a menos de 1 km.
🌾 74.1 % de los focos cayó fuera del bosque.
⚠️ En Mollendo, Sentinel-2 marca 118 ha quemadas, pero el dato aún no está validado.

Tablero completo: [enlace al tablero]
Hecho con Python: geopandas, Earth Engine y Sentinel-2.

#IncendiosForestales #Perú #DataScience #Python #Teledetección #IngenieríaQuímica

Voz generada con IA.

## X (Twitter)

Del 15 al 21 de octubre, 7,145 focos de calor en el Perú → 47 incendios activos.
El más urgente no es el más grande: en Paracas hay ~2,278 personas estimadas a ≤ 1 km del fuego.
Hice un tablero con Python y datos satelitales: [enlace al tablero]

Voz generada con IA.

## LinkedIn

Esta semana convertí datos satelitales en un tablero para decidir dónde actuar ante los incendios forestales en el Perú.

Qué hice (Python · geopandas · Earth Engine):
• 7,145 focos de calor VIIRS (NASA FIRMS, 15–21 oct 2026) agrupados en 47 incendios activos (focos a ≤ 1 km y ≤ 48 h).
• Un índice de prioridad 0–100 que combina tamaño, actividad, intensidad, población (WorldPop ajustado al Censo 2025) y construcciones (Google Open Buildings).
• Resultado: el de mayor prioridad no es el más grande. Paracas (Ica) tiene unas 2,278 personas estimadas a ≤ 1 km, frente a los 217 ha de huella del incendio de Moquegua.
• 74.1 % de los focos cayó en zonas sin bosque (Hansen GFC).

Lo que aprendí: un número de satélite no es un hecho hasta validarlo. En Mollendo, Sentinel-2 (dNBR) marca 118 ha quemadas, pero ninguno de los focos cae dentro y casi todo es suelo desnudo. Lo reporto como «sin validar».

Tablero: [enlace al tablero]

#DataScience #Python #SIG #Teledetección #GestiónDeRiesgos #IngenieríaQuímica

Voz generada con IA.

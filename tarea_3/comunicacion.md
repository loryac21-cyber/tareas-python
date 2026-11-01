# Guía de comunicación: cómo publicar estos resultados en LinkedIn

El tema toca ingresos de miles de familias productoras, a empresas exportadoras y a instituciones públicas. Los datos pueden leerse como
"buenas noticias" (récords de valor) o como "malas noticias" (caída en 2026). Esta guía busca que la publicación sea **precisa, útil y
propositiva**, sin alarmar ni sobrevender.

## 1. Mensaje central

> El valor de nuestras exportaciones de café y cacao creció sobre todo por los precios internacionales. Los precios no los decidimos;
> la productividad, la calidad y la diversificación de mercados sí podemos trabajarlas.

Tres apoyos, uno por hallazgo:

1. **Café:** el 74 % del aumento del valor entre 2015 y 2025 vino del precio; el volumen creció 31 %.
2. **Cacao:** creció en precio y en volumen, pero en enero–agosto de 2026 su valor bajó 48 %, con un precio promedio que fue la mitad
   del de un año antes.
3. **Mercados:** el cacao se diversificó (10,4 mercados equivalentes); el café se concentra en Estados Unidos (33 %).

## 2. Qué decir y qué evitar

| En lugar de… | Mejor decir… | Por qué |
|---|---|---|
| "Récord histórico de exportaciones de café" | "Récord de valor exportado, con un volumen similar al de años anteriores" | El récord es de precio, no de producción |
| "Los productores ganaron el triple" | "El valor FOB exportado casi se triplicó" | El valor FOB no es el precio en chacra; no medimos ingresos de productores |
| "El cacao colapsa" / "crisis del cacao" | "El valor del cacao exportado bajó 48 % en enero–agosto de 2026, en línea con la caída del precio internacional" | Dato preciso, sin adjetivos alarmistas; el volumen bajó solo 11 % |
| "El precio seguirá cayendo" | "Los precios ya corrigieron desde sus máximos de 2025" | No hacemos pronósticos de precios |
| "Hay que dejar Europa" | "Diversificar es depender menos de un solo comprador" | La UE, como bloque, sigue siendo el principal destino del café y del cacao (40 % de cada uno en 2025) |
| "El Estado debe…" / "las empresas no…" | "Propuestas para conversar: productividad, calidad, gestión de riesgo y seguimiento de mercados" | Tono propositivo, sin culpar a actores |
| "Coberturas: compren futuros" | "Instrumentos de gestión de riesgo a través de cooperativas y exportadores" | Es análisis económico general, no una recomendación de inversión |

## 3. Cuidados con las cifras

- **Siempre con fuente y periodo:** "SUNAT y Banco Mundial, 2015–2025". Si se cita 2026, decir "enero–agosto".
- **Valor y volumen juntos:** cada cifra de valor va con su volumen o su valor unitario.
- **Redondeo honesto:** "casi se triplicó" (x2,9), "tres de cada cuatro dólares" (74 %), "a la mitad" (−49 %).
- **No mezclar productos:** el café y el cacao tuvieron historias distintas; no generalizar "el agro creció por precio".
- **Asociación, no causa:** la descomposición es contable. El clima, la demanda y los costos también influyen.
- **Sin nombres de empresas ni de personas:** los datos son agregados por país de destino.
- **Temas regulatorios:** este trabajo no evalúa normas comerciales ni ambientales; no se mencionan para no desviar la conversación.

## 4. Antes de publicar (lista de revisión)

- [ ] Las cifras del post coinciden con el dashboard y con `web/data/hallazgos.json`.
- [ ] El post enlaza al dashboard y al repositorio.
- [ ] Aparece la nota "el valor FOB no es el precio en chacra".
- [ ] 2026 está marcado como parcial (enero–agosto).
- [ ] El reel lleva el aviso "Voz generada con IA" y la música tiene licencia de uso.
- [ ] El tono reconoce el trabajo de productores y exportadores, sin culpar a nadie.
- [ ] Hay al menos dos capturas del dashboard y dos hallazgos en el post.

## 5. Texto para LinkedIn

El texto completo (y versiones para X y Facebook) está en [`reel/posts.md`](reel/posts.md), generado desde
[`reel/guion.json`](reel/guion.json). Adjunta el reel (`reel/reel.mp4`) y dos capturas: `figuras/dashboard_kpis.jpg` y
`figuras/dashboard_graficos.jpg`.

**Comentario fijado sugerido** (para responder dudas frecuentes):

> ¿Por qué el valor unitario no es el precio al productor? Porque se mide en el puerto peruano (FOB) e incluye acopio, procesamiento,
> transporte interno y márgenes. La metodología y el código están en el repositorio.

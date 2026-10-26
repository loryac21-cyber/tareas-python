# Tarea 2 — Voces y documentos peruanos: del archivo escaneado al texto buscable

**Pregunta:** ¿Pueden convertirse documentos escaneados y entrevistas en audio en un archivo de texto estructurado y buscable?

**Dashboard público:** https://PEGAR-ENLACE.streamlit.app

## Corpus, fuentes y licencias (fecha de extracción: 2026-10-25)

| Corpus | Cantidad | Fuente | Licencia |
|---|---|---|---|
| Impresos | 35 | BCRP — *Reporte de Inflación* trimestral (marzo/junio/setiembre/diciembre, 2018‑2026); 1 página de prosa por reporte | Publicación institucional de acceso público; se cita al BCRP. No se redistribuyen imágenes: el dashboard enlaza el PDF oficial |
| Fotos | 8 | Fotos propias con celular (sombra e inclinación) de páginas del Reporte de Inflación | Propias, CC BY 4.0, sin datos personales |
| Manuscritos | 9 | Hojas escritas a mano por la autora: estrofas de Vallejo (1918), Valdelomar (1916), Eguren (1911), Chocano (1906) — dominio público — y 5 declaraciones ambientales originales | Propias, CC BY 4.0, sin datos personales |
| Audio | 24 clips, ≥30 min | OpenSLR 73 — *Crowdsourced high‑quality Peruvian Spanish speech data set* (Google). Clips de ~80 s uniendo frases de un mismo hablante; 2 clips alternan dos voces (multihablante) | CC BY‑SA 4.0 — Guevara‑Rukoz et al. (2020), LREC |

El detalle por archivo (URL, licencia y cómo recuperarlo) está en `datos/fuentes.csv`. Los PDF, audios originales y salidas pesadas están en `datos/raw/` (excluido de Git).

## Pipeline

1. `01_extraccion.ipynb` — descarga, PaddleOCR (`lang=es`), faster‑whisper `small` con VAD, diarización (MFCC + F0 + clustering aglomerativo), seudonimización (DNI, teléfonos, correos, nombres con tratamiento), limpieza por hash, EDA con Plotly y exportación a CSV.
2. `02_evaluacion.ipynb` — muestra fija de 10 documentos y 10 clips con referencias manuales, CER/WER de la línea base, modelos alternativos (EasyOCR; wav2vec2 XLS‑R español), extracción JSON con LLM, auditoría humana de 20 casos y tabla comparativa.
3. `app.py` — dashboard Streamlit que solo lee los CSV de `datos/`.

**Referencias manuales:** se partió de un borrador (capa de texto del PDF, guion de lectura de OpenSLR o el texto copiado a mano) y se revisó leyendo la imagen / escuchando el audio. Los borradores sin revisar no se usan en las métricas.

## Resultados (muestra de 10 documentos y 10 clips)

Ver la tabla completa en `datos/metricas.csv` y en la pestaña *Evaluación* del dashboard.

- Resultados Test: COPIAR de `datos/resumen_test.txt`

## Hallazgos

1. COMPLETAR (p. ej., diferencia de CER entre impresos y manuscritos y su causa).
2. COMPLETAR (p. ej., WER en clips multihablante vs. un hablante; si la diarización acertó el número de hablantes).

## Limitaciones

1. La diarización es ligera (MFCC + F0); distingue bien voces de distinto tono pero puede confundir dos voces parecidas. Una alternativa más precisa es pyannote (requiere token de Hugging Face).
2. Los audios de OpenSLR son frases leídas en estudio, más limpias que una entrevista real; el WER obtenido es optimista frente a audio espontáneo con ruido.

## Cómo ejecutar en local (Windows)

```bat
cd tarea_2
uv venv --python 3.11
.venv\Scripts\activate
uv pip install -r requirements-pipeline.txt
set GEMINI_API_KEY=tu_clave
jupyter nbconvert --to notebook --execute --inplace 01_extraccion.ipynb --ExecutePreprocessor.timeout=-1
jupyter nbconvert --to notebook --execute --inplace 02_evaluacion.ipynb --ExecutePreprocessor.timeout=-1
streamlit run app.py
```

Solo el dashboard: `pip install -r requirements.txt` y `streamlit run app.py`.

## Uso de IA

Se usó Claude como asistente de programación; las capturas de la conversación están en `evidencias_ia/`. Los resultados se ejecutaron y verificaron localmente.

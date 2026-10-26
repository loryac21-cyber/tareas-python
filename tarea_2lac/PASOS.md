# Pasos para completar la Tarea 2 (Windows) — borrar este archivo antes de entregar

## 0. Antes de empezar
- Python vía `uv` (ya lo usaste en el curso). Si no: `pip install uv`.
- Una API key gratuita de Gemini (aistudio.google.com → Get API key) **o** Ollama con `ollama pull qwen2.5:3b`.
- ~6 GB libres (PDF del BCRP ~0,5 GB, OpenSLR ~1 GB, modelos ~3 GB).

## 1. Repo y Issues (GitHub Desktop + VS Code)
1. Copia esta carpeta `tarea_2/` dentro de tu repo del curso (o crea uno público nuevo).
2. GitHub Desktop → commit `inicio: estructura tarea_2` → Push.
3. En github.com → Issues → crea:
   - `T2 – Parte 1: Corpus y extracción (OCR + ASR)`
   - `T2 – Parte 2: Evaluación y extracción estructurada`
   - `T2 – Parte 3: Dashboard y despliegue`

## 2. Tus capturas (lo único que no se puede descargar)
- **9 manuscritos:** copia a mano cada texto de `datos/referencias/manuscritos_textos.md` (sin nombre ni firma), foto de frente →
  `datos/raw/documentos/manuscritos/manuscrito_01.jpg … manuscrito_09.jpg`.
- **8 fotos:** después de correr la sección 1 del notebook 01, abre en pantalla
  `datos/referencias/para_fotografiar/foto_01.png … foto_08.png` y tómales foto con el celular
  **inclinado y con sombra** → `datos/raw/documentos/fotos/foto_01.jpg … foto_08.jpg` (mismo número).

## 3. Entorno y ejecución
```bat
cd tarea_2
uv venv --python 3.11
.venv\Scripts\activate
uv pip install -r requirements-pipeline.txt
set GEMINI_API_KEY=tu_clave
jupyter nbconvert --to notebook --execute --inplace 01_extraccion.ipynb --ExecutePreprocessor.timeout=-1
```
(O abre el notebook en VS Code, elige el kernel `.venv` y "Run All".)
Commit: `ocr+asr: 52 documentos y 24 clips (#1)`.

## 4. Referencias manuales y auditoría
1. Corre las 3 primeras celdas de código de `02_evaluacion.ipynb`: crea `datos/referencias/doc_XXX.txt` y `clip_XXX.txt` (20 archivos) con un borrador.
2. Abre cada uno, compáralo con la imagen / escucha el audio, corrige y **borra la primera línea `# BORRADOR`**.
3. Ejecuta todo el notebook 02. Se crea `datos/auditoria_llm.csv`: llena `correcto` (1/0) y `error` en las 20 filas, y vuelve a ejecutar.
4. Completa la celda "Decisión" y "Hallazgos/Limitaciones" del README con tus números.
Commit: `eval: CER/WER, LLM y auditoría 20 casos (#2)`.

## 5. Dashboard
1. `streamlit run app.py` para probar.
2. Push. share.streamlit.io → Create app → tu repo, rama `main`, archivo `tarea_2/app.py`.
3. Pega el enlace en el README. Commit: `app: dashboard desplegado (#3)`.
4. Capturas de esta conversación → `evidencias_ia/01.png, 02.png…` (oculta claves).
5. Cierra los 3 Issues con un comentario de bitácora.

## 6. Comentario en el Issue #190
```
Tarea 2 – Individual
Fuentes: BCRP (Reporte de Inflación) / OpenSLR 73 / capturas propias sin datos personales
Estudiante: Lita Leydi Acosta Carbajal (@loryac21-cyber)
Dashboard público (obligatorio): https://...streamlit.app
Carpeta del trabajo: https://github.com/loryac21-cyber/REPO/tree/main/tarea_2
Resultados Test: (copiar datos/resumen_test.txt)
```

# 🗞️ Tarea 1 – Noticias peruanas: del titular al clasificador

**Estudiante:** Lita Leydi Acosta Carbajal · **Opción:** C – Comparada (La República + El Comercio)

## 1. Pregunta del proyecto
**¿Pueden convertir titulares peruanos en un clasificador de noticias?**
Se recolectan noticias reales, se etiquetan de forma semi-supervisada con un LLM, se entrena un Transformer ligero (DistilBERT multilingüe) y se despliega un dashboard en Streamlit que clasifica titulares nuevos en vivo en 4 categorías: `politica`, `economia`, `deportes`, `ciencia_tecnologia`.

## 2. Medios y fechas de extracción
| Medio | Fuente usada | Fecha de descarga |
|---|---|---|
| La República (`larepublica.pe`) | Feeds RSS oficiales `/rss/*.xml` y sitemaps listados en `robots.txt` | `AAAA-MM-DD` *(copiar de la 1.ª celda de `01_recoleccion.ipynb`)* |
| El Comercio (`elcomercio.pe`) | Feeds RSS Arc `/arc/outboundfeeds/...` y sitemaps listados en `robots.txt` | `AAAA-MM-DD` |

Rango de fechas de publicación: `AAAA-MM-DD → AAAA-MM-DD` · Noticias válidas: `N` (ver `datos/noticias.csv`).
Buenas prácticas: se respeta `robots.txt` (`urllib.robotparser`), User-Agent descriptivo, pausa aleatoria de 1–2 s y máximo 1 reintento. No se hace scraping de portadas HTML: solo canales oficiales RSS/sitemap.

## 3. Resultados
| Modelo (mismo test reservado) | Accuracy | F1 macro |
|---|---|---|
| Zero-shot `Recognai/bert-base-spanish-wwm-cased-xnli` (40 titulares) | 0.xx | 0.xx |
| LLM débil `Qwen2.5-Instruct` | 0.xx | 0.xx |
| **DistilBERT multilingüe fine-tuned** | **0.xx** | **0.xx** |

Acuerdo LLM–Humano (auditoría de 20 casos): `xx/20`. Matriz de confusión: `modelo/matriz_confusion_test.png`.

## 4. Hallazgos analíticos
1. *(Completar con la salida del notebook 1)* — p. ej. «`<categoría>` concentra el XX % del corpus y `<categoría>` solo el XX %: el dataset está desbalanceado, por eso se usa F1 macro y split estratificado».
2. *(Completar con la salida del notebook 2)* — p. ej. «`deportes` obtiene el mejor F1 (léxico exclusivo: clubes, Liga 1, selección), mientras que la confusión más frecuente es `politica ↔ economia`, por titulares sobre el MEF, presupuesto o leyes con impacto económico».

## 5. Limitaciones técnicas
1. **Ventana temporal corta:** los RSS/sitemaps solo exponen las notas más recientes, así que el corpus refleja la agenda de pocos días (temas coyunturales sobrerrepresentados) y puede no generalizar a otras épocas.
2. **Etiquetas ruidosas y modelo pesado:** el Transformer se entrena con etiquetas débiles del LLM (los errores del LLM se heredan) y la verdad de referencia es la sección editorial, que no siempre coincide con el tema del titular. Además, los pesos (~540 MB) superan el límite de GitHub: en Streamlit Cloud la app usa el respaldo ligero TF-IDF + LogReg (`modelo/tfidf_logreg.joblib`).

## 6. Cómo ejecutar en local
```bash
git clone https://github.com/<usuario>/<repo>.git
cd <repo>/tarea_1
python -m venv .venv
# Windows: .venv\Scripts\activate    |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# 1) Recolección (genera datos/noticias.csv)
jupyter nbconvert --to notebook --execute --inplace 01_recoleccion.ipynb
# 2) Clasificación (genera datos/etiquetas_llm.csv y modelo/) — recomendado en Google Colab con GPU T4
# 3) Dashboard
streamlit run app.py
```
El probador del dashboard usa el DistilBERT de `modelo/` si sus pesos están en la carpeta; si no, usa `modelo/tfidf_logreg.joblib`.

## Estructura
```
tarea_1/
├── 01_recoleccion.ipynb     # Scraping (RSS/sitemaps), limpieza, mapeo y EDA (Plotly)
├── 02_clasificacion.ipynb   # Zero-shot, LLM débil + auditoría, fine-tuning, evaluación
├── app.py                   # Dashboard Streamlit
├── requirements.txt
├── datos/  noticias.csv · etiquetas_llm.csv · auditoria_20.csv · raw/
├── figuras/                 # Gráficos del EDA (html/png)
└── modelo/ metricas.json · tfidf_logreg.joblib · matriz_confusion_test.png · config/tokenizer (pesos en .gitignore)
```

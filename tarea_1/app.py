"""Tarea 1 – Dashboard: ¿Pueden convertir titulares peruanos en un clasificador de noticias?

Ejecutar:  streamlit run app.py
Modelo usado en el probador (en este orden):
  1) modelo/ con pesos del DistilBERT fine-tuned (model.safetensors, solo local: no se sube a GitHub)
  2) modelo/tfidf_logreg.joblib (artefacto ligero, sí se sube)
  3) TF-IDF + LogReg entrenado al vuelo con datos/noticias.csv
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
DATOS = BASE / "datos" / "noticias.csv"
ETIQ = BASE / "datos" / "etiquetas_llm.csv"
MODELO = BASE / "modelo"
ORDEN = ["politica", "economia", "deportes", "ciencia_tecnologia"]
NOMBRES = {"politica": "Política", "economia": "Economía", "deportes": "Deportes",
           "ciencia_tecnologia": "Ciencia y tecnología"}

st.set_page_config(page_title="Clasificador de noticias peruanas", page_icon="🗞️", layout="wide")


@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATOS)
    if ETIQ.exists():
        e = pd.read_csv(ETIQ)
        if len(e) == len(df):
            df["etiqueta_llm"] = e["etiqueta_llm"].values
            df["confianza_llm"] = e["confianza"].values
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    return df


@st.cache_data
def cargar_metricas():
    p = MODELO / "metricas.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@st.cache_resource
def cargar_clasificador():
    pesos = list(MODELO.glob("*.safetensors")) + list(MODELO.glob("pytorch_model*.bin"))
    if (MODELO / "config.json").exists() and pesos:
        try:
            from transformers import pipeline
            clf = pipeline("text-classification", model=str(MODELO), tokenizer=str(MODELO), top_k=None)

            def predecir(texto):
                out = clf([texto], truncation=True, max_length=64)[0]
                return {d["label"]: float(d["score"]) for d in out}
            return predecir, "DistilBERT multilingüe fine-tuned"
        except Exception as e:  # noqa: BLE001
            st.sidebar.warning(f"No se pudo cargar el Transformer ({type(e).__name__}); se usa TF-IDF.")

    import joblib
    ruta = MODELO / "tfidf_logreg.joblib"
    pipe = None
    if ruta.exists():
        try:
            pipe = joblib.load(ruta)
            nombre = "TF-IDF + Regresión logística (artefacto ligero)"
        except Exception:  # noqa: BLE001  (p. ej. versión distinta de scikit-learn)
            pipe = None
    if pipe is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        d = cargar_datos()
        pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode"),
                             LogisticRegression(max_iter=2000, C=5, class_weight="balanced"))
        pipe.fit(d["titular"].astype(str), d["categoria"])
        nombre = "TF-IDF + Regresión logística (entrenado al iniciar)"

    def predecir(texto):
        probs = pipe.predict_proba([texto])[0]
        return dict(zip(pipe.classes_, map(float, probs)))
    return predecir, nombre


df = cargar_datos()
met = cargar_metricas()

# ---------------- Encabezado ----------------
st.title("🗞️ ¿Pueden convertir titulares peruanos en un clasificador de noticias?")
st.caption("Tarea 1 · Fundamentos de Python · Lita Leydi Acosta Carbajal · Opción C: La República vs. El Comercio")
with st.expander("📋 Resumen metodológico", expanded=False):
    st.markdown(f"""
1. **Recolección:** RSS y sitemaps oficiales listados en el `robots.txt` de La República y El Comercio
   (pausas de 1–2 s, User-Agent descriptivo, máx. 1 reintento). {len(df)} noticias válidas.
2. **Normalización:** cada `seccion_original` se mapeó a 4 categorías fijas: política, economía, deportes,
   ciencia y tecnología; el resto se descartó.
3. **Línea base zero-shot:** `{met.get('modelo_zeroshot', 'Recognai/bert-base-spanish-wwm-cased-xnli')}` sobre 40 titulares.
4. **Supervisión débil:** un LLM local (`{met.get('modelo_llm', 'Qwen2.5-Instruct')}`) etiquetó todo el dataset;
   se auditaron 20 casos a mano.
5. **Fine-tuning:** `distilbert-base-multilingual-cased` con split estratificado 70/15/15 (`random_state=42`),
   evaluado una sola vez sobre el test reservado.
""")

# ---------------- Filtros ----------------
st.sidebar.header("🔎 Filtros")
medios = sorted(df["medio"].dropna().unique())
sel_medios = st.sidebar.multiselect("Medio", medios, default=medios)
cats = [c for c in ORDEN if c in df["categoria"].unique()]
sel_cats = st.sidebar.multiselect("Categoría", cats, default=cats, format_func=lambda c: NOMBRES.get(c, c))
fdf = df[df["medio"].isin(sel_medios) & df["categoria"].isin(sel_cats)]

# ---------------- Métricas ----------------
c1, c2, c3 = st.columns(3)
c1.metric("Total de noticias recolectadas", f"{len(df):,}",
          delta=f"{len(fdf):,} con los filtros" if len(fdf) != len(df) else None, delta_color="off")
f1 = met.get("f1_macro_test")
c2.metric("F1 macro en test (fine-tuned)", f"{f1:.2f}" if f1 is not None else "—",
          delta=(f"{f1 - met['f1_zeroshot_40']:+.2f} vs. zero-shot" if f1 is not None and "f1_zeroshot_40" in met else None))
ac = met.get("acuerdo_llm_humano")
c3.metric("Concordancia LLM vs. auditoría humana", f"{ac / 20:.0%}" if ac is not None else "—",
          delta=f"{ac}/20 casos" if ac is not None else None, delta_color="off")
if not met:
    st.info("Aún no existe `modelo/metricas.json`: ejecuta `02_clasificacion.ipynb` para ver las métricas.")

# ---------------- Visualización ----------------
st.subheader("Distribución de categorías")
if fdf.empty:
    st.warning("No hay noticias con esos filtros.")
else:
    g = fdf.groupby(["categoria", "medio"]).size().reset_index(name="noticias")
    g["categoria"] = g["categoria"].map(NOMBRES)
    top = fdf["categoria"].value_counts()
    fig = px.bar(g, x="categoria", y="noticias", color="medio", barmode="group", text="noticias",
                 category_orders={"categoria": [NOMBRES[c] for c in ORDEN]},
                 title=f"{NOMBRES[top.index[0]]} concentra el {top.iloc[0] / top.sum():.0%} de las noticias filtradas",
                 labels={"categoria": "Categoría", "noticias": "Noticias", "medio": "Medio"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Explorar noticias")
    cols = [c for c in ["fecha", "medio", "categoria", "etiqueta_llm", "titular", "bajada", "seccion_original", "url"]
            if c in fdf.columns]
    st.dataframe(fdf[cols], width="stretch", hide_index=True,
                 column_config={"url": st.column_config.LinkColumn("url")})
    st.download_button("⬇️ Descargar CSV filtrado", fdf[cols].to_csv(index=False).encode("utf-8"),
                       file_name="noticias_filtradas.csv", mime="text/csv")

# ---------------- Probador en vivo ----------------
st.divider()
st.subheader("🧪 Probador en vivo")
predecir, nombre_modelo = cargar_clasificador()
st.caption(f"Modelo en uso: **{nombre_modelo}**")
titular = st.text_input("Escribe o pega un titular nuevo",
                        placeholder="Ej.: BCRP mantiene su tasa de referencia en 4,25% por tercer mes consecutivo")
if st.button("Clasificar titular", type="primary"):
    if not titular.strip():
        st.warning("Escribe un titular primero.")
    else:
        probs = predecir(titular.strip())
        pred = max(probs, key=probs.get)
        a, b = st.columns([1, 2])
        a.metric("Categoría predicha", NOMBRES.get(pred, pred), f"confianza {probs[pred]:.1%}", delta_color="off")
        pdf = pd.DataFrame({"categoria": [NOMBRES.get(k, k) for k in probs], "probabilidad": list(probs.values())})
        b.plotly_chart(px.bar(pdf.sort_values("probabilidad"), x="probabilidad", y="categoria", orientation="h",
                              range_x=[0, 1], text_auto=".1%", height=230,
                              title="Probabilidad por categoría"), width="stretch")

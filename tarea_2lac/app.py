"""Dashboard — Voces y documentos peruanos (Tarea 2). Solo lee CSV precalculados."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
D = BASE / "datos"
st.set_page_config(page_title="Voces y documentos peruanos", page_icon="📄", layout="wide")


@st.cache_data
def leer(nombre, rellenar=True):
    p = D / nombre
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    return df.fillna("") if rellenar else df


docs, aud = leer("documentos.csv"), leer("transcripciones.csv")
llm, met = leer("extraccion_llm.csv"), leer("metricas.csv")
det, audit = leer("eval_detalle.csv", rellenar=False), leer("auditoria_llm.csv")
campos = {r.id: json.loads(r.campos_json) for r in llm.itertuples()} if len(llm) else {}

st.title("¿Pueden convertirse documentos escaneados y audios en texto buscable?")
st.caption("Pipeline OCR (PaddleOCR) + ASR (faster-whisper + VAD + diarización) + extracción con LLM "
           "sobre 35 Reportes de Inflación del BCRP, fotos y manuscritos propios, y voces peruanas "
           "de OpenSLR 73 (CC BY-SA 4.0). Todo se calculó en notebooks; esta app solo explora resultados.")

# ---------------- Indicadores
def valor(modelo):
    f = met[met.modelo == modelo] if len(met) else met
    return f"{float(f.valor.iloc[0]):.3f}" if len(f) else "—"

c = st.columns(6)
c[0].metric("Documentos procesados", len(docs))
c[1].metric("Minutos de audio", f"{pd.to_numeric(aud.get('duracion_seg', pd.Series(dtype=float))).sum() / 60:.1f}")
c[2].metric("CER PaddleOCR", valor("PaddleOCR (base)"))
c[3].metric("CER EasyOCR", valor("EasyOCR (alternativo)"))
c[4].metric("WER whisper small", valor("faster-whisper small (base)"))
ok = pd.to_numeric(audit.get("correcto", pd.Series(dtype=float)), errors="coerce")
c[5].metric("Concordancia LLM vs. humano", f"{ok.mean():.0%}" if ok.notna().sum() else "—",
            help=f"{int(ok.sum())}/{ok.notna().sum()} extracciones completamente correctas" if ok.notna().sum() else None)

# ---------------- Filtros globales
with st.sidebar:
    st.header("Filtros")
    q = st.text_input("Buscar palabra en OCR y ASR").strip().lower()
    tipos = st.multiselect("Tipo de documento", sorted(docs.tipo.unique()) if len(docs) else [],
                           default=sorted(docs.tipo.unique()) if len(docs) else [])
    dur = pd.to_numeric(aud.duracion_seg) if len(aud) else pd.Series([0.0])
    rango = st.slider("Duración del clip (s)", 0.0, float(dur.max()) + 1, (0.0, float(dur.max()) + 1))

fd = docs[docs.tipo.isin(tipos)] if len(docs) else docs
fa = aud[pd.to_numeric(aud.duracion_seg).between(*rango)] if len(aud) else aud
if q:
    fd = fd[fd.texto_ocr.str.lower().str.contains(q, regex=False)]
    fa = fa[fa.texto_asr.str.lower().str.contains(q, regex=False)]

t1, t2, t3, t4 = st.tabs(["📊 Resultados", "📄 Documentos", "🎧 Audios", "🧪 Evaluación"])

with t1:
    a, b = st.columns(2)
    if len(fd):
        cnt = fd.tipo.value_counts().rename_axis("tipo").reset_index(name="n")
        a.plotly_chart(px.bar(cnt, x="tipo", y="n", color="tipo", text="n",
                              title="Documentos por tipo (filtrados)"), use_container_width=True)
    if len(fa):
        b.plotly_chart(px.histogram(fa, x="duracion_seg", nbins=15, color="n_hablantes",
                                    title="Duración de clips filtrados (s)"), use_container_width=True)
    st.subheader("Tabla de textos revisados y seudonimizados")
    tabla = pd.concat([
        fd.assign(modalidad="documento", texto=fd.texto_ocr)[["id", "modalidad", "tipo", "fuente", "texto"]] if len(fd) else pd.DataFrame(),
        fa.assign(modalidad="audio", tipo="clip", texto=fa.texto_asr)[["id", "modalidad", "tipo", "fuente", "texto"]] if len(fa) else pd.DataFrame()])
    st.dataframe(tabla, use_container_width=True, hide_index=True)
    st.download_button("Descargar CSV", tabla.to_csv(index=False).encode("utf-8"), "textos_filtrados.csv", "text/csv")

with t2:
    if len(fd):
        did = st.selectbox("Documento", fd.id, format_func=lambda i: f"{i} — {fd.set_index('id').loc[i, 'tipo']}")
        r = fd.set_index("id").loc[did]
        izq, der = st.columns([1, 1])
        with izq:
            st.markdown(f"**Fuente:** {r.fuente}  \n**Modelo:** {r.modelo_ocr}")
            if r.get("ejemplo_img") and (BASE / r.ejemplo_img).exists():
                st.image(str(BASE / r.ejemplo_img), caption="Captura propia (CC BY 4.0), sin datos personales")
            elif r.get("fuente_url"):
                st.link_button("Ver PDF original en bcrp.gob.pe", r.fuente_url)
            st.markdown("**Campos extraídos por el LLM**")
            st.json(campos.get(did, {"info": "sin extracción"}))
        with der:
            st.text_area("Texto OCR", r.texto_ocr, height=350)
            if r.texto_referencia:
                st.text_area("Referencia manual", r.texto_referencia, height=200)
                d = det[det.id == did] if len(det) else det
                if len(d):
                    st.metric("CER PaddleOCR", f"{float(d.cer_paddle.iloc[0]):.3f}",
                              delta=f"EasyOCR {float(d.cer_easyocr.iloc[0]):.3f}", delta_color="off")
    else:
        st.info("Ningún documento coincide con los filtros.")

with t3:
    if len(fa):
        cid = st.selectbox("Clip", fa.id, format_func=lambda i: f"{i} — {fa.set_index('id').loc[i, 'duracion_seg']} s")
        r = fa.set_index("id").loc[cid]
        st.markdown(f"**Fuente:** {r.fuente} · **Hablantes detectados:** {r.n_hablantes} "
                    f"(fuente: {r.get('n_hablantes_fuente', '?')}) · **Modelo:** {r.modelo_asr}")
        if r.get("ejemplo_audio") and (BASE / r.ejemplo_audio).exists():
            st.audio(str(BASE / r.ejemplo_audio))
            st.caption("Primeros 30 s. Audio OpenSLR 73, Google — CC BY-SA 4.0.")
        else:
            st.caption("Audio no publicado en el repo; reconstruible desde OpenSLR 73 (ver fuentes.csv).")
        texto = r.texto_asr.replace(" [HABLANTE_", "\n\n[HABLANTE_")
        st.text_area("Transcripción ASR (faster-whisper small)", texto, height=300)
        d = det[det.id == cid] if len(det) else det
        if len(d):
            x, y = st.columns(2)
            x.metric("WER whisper small", f"{float(d.wer_whisper.iloc[0]):.3f}")
            y.metric("WER wav2vec2", f"{float(d.wer_w2v.iloc[0]):.3f}")
            st.text_area("Transcripción wav2vec2 (alternativo)", str(d.texto_w2v.iloc[0]), height=150)
            st.text_area("Referencia manual", r.texto_referencia, height=150)
        st.markdown("**Campos extraídos por el LLM**")
        st.json(campos.get(cid, {"info": "sin extracción"}))
    else:
        st.info("Ningún clip coincide con los filtros.")

with t4:
    if len(met):
        st.dataframe(met, hide_index=True, use_container_width=True)
        st.plotly_chart(px.bar(met, x="modelo", y="valor", color="modalidad", text="valor",
                               title="Error por modelo (CER documentos / WER audio; menor es mejor)"),
                        use_container_width=True)
    if len(det):
        st.dataframe(det.drop(columns=[c for c in ["texto_easyocr", "texto_w2v"] if c in det]),
                     hide_index=True, use_container_width=True)
    if len(audit):
        st.subheader("Auditoría humana de 20 extracciones LLM")
        st.dataframe(audit[["id", "modalidad", "correcto", "error"]], hide_index=True, use_container_width=True)

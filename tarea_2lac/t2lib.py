"""Funciones del pipeline de la Tarea 2 (Voces y documentos peruanos).

Usado por 01_extraccion.ipynb y 02_evaluacion.ipynb. El dashboard (app.py)
NO importa este módulo: solo lee los CSV de datos/.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# En Windows torch debe cargarse ANTES que paddle: si paddle va primero,
# importar torch (easyocr, faster-whisper, wav2vec2) falla con WinError 127.
try:
    import torch  # noqa: F401
except ImportError:
    pass

BASE =Path(__file__).resolve().parent
DATOS = BASE / "datos"
RAW = DATOS / "raw"
RAW_DOCS = RAW / "documentos"
RAW_BCRP = RAW / "bcrp"
RAW_AUDIO = RAW / "audio"
REFS = DATOS / "referencias"
EJEMPLOS = DATOS / "ejemplos"

USER_AGENT = ("Tarea2-UNAC-DataSciencePython/1.0 (proyecto academico; "
              "descarga respetuosa con pausas de 1.5 s)")
PAUSA_SEG = 1.5

for _d in (DATOS, RAW_DOCS, RAW_BCRP, RAW_AUDIO, REFS, EJEMPLOS):
    _d.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Utilidades generales
# ----------------------------------------------------------------------------
def sha1_archivo(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def descargar(url: str, destino: Path, timeout: int = 120) -> bool:
    """Descarga con User-Agent descriptivo y pausa; no repite si ya existe."""
    import requests

    if destino.exists() and destino.stat().st_size > 0:
        return True
    destino.parent.mkdir(parents=True, exist_ok=True)
    time.sleep(PAUSA_SEG)
    try:
        with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True,
                          timeout=timeout) as r:
            if r.status_code != 200:
                return False
            tmp = destino.with_suffix(destino.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
            tmp.replace(destino)
        return True
    except Exception as e:  # red caída, timeout, etc.
        print(f"  ! error descargando {url}: {e}")
        return False


# ----------------------------------------------------------------------------
# A. Documentos impresos: Reportes de Inflación del BCRP
# ----------------------------------------------------------------------------
MESES_RI = ["diciembre", "setiembre", "junio", "marzo"]  # orden descendente
URL_RI = ("https://www.bcrp.gob.pe/docs/Publicaciones/Reporte-Inflacion/"
          "{anio}/{mes}/reporte-de-inflacion-{mes}-{anio}.pdf")


def descargar_reportes_inflacion(n: int = 35, anio_max: int = 2026,
                                 anio_min: int = 2015) -> pd.DataFrame:
    """Descarga los n Reportes de Inflación más recientes (4 por año)."""
    filas = []
    for anio in range(anio_max, anio_min - 1, -1):
        for mes in MESES_RI:
            if len(filas) >= n:
                break
            ok, url = False, None
            for mes_url in ([mes, "septiembre"] if mes == "setiembre" else [mes]):
                url = URL_RI.format(anio=anio, mes=mes_url)
                destino = RAW_BCRP / f"RI_{anio}_{mes}.pdf"
                ok = descargar(url, destino)
                if ok:
                    break
            if ok:
                filas.append({"anio": anio, "mes": mes, "url": url,
                              "pdf": str(destino.relative_to(BASE))})
                print(f"  ✓ RI {mes} {anio}")
            else:
                print(f"  - no disponible: RI {mes} {anio}")
    return pd.DataFrame(filas)


def elegir_pagina_texto(pdf_path: Path, desde: int = 2, hasta: int = 20) -> int:
    """Primera página con prosa abundante (≥1800 caracteres, pocos dígitos)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    mejor, mejor_len = desde, 0
    for i in range(desde, min(hasta, len(pdf))):
        txt = pdf[i].get_textpage().get_text_range()
        letras = sum(c.isalpha() for c in txt)
        digitos = sum(c.isdigit() for c in txt)
        if letras >= 1800 and digitos / max(letras, 1) < 0.08:
            return i
        if letras > mejor_len:
            mejor, mejor_len = i, letras
    return mejor


def renderizar_pagina(pdf_path: Path, pagina: int, destino: Path, dpi: int = 200):
    """Convierte una página del PDF en PNG y devuelve la capa de texto del PDF."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    page = pdf[pagina]
    page.render(scale=dpi / 72).to_pil().convert("RGB").save(destino)
    return page.get_textpage().get_text_range()


# ----------------------------------------------------------------------------
# OCR
# ----------------------------------------------------------------------------
def preparar_imagen(src: Path, destino: Path, lado_max: int = 2000) -> Path:
    """Corrige orientación EXIF y limita tamaño (fotos de celular)."""
    from PIL import Image, ImageOps

    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((lado_max, lado_max))
    im.save(destino, quality=92)
    return destino


_PADDLE = None


def ocr_paddle(img: Path) -> tuple[str, float, list]:
    """PaddleOCR 3.x (lang=es, modelos mobile). Devuelve texto, seg, crudo."""
    global _PADDLE
    from paddleocr import PaddleOCR

    if _PADDLE is None:
        _PADDLE = PaddleOCR(lang="es",
                            text_detection_model_name="PP-OCRv5_mobile_det",
                            use_doc_orientation_classify=False,
                            use_doc_unwarping=False,
                            use_textline_orientation=False)
    t0 = time.perf_counter()
    res = _PADDLE.predict(str(img))
    seg = time.perf_counter() - t0
    lineas, crudo = [], []
    for r in res:
        try:
            textos, scores = r["rec_texts"], r["rec_scores"]
        except Exception:
            j = r.json.get("res", r.json)
            textos, scores = j["rec_texts"], j["rec_scores"]
        lineas += list(textos)
        crudo += [{"t": t, "s": float(s)} for t, s in zip(textos, scores)]
    return "\n".join(lineas), seg, crudo


_EASY = None


def ocr_easyocr(img: Path) -> tuple[str, float]:
    """OCR alternativo: EasyOCR (CRAFT + CRNN), solo pip, CPU."""
    global _EASY
    import easyocr

    if _EASY is None:
        _EASY = easyocr.Reader(["es"], gpu=False, verbose=False)
    t0 = time.perf_counter()
    lineas = _EASY.readtext(str(img), detail=0, paragraph=True)
    return "\n".join(lineas), time.perf_counter() - t0


# ----------------------------------------------------------------------------
# B. Audio: OpenSLR 73 (español peruano, CC BY-SA 4.0)
# ----------------------------------------------------------------------------
OPENSLR_ESPEJOS = ["https://www.openslr.org/resources/73/",
                   "https://us.openslr.org/resources/73/",
                   "https://openslr.elda.org/resources/73/"]
OPENSLR_ZIPS = ["es_pe_female.zip", "es_pe_male.zip"]


def descargar_openslr73() -> list[Path]:
    rutas = []
    for nombre in OPENSLR_ZIPS + ["LICENSE"]:
        destino = RAW_AUDIO / "openslr73" / nombre
        for espejo in OPENSLR_ESPEJOS:
            print(f"  descargando {nombre} desde {espejo} ...")
            if descargar(espejo + nombre, destino, timeout=600):
                break
        if nombre.endswith(".zip"):
            carpeta = destino.with_suffix("")
            if not carpeta.exists():
                with zipfile.ZipFile(destino) as z:
                    z.extractall(carpeta)
            rutas.append(carpeta)
    return rutas


def leer_openslr(carpetas: list[Path]) -> pd.DataFrame:
    filas = []
    for carpeta in carpetas:
        wavs = {p.stem: p for p in carpeta.rglob("*.wav")}
        for idx in carpeta.rglob("line_index.tsv"):
            for linea in idx.read_text(encoding="utf-8").splitlines():
                partes = [p for p in linea.split("\t") if p.strip()]
                if len(partes) < 2 or partes[0].strip() not in wavs:
                    continue
                fid = partes[0].strip()
                filas.append({"fid": fid, "wav": wavs[fid],
                              "hablante": "_".join(fid.split("_")[:2]),
                              "genero": "F" if fid.startswith("pef") else "M",
                              "guion": partes[-1].strip()})
    return pd.DataFrame(filas)


def _cargar_16k(path: Path) -> np.ndarray:
    import soundfile as sf
    from scipy.signal import resample_poly

    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if sr != 16000:
        from math import gcd
        g = gcd(sr, 16000)
        x = resample_poly(x, 16000 // g, sr // g).astype("float32")
    return x


def construir_clips(utt: pd.DataFrame, n_mono: int = 22, n_multi: int = 2,
                    seg_objetivo: float = 82.0, semilla: int = 13) -> pd.DataFrame:
    """Une frases consecutivas de un mismo hablante en clips de ~80 s y crea
    clips multihablante alternando dos voces. Guarda WAV 16 kHz mono."""
    import soundfile as sf

    rng = random.Random(semilla)
    silencio = np.zeros(int(0.5 * 16000), dtype="float32")
    conteo = utt.groupby("hablante").size().sort_values(ascending=False)
    fem = [h for h in conteo.index if h.startswith("pef")]
    mas = [h for h in conteo.index if h.startswith("pem")]
    elegidos = []
    for i in range(max(len(fem), len(mas))):
        for lista in (fem, mas):
            if i < len(lista):
                elegidos.append(lista[i])
    usados = set()
    filas = []

    def _armar(lista_utt, cid, hablantes):
        partes, guion, seg = [], [], 0.0
        for _, u in lista_utt:
            x = _cargar_16k(u["wav"])
            partes += [x, silencio]
            guion.append(u["guion"])
            seg += (len(x) + len(silencio)) / 16000
            usados.add(u["fid"])
            if seg >= seg_objetivo:
                break
        audio = np.concatenate(partes)
        ruta = RAW_AUDIO / f"{cid}.wav"
        sf.write(ruta, audio, 16000)
        filas.append({"id": cid, "archivo_audio": str(ruta.relative_to(BASE)),
                      "duracion_seg": round(len(audio) / 16000, 1),
                      "hablantes_fuente": "+".join(hablantes),
                      "n_hablantes_fuente": len(hablantes),
                      "guion_openslr": " ".join(guion)})

    # clips multihablante primero (alternan voz femenina y masculina)
    for k in range(n_multi):
        a, b = fem[k], mas[k]
        ua = list(utt[utt.hablante == a].iterrows())
        ub = list(utt[utt.hablante == b].iterrows())
        alterna = [x for par in zip(ua, ub) for x in par]
        _armar(alterna, f"clip_{len(filas) + 1:03d}", [a, b])
    for h in elegidos:
        if len(filas) >= n_mono + n_multi:
            break
        resto = [x for x in utt[utt.hablante == h].iterrows()
                 if x[1]["fid"] not in usados]
        if sum(1 for _ in resto) < 8:
            continue
        rng.shuffle(resto)
        _armar(resto, f"clip_{len(filas) + 1:03d}", [h])
    return pd.DataFrame(filas)


def tiene_voz(path: Path, umbral_rms: float = 0.005) -> bool:
    x = _cargar_16k(path)
    return float(np.sqrt(np.mean(x ** 2))) > umbral_rms


# ----------------------------------------------------------------------------
# ASR + diarización
# ----------------------------------------------------------------------------
_WHISPER = {}


def asr_whisper(path: Path, tamano: str = "small") -> tuple[list[dict], float]:
    from faster_whisper import WhisperModel

    if tamano not in _WHISPER:
        _WHISPER[tamano] = WhisperModel(tamano, device="cpu", compute_type="int8")
    t0 = time.perf_counter()
    segs, _info = _WHISPER[tamano].transcribe(str(path), language="es",
                                              vad_filter=True, beam_size=5)
    segs = [{"inicio": s.start, "fin": s.end, "texto": s.text.strip()} for s in segs]
    return segs, time.perf_counter() - t0


def diarizar(path: Path, segs: list[dict], k_max: int = 4,
             umbral_sil: float = 0.30) -> list[dict]:
    """Diarización ligera: MFCC (media/desv.) + F0 mediana por segmento y
    clustering aglomerativo; k se elige por silueta (k=1 si silueta < umbral)."""
    import librosa
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    x = _cargar_16k(path)
    feats, validos = [], []
    for i, s in enumerate(segs):
        trozo = x[int(s["inicio"] * 16000): int(s["fin"] * 16000)]
        if len(trozo) < 16000 * 0.5:
            continue
        m = librosa.feature.mfcc(y=trozo, sr=16000, n_mfcc=20)
        f0 = librosa.yin(trozo, fmin=60, fmax=400, sr=16000)
        feats.append(np.r_[m.mean(1), m.std(1), np.median(f0) / 10])
        validos.append(i)
    etiquetas = [0] * len(segs)
    if len(feats) >= 4:
        X = StandardScaler().fit_transform(np.array(feats))
        mejor_k, mejor_s, mejor_lab = 1, umbral_sil, None
        for k in range(2, min(k_max, len(feats) - 1) + 1):
            lab = AgglomerativeClustering(n_clusters=k).fit_predict(X)
            s = silhouette_score(X, lab)
            if s > mejor_s:
                mejor_k, mejor_s, mejor_lab = k, s, lab
        if mejor_lab is not None:
            orden = {}
            for i, l in zip(validos, mejor_lab):
                orden.setdefault(l, len(orden))
                etiquetas[i] = orden[l]
            # segmentos cortos heredan la etiqueta del anterior
            for i in range(1, len(segs)):
                if i not in validos:
                    etiquetas[i] = etiquetas[i - 1]
    for s, e in zip(segs, etiquetas):
        s["hablante"] = f"HABLANTE_{e + 1}"
    return segs


def texto_con_hablantes(segs: list[dict]) -> str:
    bloques, actual = [], None
    for s in segs:
        if s["hablante"] != actual:
            actual = s["hablante"]
            bloques.append(f"[{actual}] {s['texto']}")
        else:
            bloques[-1] += " " + s["texto"]
    return " ".join(bloques)


def _ts(t: float) -> str:
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def exportar_asr(cid: str, segs: list[dict], carpeta: Path):
    carpeta.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(segs).to_csv(carpeta / f"{cid}.csv", index=False)
    (carpeta / f"{cid}.txt").write_text(texto_con_hablantes(segs), encoding="utf-8")
    srt = [f"{i}\n{_ts(s['inicio'])} --> {_ts(s['fin'])}\n[{s['hablante']}] {s['texto']}\n"
           for i, s in enumerate(segs, 1)]
    (carpeta / f"{cid}.srt").write_text("\n".join(srt), encoding="utf-8")


_W2V = {}


def asr_wav2vec2(path: Path,
                 modelo: str = "jonatasgrosman/wav2vec2-large-xlsr-53-spanish"
                 ) -> tuple[str, float]:
    """ASR alternativo (CTC, sin modelo de lenguaje), por bloques de 20 s."""
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

    if modelo not in _W2V:
        _W2V[modelo] = (Wav2Vec2Processor.from_pretrained(modelo),
                        Wav2Vec2ForCTC.from_pretrained(modelo).eval())
    proc, mod = _W2V[modelo]
    x = _cargar_16k(path)
    t0 = time.perf_counter()
    textos = []
    for i in range(0, len(x), 20 * 16000):
        entrada = proc(x[i:i + 20 * 16000], sampling_rate=16000,
                       return_tensors="pt", padding=True)
        with torch.inference_mode():
            logits = mod(entrada.input_values).logits
        textos.append(proc.batch_decode(logits.argmax(-1))[0])
    return " ".join(textos), time.perf_counter() - t0


# ----------------------------------------------------------------------------
# Seudonimización
# ----------------------------------------------------------------------------
PATRONES_PII = {
    "DNI": re.compile(r"\b(?:DNI\s*[:N°º.]*\s*)?\d{8}\b"),
    "TELEFONO": re.compile(r"\b9\d{2}[\s-]?\d{3}[\s-]?\d{3}\b"),
    "CORREO": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "PERSONA": re.compile(r"\b(?:Sr|Sra|Srta|señor|señora|Don|Doña)\.?\s+"
                          r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?"),
}


def seudonimizar(texto: str) -> tuple[str, int]:
    """Reemplaza DNI, teléfonos, correos y nombres con tratamiento. Los
    funcionarios públicos citados en su cargo (p. ej. presidente del BCRP) no
    son datos personales privados y se mantienen. Requiere revisión humana."""
    if not isinstance(texto, str):
        return texto, 0
    n = 0
    for etiqueta, pat in PATRONES_PII.items():
        texto, k = pat.subn(f"[{etiqueta}]", texto)
        n += k
    return texto, n


# ----------------------------------------------------------------------------
# Métricas
# ----------------------------------------------------------------------------
def normalizar(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = re.sub(r"\[HABLANTE_\d+\]", " ", t)
    t = unicodedata.normalize("NFC", t.lower())
    t = re.sub(r"[^\wáéíóúüñ\s]", " ", t)
    t = t.replace("_", " ")
    return re.sub(r"\s+", " ", t).strip()


def cer(ref: str, hyp: str) -> float:
    import jiwer
    r, h = normalizar(ref), normalizar(hyp)
    return float(jiwer.cer(r, h)) if r else np.nan


def wer(ref: str, hyp: str) -> float:
    import jiwer
    r, h = normalizar(ref), normalizar(hyp)
    return float(jiwer.wer(r, h)) if r else np.nan


# ----------------------------------------------------------------------------
# Extracción estructurada con LLM (Gemini API u Ollama local)
# ----------------------------------------------------------------------------
PROMPT_LLM = """Eres un asistente de extracción de información. Lee el texto y
devuelve SOLO un objeto JSON válido con estas claves:
- "modalidad": "{modalidad}"
- "tema": tema principal en máximo 8 palabras
- "resumen": resumen fiel en 1 o 2 oraciones
{extra}
Reglas: usa null cuando el dato no aparezca explícitamente en el texto.
No inventes datos. No agregues claves.

TEXTO ({tipo}):
\"\"\"{texto}\"\"\""""

EXTRA_DOC = ('- "emisor": institución o autor que emite el documento, o null\n'
             '- "fecha": fecha o periodo mencionado (texto literal), o null\n'
             '- "monto": primera cifra económica o porcentaje relevante con su unidad, o null')
EXTRA_AUD = ('- "numero_hablantes": número de hablantes si el texto tiene marcas '
             '[HABLANTE_n], si no null\n'
             '- "citas_clave": lista de hasta 2 frases textuales del audio')


def llm_proveedor() -> tuple[str, str]:
    prov = os.environ.get("LLM_PROVEEDOR", "gemini").lower()
    modelo = os.environ.get("LLM_MODELO",
                            "gemini-2.5-flash" if prov == "gemini" else "qwen2.5:3b")
    return prov, modelo


def extraer_llm(texto: str, modalidad: str, tipo: str) -> dict:
    prov, modelo = llm_proveedor()
    prompt = PROMPT_LLM.format(modalidad=modalidad, tipo=tipo,
                               extra=EXTRA_DOC if modalidad == "documento" else EXTRA_AUD,
                               texto=(texto or "")[:6000])
    if prov == "gemini":
        from google import genai
        from google.genai import types

        cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        r = cliente.models.generate_content(
            model=modelo, contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json",
                                               temperature=0))
        salida = r.text
    else:  # ollama
        import requests

        r = requests.post("http://localhost:11434/api/generate", timeout=300,
                          json={"model": modelo, "prompt": prompt, "format": "json",
                                "stream": False, "options": {"temperature": 0}})
        salida = r.json()["response"]
    try:
        datos = json.loads(salida)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", salida, re.S)
        datos = json.loads(m.group(0)) if m else {"error": salida[:200]}
    datos["modalidad"] = modalidad
    return datos

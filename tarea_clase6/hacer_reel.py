"""Del guion revisado a un reel vertical con tu voz clonada (pasos 4 y 5 de la sesión 15).

    guion.json + mi_voz.m4a  ->  salidas/reel.mp4, reel.srt, portada.png, posts.md

1. Convierte tu nota de voz a WAV 24 kHz y Whisper la transcribe (texto de referencia).
2. Qwen3-TTS clona tu voz y narra cada escena. Control: Whisper vuelve a escuchar la escena y,
   si entiende mal más del 25 % de las palabras, la genera de nuevo (hasta 3 intentos).
3. Whisper marca cuándo se dice cada palabra -> subtítulos con la palabra que suena en naranja.
4. Audio normalizado a -14 LUFS; video 1080x1920, 30 fps, H.264 + AAC (Reels, X, LinkedIn).
   Aviso «Voz generada con IA» durante todo el video. Nada importante en los bordes.

Uso en Windows (PowerShell, dentro de la carpeta reel_lory):
    .venv\\Scripts\\python hacer_reel.py --voz mi_voz.m4a --autor "Lory Acosta" ^
        --fuente "NASA FIRMS · Sentinel-2 · CENEPRED" --tts Qwen/Qwen3-TTS-12Hz-0.6B-Base

Prueba sin modelos (solo arma el video con un audio sintético):
    .venv\\Scripts\\python hacer_reel.py --prueba
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

try:  # consola de Windows (cp1252) no imprime «≤», «¡¡», tildes...
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

W, H, FPS = 1080, 1920, 30
SR_OUT = 48000
PAUSA_S = 0.35          # silencio entre escenas
FINAL_S = 1.2           # cola al final del video
MAX_ERROR = 0.25        # WER máximo aceptado por escena
INTENTOS = 3

# paleta (como las diapositivas de la sesión)
FONDO = (28, 26, 23)
CAJA = (44, 41, 37)
BLANCO = (247, 242, 235)
GRIS = (168, 160, 150)
NARANJA = (240, 136, 62)
LINEA = (70, 66, 60)

# zonas seguras: arriba van el nombre de la cuenta, abajo los botones y la descripción
MARGEN_X = 96
SEG_ARRIBA = 230
SEG_ABAJO = H - 400


# ----------------------------------------------------------------------------- utilidades
def log(msg: str) -> None:
    print(msg, flush=True)


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = shutil.which("ffmpeg")
        if not exe:
            sys.exit("No encuentro ffmpeg: instale imageio-ffmpeg (uv pip install imageio-ffmpeg)")
        return exe


def correr(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        sys.exit(f"Falló ffmpeg:\n{' '.join(cmd)}\n{r.stderr[-2000:]}")
    return r


def normalizar(t: str) -> str:
    """minúsculas, sin tildes ni puntuación, números a palabras (para comparar con Whisper)."""
    try:
        from num2words import num2words
        def a_palabras(m):
            s = m.group(0).replace(",", "")
            try:
                return num2words(float(s) if "." in s else int(s), lang="es")
            except Exception:
                return s
        t = re.sub(r"\d+(?:[.,]\d+)*", a_palabras, t)
    except ImportError:
        pass
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-zñ0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def tasa_error(ref: str, hip: str) -> float:
    ref_n, hip_n = normalizar(ref), normalizar(hip)
    try:
        import jiwer
        return float(jiwer.wer(ref_n, hip_n))
    except ImportError:
        sm = difflib.SequenceMatcher(None, ref_n.split(), hip_n.split())
        return 1 - sm.ratio()


def fuente_tipo(tam: int, negrita: bool = True, condensada: bool = False) -> ImageFont.FreeTypeFont:
    win = Path("C:/Windows/Fonts")
    candidatos = []
    if condensada:
        candidatos.append((win / "bahnschrift.ttf", "Bold Condensed" if negrita else "Regular"))
    if negrita:
        candidatos += [(win / "segoeuib.ttf", None), (win / "arialbd.ttf", None),
                       (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), None),
                       (Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"), None)]
    else:
        candidatos += [(win / "segoeui.ttf", None), (win / "arial.ttf", None),
                       (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), None),
                       (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), None)]
    for ruta, variante in candidatos:
        if ruta.exists():
            try:
                f = ImageFont.truetype(str(ruta), tam)
                if variante:
                    f.set_variation_by_name(variante)
                return f
            except Exception:
                continue
    return ImageFont.load_default(tam)


# ----------------------------------------------------------------------------- voz y tiempos
def cargar_whisper(tam: str):
    from faster_whisper import WhisperModel
    log(f"Cargando Whisper ({tam})…")
    return WhisperModel(tam, device="cpu", compute_type="int8")


def transcribir(whisper, wav: Path) -> tuple[str, list[dict]]:
    segs, _ = whisper.transcribe(str(wav), language="es", word_timestamps=True, beam_size=5)
    palabras, texto = [], []
    for s in segs:
        texto.append(s.text.strip())
        for w in s.words or []:
            palabras.append({"w": w.word.strip(), "ini": float(w.start), "fin": float(w.end)})
    return " ".join(texto), palabras


def alinear(frase: str, oidas: list[dict], dur: float) -> list[dict]:
    """Tiempos para cada palabra de la frase original (no la de Whisper, que puede equivocarse)."""
    tokens = frase.split()
    if not tokens:
        return []
    n_t = [normalizar(t) for t in tokens]
    n_o = [normalizar(o["w"]) for o in oidas]
    ini = [None] * len(tokens)
    fin = [None] * len(tokens)
    sm = difflib.SequenceMatcher(None, n_t, n_o, autojunk=False)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            ini[a + k], fin[a + k] = oidas[b + k]["ini"], oidas[b + k]["fin"]
    # interpolar las que Whisper no reconoció, según su largo en letras
    t0 = oidas[0]["ini"] if oidas else 0.05
    t1 = oidas[-1]["fin"] if oidas else max(dur - 0.05, 0.1)
    k = 0
    while k < len(tokens):
        if ini[k] is not None:
            k += 1
            continue
        j = k
        while j < len(tokens) and ini[j] is None:
            j += 1
        a_t = fin[k - 1] if k > 0 else t0
        b_t = ini[j] if j < len(tokens) else t1
        largos = [max(len(tokens[m]), 1) for m in range(k, j)]
        total = sum(largos)
        cur = a_t
        for m, lg in zip(range(k, j), largos):
            paso = (b_t - a_t) * lg / total
            ini[m], fin[m] = cur, cur + paso
            cur += paso
        k = j
    return [{"w": t, "ini": float(i), "fin": float(f)} for t, i, f in zip(tokens, ini, fin)]


def voz_prueba(frase: str, ruta: Path, sr: int = 24000) -> tuple[np.ndarray, list[dict]]:
    """Audio sintético (un tono por palabra) para probar el armado del video sin modelos."""
    tokens = frase.split()
    partes, palabras, t = [], [], 0.08
    partes.append(np.zeros(int(0.08 * sr), np.float32))
    for tok in tokens:
        d = 0.12 + 0.045 * len(tok)
        n = int(d * sr)
        tt = np.arange(n) / sr
        tono = 0.2 * np.sin(2 * np.pi * (180 + 6 * len(tok)) * tt) * np.hanning(n)
        partes += [tono.astype(np.float32), np.zeros(int(0.06 * sr), np.float32)]
        palabras.append({"w": tok, "ini": t, "fin": t + d})
        t += d + 0.06
    audio = np.concatenate(partes)
    sf.write(ruta, audio, sr)
    return audio, palabras


# ----------------------------------------------------------------------------- dibujo
def envolver(draw: ImageDraw.ImageDraw, texto: str, fuente, ancho: int) -> list[str]:
    lineas, actual = [], ""
    for p in texto.split():
        prueba = (actual + " " + p).strip()
        if draw.textlength(prueba, font=fuente) <= ancho or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def cifra_animada(cifra: str, avance: float) -> str:
    """Cuenta de 0 a la cifra en los primeros instantes de la escena (mantiene comas y decimales)."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", cifra)
    if not m or avance >= 1:
        return cifra
    s = m.group(0)
    dec = len(s.split(".")[1]) if "." in s else 0
    valor = float(s.replace(",", ""))
    e = 1 - (1 - avance) ** 3
    v = valor * e
    txt = f"{v:,.{dec}f}" if "," in s else f"{v:.{dec}f}"
    return cifra[:m.start()] + txt + cifra[m.end():]


def trozos(palabras: list[dict], max_pal: int = 4, max_car: int = 23) -> list[list[dict]]:
    """Agrupa palabras en líneas cortas de subtítulo."""
    out, cur = [], []
    for w in palabras:
        largo = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
        if cur and (len(cur) >= max_pal or largo > max_car):
            out.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.:;!?]$", w["w"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


class Lienzo:
    def __init__(self, autor: str, fuente_txt: str, titulo: str):
        self.autor, self.fuente_txt, self.titulo = autor, fuente_txt, titulo.upper()
        self.f_cifra = fuente_tipo(250, condensada=True)
        self.f_cifra_chica = fuente_tipo(170, condensada=True)
        self.f_etq = fuente_tipo(54, negrita=False)
        self.f_kicker = fuente_tipo(34)
        self.f_badge = fuente_tipo(26)
        self.f_sub = fuente_tipo(54)
        self.f_pie = fuente_tipo(28, negrita=False)
        self.f_portada = fuente_tipo(120, condensada=True)

    def cabecera(self, d: ImageDraw.ImageDraw, avance: float) -> None:
        y = SEG_ARRIBA
        d.line([(MARGEN_X, y), (W - MARGEN_X, y)], fill=LINEA, width=4)
        d.line([(MARGEN_X, y), (MARGEN_X + (W - 2 * MARGEN_X) * avance, y)], fill=NARANJA, width=8)
        d.text((MARGEN_X, y + 36), self.titulo, font=self.f_kicker, fill=NARANJA)
        txt = "VOZ GENERADA CON IA"
        tw = d.textlength(txt, font=self.f_badge)
        y2 = y + 96
        d.rounded_rectangle([MARGEN_X, y2, MARGEN_X + tw + 36, y2 + 50], radius=25, outline=GRIS, width=2)
        d.text((MARGEN_X + 18, y2 + 9), txt, font=self.f_badge, fill=BLANCO)

    def pie(self, d: ImageDraw.ImageDraw) -> None:
        txt = f"{self.autor} · Fuente: {self.fuente_txt}"
        lineas = envolver(d, txt, self.f_pie, W - 2 * MARGEN_X)
        y = SEG_ABAJO - 44 * len(lineas)
        for ln in lineas:
            d.text((MARGEN_X, y), ln, font=self.f_pie, fill=GRIS)
            y += 44

    def cuadro(self, escena: dict, t_esc: float, palabras: list[dict], t_abs: float, avance: float) -> Image.Image:
        img = Image.new("RGB", (W, H), FONDO)
        d = ImageDraw.Draw(img)
        self.cabecera(d, avance)

        # cifra grande + etiqueta
        cifra = escena.get("cifra", "")
        y = 640
        if cifra:
            txt = cifra_animada(cifra, min(t_esc / 0.7, 1))
            f = self.f_cifra
            if d.textlength(cifra, font=f) > W - 2 * MARGEN_X:
                f = self.f_cifra_chica
            d.text((MARGEN_X - 6, y), txt, font=f, fill=BLANCO)
            y += f.size + 40
        for ln in envolver(d, escena.get("etiqueta", ""), self.f_etq, W - 2 * MARGEN_X):
            d.text((MARGEN_X, y), ln, font=self.f_etq, fill=GRIS)
            y += 70

        # subtítulo: la palabra que suena va en naranja
        linea = None
        for tr in trozos(palabras):
            if tr[0]["ini"] - 0.15 <= t_abs <= tr[-1]["fin"] + 0.25:
                linea = tr
        if linea:
            sep = d.textlength(" ", font=self.f_sub)
            anchos = [d.textlength(w["w"], font=self.f_sub) for w in linea]
            total = sum(anchos) + sep * (len(linea) - 1)
            x0 = (W - total) / 2
            yb = 1330
            d.rounded_rectangle([x0 - 34, yb - 22, x0 + total + 34, yb + 90], radius=22, fill=CAJA)
            x = x0
            for w, aw in zip(linea, anchos):
                activo = w["ini"] <= t_abs <= w["fin"] + 0.05
                d.text((x, yb), w["w"], font=self.f_sub, fill=NARANJA if activo else BLANCO)
                x += aw + sep

        self.pie(d)
        return img

    def portada(self, escenas: list[dict]) -> Image.Image:
        img = Image.new("RGB", (W, H), FONDO)
        d = ImageDraw.Draw(img)
        self.cabecera(d, 1.0)
        y = 560
        for ln in ["¿Qué está", "ardiendo en", "el Perú?"]:
            d.text((MARGEN_X - 4, y), ln, font=self.f_portada, fill=BLANCO)
            y += 140
        e = escenas[0]
        y += 60
        d.text((MARGEN_X, y), e.get("cifra", ""), font=self.f_cifra_chica, fill=NARANJA)
        y += self.f_cifra_chica.size + 30
        for ln in envolver(d, e.get("etiqueta", ""), self.f_etq, W - 2 * MARGEN_X):
            d.text((MARGEN_X, y), ln, font=self.f_etq, fill=GRIS)
            y += 70
        self.pie(d)
        return img


# ----------------------------------------------------------------------------- salidas
def srt_tiempo(s: float) -> str:
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s_, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s_:02d},{ms:03d}"


def escribir_srt(palabras: list[dict], ruta: Path) -> None:
    bloques = []
    for k, tr in enumerate(trozos(palabras, max_pal=7, max_car=42), 1):
        txt = " ".join(w["w"] for w in tr)
        bloques.append(f"{k}\n{srt_tiempo(tr[0]['ini'])} --> {srt_tiempo(tr[-1]['fin'] + 0.2)}\n{txt}\n")
    ruta.write_text("\n".join(bloques), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--guion", default="guion.json")
    ap.add_argument("--voz", default="mi_voz.m4a", help="nota de voz de ~15 s (.m4a, .ogg, .wav, .mp3)")
    ap.add_argument("--texto-voz", default=None, help="lo que dijiste en la nota de voz (si no, lo transcribe Whisper)")
    ap.add_argument("--autor", default="Lory Acosta")
    ap.add_argument("--fuente", default="NASA FIRMS · Sentinel-2 · CENEPRED")
    ap.add_argument("--tts", default="Qwen/Qwen3-TTS-12Hz-0.6B-Base")
    ap.add_argument("--whisper", default="small", help="tiny, base, small, medium (más grande = más lento)")
    ap.add_argument("--salidas", default="salidas")
    ap.add_argument("--posts", default="posts.md")
    ap.add_argument("--prueba", action="store_true", help="sin modelos: audio sintético para probar el video")
    a = ap.parse_args()

    out = Path(a.salidas)
    (out / "escenas").mkdir(parents=True, exist_ok=True)
    guion = json.loads(Path(a.guion).read_text(encoding="utf-8"))
    escenas = guion["escenas"]
    ff = ffmpeg_exe()

    # ---------------------------------------------------------------- 1-2. voz por escena
    resultados = []   # (audio float32 mono, sr, palabras con tiempos)
    if a.prueba:
        log("Modo prueba: sin Qwen3-TTS ni Whisper")
        for k, e in enumerate(escenas, 1):
            audio, pal = voz_prueba(e["frase"], out / "escenas" / f"escena_{k}.wav")
            resultados.append((audio, 24000, pal))
    else:
        voz = Path(a.voz)
        if not voz.exists():
            sys.exit(f"No encuentro la nota de voz: {voz.resolve()}")
        ref_wav = out / "voz_referencia.wav"
        correr([ff, "-y", "-i", str(voz), "-t", "20", "-ac", "1", "-ar", "24000",
                "-af", "highpass=f=70,afftdn=nf=-25", str(ref_wav)])
        whisper = cargar_whisper(a.whisper)
        ref_text = a.texto_voz
        if not ref_text:
            ref_text, _ = transcribir(whisper, ref_wav)
        log(f"Texto de tu nota de voz: «{ref_text}»")

        import torch
        from qwen_tts import Qwen3TTSModel
        cuda = torch.cuda.is_available()
        log(f"Cargando {a.tts} en {'GPU' if cuda else 'CPU'} (la primera vez descarga el modelo)…")
        tts = Qwen3TTSModel.from_pretrained(a.tts, device_map="cuda:0" if cuda else "cpu",
                                            dtype=torch.bfloat16 if cuda else torch.float32)
        idiomas = tts.get_supported_languages() or []
        idioma = next((l for l in idiomas if "spanish" in str(l).lower() or str(l).lower() in ("es", "español")),
                      "Auto" if any(str(l).lower() == "auto" for l in idiomas) else None)
        log(f"Idioma: {idioma}")
        prompt = tts.create_voice_clone_prompt(ref_audio=str(ref_wav), ref_text=ref_text)

        for k, e in enumerate(escenas, 1):
            mejor = None
            for intento in range(1, INTENTOS + 1):
                wavs, sr = tts.generate_voice_clone(text=e["frase"], language=idioma, voice_clone_prompt=prompt)
                audio = np.asarray(wavs[0], dtype=np.float32)
                ruta = out / "escenas" / f"escena_{k}.wav"
                sf.write(ruta, audio, sr)
                oido, pal_oidas = transcribir(whisper, ruta)
                err = tasa_error(e["frase"], oido)
                log(f"Escena {k} intento {intento}: {len(audio) / sr:.1f} s · error Whisper {err:.0%}")
                if mejor is None or err < mejor[0]:
                    mejor = (err, audio, sr, pal_oidas)
                if err <= MAX_ERROR:
                    break
            err, audio, sr, pal_oidas = mejor
            if err > MAX_ERROR:
                log(f"   ¡¡ escena {k}: Whisper sigue entendiendo mal ({err:.0%}). Escúchela antes de publicar.")
            sf.write(out / "escenas" / f"escena_{k}.wav", audio, sr)
            resultados.append((audio, sr, alinear(e["frase"], pal_oidas, len(audio) / sr)))

    # ---------------------------------------------------------------- 3. unir audio + tiempos absolutos
    import librosa
    partes, palabras, tramos, t = [], [], [], 0.25
    partes.append(np.zeros(int(0.25 * SR_OUT), np.float32))
    for (audio, sr, pal), e in zip(resultados, escenas):
        if sr != SR_OUT:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=SR_OUT)
        dur = len(audio) / SR_OUT
        tramos.append((t, t + dur + PAUSA_S, e))
        palabras += [{"w": w["w"], "ini": w["ini"] + t, "fin": w["fin"] + t} for w in pal]
        partes += [audio.astype(np.float32), np.zeros(int(PAUSA_S * SR_OUT), np.float32)]
        t += dur + PAUSA_S
    partes.append(np.zeros(int(FINAL_S * SR_OUT), np.float32))
    voz_cruda = out / "voz_cruda.wav"
    sf.write(voz_cruda, np.concatenate(partes), SR_OUT)
    duracion = t + FINAL_S
    tramos[-1] = (tramos[-1][0], duracion, tramos[-1][2])

    # -14 LUFS (volumen de redes)
    voz_final = out / "reel_audio.wav"
    correr([ff, "-y", "-i", str(voz_cruda), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-ar", str(SR_OUT), "-ac", "2", str(voz_final)])
    log(f"Audio: {duracion:.1f} s" + ("  ¡¡ fuera de 30–60 s: ajuste el guion" if not 30 <= duracion <= 60 else ""))

    escribir_srt(palabras, out / "reel.srt")
    (out / "tiempos.json").write_text(json.dumps(palabras, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------------------------------------------------------------- 4. video
    lienzo = Lienzo(a.autor, a.fuente, guion.get("titulo", "Del texto a tu voz"))
    lienzo.portada(escenas).save(out / "portada.png")
    n = int(math.ceil(duracion * FPS))
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(voz_final), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", str(SR_OUT), "-shortest", "-movflags", "+faststart",
           str(out / "reel.mp4")]
    log(f"Armando video: {n} cuadros…")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for i in range(n):
        ta = i / FPS
        ini, fin, e = next(((a0, b0, e0) for a0, b0, e0 in tramos if a0 <= ta < b0), tramos[-1])
        if ta < tramos[0][0]:
            ini, fin, e = tramos[0]
        img = lienzo.cuadro(e, max(ta - ini, 0), palabras, ta, min(ta / duracion, 1))
        proc.stdin.write(img.tobytes())
        if i % (FPS * 10) == 0:
            log(f"   {ta:4.0f} s")
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0:
        sys.exit(f"Falló ffmpeg al codificar:\n{err[-2000:]}")

    # ---------------------------------------------------------------- 5. posts
    if Path(a.posts).exists():
        txt = Path(a.posts).read_text(encoding="utf-8")
        if "Voz generada con IA" not in txt:
            log("¡¡ posts.md no menciona «Voz generada con IA»: agréguelo al final de cada post")
        shutil.copy(a.posts, out / "posts.md")

    log(f"\nListo en {out.resolve()}:")
    for f in ["reel.mp4", "reel.srt", "portada.png", "posts.md"]:
        if (out / f).exists():
            log(f"   {f:12s} {(out / f).stat().st_size / 1e6:6.2f} MB")


if __name__ == "__main__":
    main()

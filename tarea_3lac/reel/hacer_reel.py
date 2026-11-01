"""Arma el reel vertical (1080 x 1920) a partir de reel/guion.json.

Cada escena muestra su cifra, su etiqueta y su imagen (reel/recursos/), con subtítulos palabra por palabra,
música de fondo opcional y el aviso «Voz generada con IA». La voz y los subtítulos reutilizan el módulo de la
sesión 15 del curso (Qwen3-TTS o VoxCPM2 para clonar la voz y Whisper para los tiempos de cada palabra).

Vista previa, sin voz (tiempos estimados, para revisar el diseño):
    uv run python reel/hacer_reel.py --vista-previa

Reel final con tu voz (usa el entorno .venv de la sesión 15, ver README):
    <sesion15>/.venv/Scripts/python reel/hacer_reel.py --voz reel/mi_voz.m4a --musica reel/recursos/musica.mp3

Salidas: reel/reel.mp4, reel/subtitulos.srt, reel/portada.png y reel/posts.md
(la vista previa va a reel/salidas/, que git ignora).
"""
import argparse
import importlib.util
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
SESION15 = AQUI.parents[2] / "Data-Science-Python" / "sessions" / "15-texto-a-reel"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

ANCHO, ALTO, FPS = 1080, 1920, 30
MARGEN = 90
FONDO, TEXTO, SUAVE, ACENTO, CAJA = "#1C1A17", "#F7F3EC", "#B8AE9F", "#F08A4B", "#2A2723"
PAUSA, INICIO, FINAL = 0.35, 0.3, 0.8      # silencios entre escenas, al inicio y al final (como en la sesión 15)
PALABRAS_POR_SEGUNDO = 2.6                 # solo para la vista previa
Y_BLOQUE, Y_IMAGEN, Y_SUB, Y_PIE = 390, 760, 1450, 1640
DASHBOARD = "loryac21-cyber.github.io/tareas-python/tarea_3lac/web"


@dataclass
class Narracion:
    """Misma forma que la Narracion de la sesión 15: audio, escenas (inicio, fin) y palabras (inicio, fin, texto)."""
    audio: np.ndarray
    sr: int
    escenas: list
    palabras: list = field(default_factory=list)

    @property
    def duracion(self):
        return len(self.audio) / self.sr


def _reloj(msg, t):
    print(f"[{time.time() - t:5.1f}s] {msg}", flush=True)


# Narración ------------------------------------------------------------------

def narracion_estimada(guion, sr=24000):
    """Sin voz: cada escena dura lo que tomaría leerla y las palabras se reparten de forma pareja."""
    escenas, palabras, t = [], [], INICIO
    for e in guion["escenas"]:
        texto = e["frase"].split()
        dur = len(texto) / PALABRAS_POR_SEGUNDO
        escenas.append((t, t + dur))
        paso = dur / len(texto)
        palabras += [(t + i * paso, t + (i + 1) * paso, p) for i, p in enumerate(texto)]
        t += dur + PAUSA
    audio = np.zeros(int((t + FINAL) * sr), np.float32)
    return Narracion(audio, sr, escenas, palabras)


def narracion_con_voz(guion, voz, motor, tts, device, velocidad, sesion15):
    """Clona la voz y transcribe con el módulo reel.py de la sesión 15."""
    spec = importlib.util.spec_from_file_location("reel_sesion15", sesion15 / "reel.py")
    r15 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r15)
    v = r15.VozExpresiva(voz, device=device) if motor == "voxcpm" else r15.Voz(voz, modelo=tts or r15.TTS, device=device)
    print(f"   referencia transcrita: «{v.texto_ref}»")
    n = r15.narrar(v, guion, velocidad=velocidad)
    r15.subtitulos(n, guion)
    return Narracion(n.audio, n.sr, n.escenas, n.palabras)


# Subtítulos -----------------------------------------------------------------

def bloques(palabras, max_palabras=4, max_letras=24):
    """Bloques cortos para leer en el celular; corta en signos de puntuación."""
    salida, actual = [], []
    for p in palabras:
        actual.append(p)
        largo = sum(len(x[2]) + 1 for x in actual)
        if len(actual) >= max_palabras or largo >= max_letras or p[2][-1] in ".,;:?!":
            salida.append(actual)
            actual = []
    if actual:
        salida.append(actual)
    return salida


def a_srt(narracion, ruta):
    def hms(t):
        return f"{int(t // 3600):02}:{int(t % 3600 // 60):02}:{int(t % 60):02},{int(t % 1 * 1000):03}"
    lineas = []
    for i, b in enumerate(bloques(narracion.palabras), 1):
        lineas += [str(i), f"{hms(b[0][0])} --> {hms(b[-1][1])}", " ".join(p[2] for p in b), ""]
    Path(ruta).write_text("\n".join(lineas), encoding="utf-8")


# Diseño ---------------------------------------------------------------------

_FUENTES = {
    # Windows trae Bahnschrift (condensada, para cifras) y Segoe UI; si no están, se usa DejaVu de Pillow
    "cifra": ("C:/Windows/Fonts/bahnschrift.ttf", [700, 75]),
    "negrita": ("C:/Windows/Fonts/segoeuib.ttf", None),
    "semi": ("C:/Windows/Fonts/seguisb.ttf", None),
    "normal": ("C:/Windows/Fonts/segoeui.ttf", None),
}


def fuente(tipo, tam):
    ruta, ejes = _FUENTES[tipo]
    try:
        f = ImageFont.truetype(ruta, tam)
        if ejes:
            f.set_variation_by_axes(ejes)
        return f
    except OSError:
        return ImageFont.load_default(tam)


_RESPALDO = "C:/Windows/Fonts/seguisym.ttf"   # Segoe UI Symbol: flechas que Bahnschrift no tiene


def _tramos(texto, f):
    """Parte el texto en tramos que la fuente sí dibuja y caracteres que van con la fuente de respaldo (p. ej. «→»)."""
    try:
        from fontTools.ttLib import TTFont
        cmap = TTFont(f.path).getBestCmap()
        respaldo = ImageFont.truetype(_RESPALDO, f.size)
    except Exception:
        return [(texto, f)]
    tramos = []
    for ch in texto:
        fc = f if ord(ch) in cmap or ch == " " else respaldo
        if tramos and tramos[-1][1] is fc:
            tramos[-1] = (tramos[-1][0] + ch, fc)
        else:
            tramos.append((ch, fc))
    return tramos


def largo_mixto(d, texto, f):
    return sum(d.textlength(t, font=ft) for t, ft in _tramos(texto, f))


def texto_mixto(d, x, y, texto, f, color):
    for t, ft in _tramos(texto, f):
        d.text((x, y), t, font=ft, fill=color, anchor="ls")
        x += d.textlength(t, font=ft)


def envolver(d, texto, f, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if d.textlength(prueba, font=f) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    return lineas + [actual]


def base(guion, autor, fuente_datos):
    """Lo fijo: título, aviso de voz con IA, autor, fuente y enlace al tablero."""
    img = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(img)
    d.text((MARGEN, 205), guion["titulo"].upper(), font=fuente("negrita", 38), fill=ACENTO)
    aviso, f = "VOZ GENERADA CON IA", fuente("negrita", 27)
    x1 = MARGEN + d.textlength(aviso, font=f) + 36
    d.rounded_rectangle((MARGEN, 268, x1, 316), radius=24, outline=SUAVE, width=2)
    d.text((MARGEN + 18, 292), aviso, font=f, fill=SUAVE, anchor="lm")
    pie = fuente("normal", 30)
    y = Y_PIE
    for linea in envolver(d, f"{autor} · Fuente: {fuente_datos}", pie, ANCHO - 2 * MARGEN):
        d.text((MARGEN, y), linea, font=pie, fill=SUAVE)
        y += 42
    d.text((MARGEN, y + 12), "Tablero: " + DASHBOARD, font=fuente("semi", 28), fill=TEXTO)
    return img


def capa_escena(e):
    """Capa transparente con la cifra, la etiqueta y la imagen de la escena."""
    capa = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    ancho = ANCHO - 2 * MARGEN
    y = Y_BLOQUE
    if e.get("cifra"):
        tam = 190
        while largo_mixto(d, e["cifra"], fuente("cifra", tam)) > ancho and tam > 90:
            tam -= 10
        f = fuente("cifra", tam)
        alto = -d.textbbox((0, 0), "0", font=f, anchor="ls")[1]
        texto_mixto(d, MARGEN, y + alto, e["cifra"], f, TEXTO)
        y += alto + 34
        fe, color = fuente("semi", 44), SUAVE
    else:
        fe, color = fuente("negrita", 76), TEXTO
    for linea in envolver(d, e["etiqueta"], fe, ancho):
        d.text((MARGEN, y), linea, font=fe, fill=color)
        y += int(fe.size * 1.25)
    ruta = AQUI / e["visual"]
    if ruta.exists():
        img = Image.open(ruta).convert("RGBA")
        img.thumbnail((ancho, Y_SUB - 60 - max(y + 20, Y_IMAGEN)))
        capa.alpha_composite(img, (MARGEN + (ancho - img.width) // 2, max(y + 20, Y_IMAGEN)))
    return capa


def cuadro(fondo, capas, narracion, t, grupos, fuente_sub):
    img = fondo.copy()
    i = max([k for k, (ini, _) in enumerate(narracion.escenas) if ini - PAUSA <= t] or [0])
    a = min(1.0, max(0.0, (t - narracion.escenas[i][0] + PAUSA) / 0.35))   # entrada suave de cada escena
    capa = capas[i]
    if a < 1:
        capa = capa.copy()
        capa.putalpha(capa.getchannel("A").point(lambda v: int(v * a)))
    img.paste(capa, (0, int(40 * (1 - a))), capa)

    d = ImageDraw.Draw(img)
    d.rounded_rectangle((MARGEN, 150, ANCHO - MARGEN, 158), radius=4, fill=CAJA)
    d.rounded_rectangle((MARGEN, 150, MARGEN + (ANCHO - 2 * MARGEN) * min(1, t / narracion.duracion), 158), radius=4, fill=ACENTO)

    b = next((b for b in grupos if b[0][0] - 0.1 <= t <= b[-1][1] + 0.25), None)
    if b:
        texto = " ".join(p[2] for p in b)
        w = d.textlength(texto, font=fuente_sub)
        x = (ANCHO - w) / 2
        d.rounded_rectangle((x - 34, Y_SUB - 24, x + w + 34, Y_SUB + fuente_sub.size + 30), radius=28, fill=CAJA)
        for ini, fin, palabra in b:
            d.text((x, Y_SUB), palabra, font=fuente_sub, fill=ACENTO if ini <= t <= fin + 0.05 else TEXTO)
            x += d.textlength(palabra + " ", font=fuente_sub)
    return img.convert("RGB")


def video(guion, narracion, ruta, autor, fuente_datos, musica=None, volumen_musica=0.12, con_voz=True):
    """Dibuja cada cuadro con Pillow y se los pasa a ffmpeg con la narración (y la música, más baja)."""
    ruta = Path(ruta)
    wav = ruta.with_suffix(".wav")
    sf.write(wav, narracion.audio, narracion.sr)
    fondo = base(guion, autor, fuente_datos)
    capas = [capa_escena(e) for e in guion["escenas"]]
    grupos, fuente_sub = bloques(narracion.palabras), fuente("negrita", 58)
    dur = narracion.duracion

    entradas = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ANCHO}x{ALTO}", "-r", str(FPS), "-i", "-", "-i", str(wav)]
    voz = "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[voz]" if con_voz else "[1:a]anull[voz]"
    if musica:
        entradas += ["-stream_loop", "-1", "-i", str(musica)]
        filtro = (f"{voz};[2:a]volume={volumen_musica},afade=t=in:d=1.5,afade=t=out:st={max(0, dur - 2.5):.2f}:d=2.5[mus];"
                  "[voz][mus]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        filtro = voz.replace("[voz]", "[a]")
    cmd = [FFMPEG, "-y", "-v", "error", *entradas, "-filter_complex", filtro, "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", f"{dur:.2f}", "-movflags", "+faststart", str(ruta)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(int(dur * FPS)):
        proc.stdin.write(cuadro(fondo, capas, narracion, k / FPS, grupos, fuente_sub).tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink(missing_ok=True)
    return ruta


def portada(guion, narracion, ruta, autor, fuente_datos, escena=0):
    t = narracion.escenas[escena][0] + 1.0
    cuadro(base(guion, autor, fuente_datos), [capa_escena(e) for e in guion["escenas"]], narracion, t,
           bloques(narracion.palabras), fuente("negrita", 58)).save(ruta)


def posts(guion, ruta):
    h = " ".join(guion.get("hashtags", []))
    p = guion["posts"]
    Path(ruta).write_text(
        f"# {guion['titulo']}\n\n## LinkedIn\n\n{p['linkedin']}\n\n{h}\n\n"
        f"## X ({len(p['x'])} caracteres)\n\n{p['x']}\n\n## Facebook\n\n{p['facebook']}\n\n{h}\n",
        encoding="utf-8")


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--vista-previa", action="store_true", help="sin voz: tiempos estimados, para revisar el diseño")
    a.add_argument("--voz", help="10 a 25 s de tu voz (wav, m4a, ogg/opus de WhatsApp, mp3)")
    a.add_argument("--musica", help="música de fondo con licencia de uso (mp3/wav); se repite y se atenúa")
    a.add_argument("--volumen-musica", type=float, default=0.12)
    a.add_argument("--autor", default="Nombre Apellido", help="tu nombre, aparece en el pie del video")
    a.add_argument("--fuente", default="SUNAT, Nota Tributaria (cuadros G8 y G9)")
    a.add_argument("--motor", default="qwen", choices=["qwen", "voxcpm"])
    a.add_argument("--tts", default=None, help="modelo Qwen3-TTS; Qwen/Qwen3-TTS-12Hz-0.6B-Base es más rápido en CPU")
    a.add_argument("--device", default="cpu", help="cpu o cuda")
    a.add_argument("--velocidad", type=float, default=1.0)
    a.add_argument("--sesion15", default=str(SESION15), help="carpeta sessions/15-texto-a-reel del curso")
    args = a.parse_args()
    if not args.vista_previa and not args.voz:
        a.error("usa --vista-previa o --voz mi_voz.m4a")

    t0 = time.time()
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    for e in guion["escenas"]:
        print(f"   {e['cifra'] or '-':>12} | {e['frase']}")

    if args.vista_previa:
        n = narracion_estimada(guion)
        salidas = AQUI / "salidas"
        salidas.mkdir(exist_ok=True)
        destino, srt = salidas / "vista_previa.mp4", AQUI / "subtitulos.srt"
    else:
        n = narracion_con_voz(guion, args.voz, args.motor, args.tts, args.device, args.velocidad, Path(args.sesion15))
        (AQUI / "guion.json").write_text(json.dumps(guion, ensure_ascii=False, indent=2), encoding="utf-8")  # guarda el WER por escena
        destino, srt = AQUI / "reel.mp4", AQUI / "subtitulos.srt"
    _reloj(f"narración: {n.duracion:.1f} s en {len(n.escenas)} escenas", t0)

    a_srt(n, srt)
    portada(guion, n, AQUI / "portada.png", args.autor, args.fuente)
    posts(guion, AQUI / "posts.md")
    video(guion, n, destino, args.autor, args.fuente, args.musica, args.volumen_musica, con_voz=not args.vista_previa)
    _reloj(f"listo: {destino.relative_to(AQUI.parent)} · {srt.relative_to(AQUI.parent)}", t0)

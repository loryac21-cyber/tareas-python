# Reel · Café, cacao y madera bajo la lupa de Europa

Video vertical de unos 64 s (1080 × 1920) en 6 escenas, cada una con su cifra y un gráfico o mapa:

| # | Cifra | Visual | Narración (resumen) |
|---|---|---|---|
| 1 | 40 % | Mapa de destinos en la UE (2025) | 4 de cada 10 dólares de café y cacao se venden en la UE |
| 2 | 30/12/2026 | Línea de tiempo del EUDR | Desde esa fecha, Europa exigirá probar que no hay deforestación |
| 3 | US$ 1400 M | Barras FOB a la UE por producto | Lo vendido a Europa en 2025: casi el 14 % de todo lo que se le exporta |
| 4 | x5 | Cacao: valor frente a volumen | El cacao a la UE se multiplicó por cinco, sobre todo por precio |
| 5 | 54 % → 40 % | Parte del café que compra la UE | El café va en sentido contrario |
| 6 | — | Captura del dashboard | Invitación a explorar el tablero |

Cada cifra está anotada en `guion.json` (campo `verificacion`) con su origen en `03_analisis.ipynb`.

## Archivos

| Archivo | Qué es |
|---|---|
| `guion.json` | Guion por escenas, con el formato de la sesión 15 del curso (frase, cifra, etiqueta, estilo de voz y posts) |
| `generar_recursos.py` | Dibuja las imágenes de cada escena en `recursos/` a partir de `datos/procesados/` |
| `hacer_reel.py` | Arma el video: narración, subtítulos palabra por palabra, música y aviso de IA |
| `recursos/` | Imágenes de las escenas (y aquí va la música, `musica.mp3`) |
| `subtitulos.srt` | Subtítulos. **Ahora tienen tiempos estimados**: se regeneran con los tiempos reales al narrar con tu voz |
| `portada.png` | Miniatura para LinkedIn |
| `posts.md` | Textos para LinkedIn, X y Facebook |
| `reel.mp4` | El video final (se crea en el paso 4) |

## Pasos

**1. Vista previa sin voz** (ya hecha; sirve para revisar el diseño):

```bash
uv run python reel/generar_recursos.py
uv run python reel/hacer_reel.py --vista-previa      # reel/salidas/vista_previa.mp4
```

**2. Graba tu voz (15 a 25 s).** Una nota de voz de WhatsApp sirve. Busca un cuarto callado, ponte a un palmo del micrófono y lee con el tono
que quieres en el reel. Por ejemplo, la primera escena del guion y un par de frases más. Guárdala como `reel/mi_voz.m4a` (o `.opus`, `.wav`).
Git la ignora.

**3. Prepara el entorno de la sesión 15**, una sola vez. La primera corrida baja unos 4 GB de modelos:

```bash
cd ../../Data-Science-Python/sessions/15-texto-a-reel
uv venv .venv
uv pip install --python .venv\Scripts\python qwen-tts faster-whisper pillow imageio-ffmpeg soundfile jiwer num2words fonttools
```

**4. Música.** Usa una pista con licencia de uso libre, por ejemplo de la Biblioteca de audio de YouTube o de Pixabay Music. Guárdala como
`reel/recursos/musica.mp3` y anota el título, el autor y la licencia en la sección de créditos de este README.

**5. Reel final con tu voz clonada** (desde `tarea_3lac/`, con el Python de la sesión 15):

```bash
..\..\Data-Science-Python\sessions\15-texto-a-reel\.venv\Scripts\python reel\hacer_reel.py ^
    --voz reel\mi_voz.m4a --musica reel\recursos\musica.mp3 --autor "Tu Nombre" ^
    --tts Qwen/Qwen3-TTS-12Hz-0.6B-Base
```

El script narra cada escena con tu voz y revisa con Whisper que se entienda (WER por escena en `guion.json`). Luego escribe `reel.mp4`,
`subtitulos.srt` con los tiempos reales, `portada.png` y `posts.md`. Míralo completo antes de publicar: las cifras deben sonar bien.

## Transparencia y créditos

- El video muestra «VOZ GENERADA CON IA» durante todo el reel, y la fuente de los datos en el pie: SUNAT, Nota Tributaria (cuadros G8 y G9).
- **Voz:** generada con Qwen3-TTS (Alibaba, Apache 2.0) a partir de la grabación de mi propia voz.
- **Subtítulos:** Whisper large-v3-turbo (MIT).
- **Gráficos y mapa:** elaboración propia con matplotlib y Plotly a partir de datos de SUNAT.
- **Música:** _(completar: título, autor, fuente y licencia)_.

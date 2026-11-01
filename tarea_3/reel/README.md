# Reel · Café y cacao: ¿vendimos más o más caro?

Video vertical de unos 60 s (1080 × 1920) en 6 escenas, cada una con su cifra y un gráfico:

| # | Cifra | Visual | Narración (resumen) |
|---|---|---|---|
| 1 | x2,9 | Café: valor frente a volumen (2015 = 1) | El valor del café casi se triplicó, pero el volumen creció 31 % |
| 2 | 74 % | Barras: aumento del valor por precio y por volumen | Tres de cada cuatro dólares adicionales vinieron del precio |
| 3 | x6,1 | Cacao: valor frente a volumen | El cacao creció en valor y también en volumen |
| 4 | −48 % | Cacao: precio internacional y valor unitario, 2023–2026 | En 2026 el precio promedio fue la mitad y el valor bajó 48 % |
| 5 | 10,4 vs 6,1 | Regiones de destino 2015 frente a 2025 | El cacao se abrió al mundo; el café depende más de EE. UU. |
| 6 | — | Captura del dashboard | Usar los buenos precios para invertir en productividad, calidad y mercados |

Cada cifra está anotada en `guion.json` (campo `verificacion`) con su origen en los datos procesados y en `03_analisis.ipynb`. El tono
sigue la guía [`../comunicacion.md`](../comunicacion.md): datos con fuente, sin alarmismo y con un cierre propositivo.

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
| `reel.mp4` | El video final (se crea en el paso 5) |

## Pasos

**1. Vista previa sin voz** (ya hecha; sirve para revisar el diseño):

```bash
uv run python reel/generar_recursos.py
uv run python reel/hacer_reel.py --vista-previa      # reel/salidas/vista_previa.mp4
```

**2. Graba tu voz (15 a 25 s).** Una nota de voz de WhatsApp sirve. Busca un cuarto callado, ponte a un palmo del micrófono y lee con el tono
que quieres en el reel, por ejemplo la primera escena del guion y un par de frases más. Guárdala como `reel/mi_voz.m4a` (o `.opus`,
`.wav`). Git la ignora.

**3. Prepara el entorno de la sesión 15**, una sola vez. La primera corrida baja unos 4 GB de modelos:

```bash
cd ../../Data-Science-Python/sessions/15-texto-a-reel
uv venv .venv
uv pip install --python .venv\Scripts\python qwen-tts faster-whisper pillow imageio-ffmpeg soundfile jiwer num2words fonttools
```

**4. Música.** Usa una pista con licencia de uso libre, por ejemplo de la Biblioteca de audio de YouTube o de Pixabay Music. Guárdala como
`reel/recursos/musica.mp3` y anota el título, el autor y la licencia en la sección de créditos de este README.

**5. Reel final con tu voz clonada** (desde `tarea_3/`, con el Python de la sesión 15):

```bash
..\..\Data-Science-Python\sessions\15-texto-a-reel\.venv\Scripts\python reel\hacer_reel.py ^
    --voz reel\mi_voz.m4a --musica reel\recursos\musica.mp3 --autor "Tu Nombre" ^
    --tts Qwen/Qwen3-TTS-12Hz-0.6B-Base
```

El script narra cada escena con tu voz y revisa con Whisper que se entienda (WER por escena en `guion.json`). Luego escribe `reel.mp4`,
`subtitulos.srt` con los tiempos reales, `portada.png` y `posts.md`. Míralo completo antes de publicar: las cifras deben sonar bien.

## Transparencia y créditos

- El video muestra «VOZ GENERADA CON IA» durante todo el reel, y en el pie la fuente de los datos: SUNAT (Nota Tributaria) y Banco Mundial
  (Pink Sheet).
- **Voz:** generada con Qwen3-TTS (Alibaba, Apache 2.0) a partir de la grabación de mi propia voz.
- **Subtítulos:** Whisper large-v3-turbo (MIT).
- **Gráficos:** elaboración propia con matplotlib a partir de datos de SUNAT y del Banco Mundial.
- **Música:** _(completar: título, autor, fuente y licencia)_.

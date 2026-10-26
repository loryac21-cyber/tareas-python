# Reel «Monitor de Incendios Perú 2026» · Tarea sesión 15 (Del texto a tu voz)

Lory Acosta · texto fuente: mi dashboard de la Tarea 5 (`Tarea-clase5`).

| Paso | Archivo | Estado |
|---|---|---|
| 1 · Texto largo | `fuente_incendios.md` (del dashboard y el notebook) | listo |
| 2 · Guion | `guion.json` (6 escenas, ~55 s) | listo |
| 3 · Revisión | `revision.md` + `verificar_guion.py` | **léelo tú también contra la fuente** |
| 4 · Tu voz | `texto_para_grabar.txt` → `mi_voz.m4a` | grábala |
| 5 · Video | `hacer_reel.py` → `salidas/reel.mp4` | correr en tu PC |
| Posts | `posts.md` (Instagram, X, LinkedIn) | pon el enlace al tablero |
| Excelente | `prompt_guion.txt` → pegar en chat.qwen.ai y chat.deepseek.com | comparar |

## En Windows (PowerShell)

Copia esta carpeta `reel_lory` en tu repo del curso (por ejemplo `Data-Science-Python\sessions\15-texto-a-reel\`), abre PowerShell ahí y ejecuta:

```powershell
# 1. entorno e instalación (una vez; descarga torch, ~1 GB)
uv venv .venv --python 3.12
uv pip install --python .venv\Scripts\python.exe qwen-tts faster-whisper pillow imageio-ffmpeg soundfile librosa jiwer num2words

# 2. revisar cifras del guion contra la fuente
.venv\Scripts\python verificar_guion.py

# 3. graba mi_voz.m4a con texto_para_grabar.txt y guárdala en esta carpeta

# 4. voz + subtítulos + video (la primera vez descarga unos 3 GB de modelos de Hugging Face)
.venv\Scripts\python hacer_reel.py --voz mi_voz.m4a --autor "Lory Acosta" --fuente "NASA FIRMS · Sentinel-2 · CENEPRED" --tts Qwen/Qwen3-TTS-12Hz-0.6B-Base
```

Sale en `salidas\`: `reel.mp4`, `reel.srt`, `portada.png`, `posts.md` (y cada escena en `salidas\escenas\` para escucharla).

- Usa el modelo **0.6B** (no tienes Mac con chip M). En CPU tarda varios minutos; es normal.
- Control automático: si Whisper entiende mal más del 25 % de una escena, la vuelve a generar (hasta 3 veces) y avisa con ¡¡ si sigue mal.
- `--prueba` arma el video con un audio sintético, sin modelos, para revisar el diseño en segundos.
- Si `uv` no está instalado: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`.

## Antes de publicar (las tres reglas)
1. **Solo tu voz.**
2. **Declara la IA:** el video muestra «Voz generada con IA» todo el tiempo, y cada post lo dice al final.
3. **Revisa la fuente:** lee `guion.json` completo contra `fuente_incendios.md` antes de narrar.

## Entrega
Sube `salidas\reel.mp4` y `posts.md` como comentario en el issue de la sesión 15. Para el nivel «Bueno», agrega lo que corregiste del guion (`revision.md`).

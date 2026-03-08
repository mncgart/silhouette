# Model Recommendations for RTX 4090 Laptop (16 GB VRAM / 32 GB RAM)

## Direct answer
`FLUX.2 + WAN 2.2 + LTX-2 + Audio + Music` is a strong target stack, but on a laptop 4090 you should run a **tiered strategy**:

1. **Fast draft models** for iteration.
2. **Quality models** for selected final shots.
3. Keep one heavy video model optional to avoid thermal throttling and OOM.

## Suggested stack

### 1) Idea + Scriptwriting
- **Best practical local pick:** `Qwen2.5-7B-Instruct`
- **Higher quality (slower):** `Qwen2.5-14B` quantized

### 2) Image generation
- **Best draft speed:** `FLUX.1-schnell`
- **Best quality pass:** `FLUX.1-dev`

### 3) Video generation
- **Main local option:** `LTX-Video`
- **Optional heavy/experimental:** `Wan 2.2`

### 4) Speech and music
- **TTS:** `Piper` (light), `XTTS` (quality)
- **Music:** `MusicGen-small` for reliable local runtime

## Why not only the biggest models?
For laptop workflows, largest models often reduce practical throughput due to:
- VRAM pressure
- thermal throttling
- slow iteration loops

A balanced stack typically gives faster end-to-end project completion.

## Practical defaults for stability
- Image: 1024x1024, steps 20, batch 1
- Video: 720p first pass, 24 fps, short clips (3–5 s)
- Use upscaling/interpolation only on selected final clips

## No-ComfyUI architecture
Use a service approach:
- orchestrator API (FastAPI)
- separate workers for llm/image/video/audio
- queue (Redis + worker)
- unified project metadata (SQLite/Postgres)

This keeps it modular and easier to maintain than manual node graph editing.

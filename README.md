# AI Studio (No ComfyUI) — Laptop RTX 4090 Guide

This repo now includes a practical plan for building a **full local AI Studio** (idea → script → images → video → audio/music) on a laptop RTX 4090 (typically 16 GB VRAM) with 32 GB RAM.

## Is `FLUX.2 + WAN 2.2 + LTX-2 + Audio + Music` a good stack?
Short answer: **good direction**, but for a laptop 4090 you should prioritize **fast + stable** defaults and keep heavier models optional.

### Recommended baseline (best balance for laptop 4090)
- **LLM (idea/script):** `Qwen2.5-7B-Instruct` (or 14B quantized if acceptable speed)
- **Images:** `FLUX.1-schnell` for iteration, optional `FLUX.1-dev` for quality passes
- **Video:** `LTX-Video` as primary local option, `Wan 2.2` as optional heavy profile
- **Speech (TTS):** `Piper` (fast local), optional `XTTS` for better voice
- **Music:** `MusicGen-small` (local), `medium` only if memory allows

> Why this baseline: it fits 16 GB VRAM more reliably, reduces OOM errors, and keeps one-click setup practical.

## One-click setup
Use the installer script:

```bash
bash scripts/one_click_4090.sh
```

What it does:
1. Installs OS packages (`python3-venv`, `ffmpeg`, `git`, `curl`, etc.)
2. Creates `.venv`
3. Installs PyTorch + core inference libraries
4. Installs optional local services (`ollama`, `piper`)
5. Writes a local model profile at `config/models.4090.yaml`

## Files
- `scripts/one_click_4090.sh`: one-click local setup script
- `config/models.4090.yaml`: conservative model presets for 16 GB VRAM
- `docs/model_recommendations.md`: quality/speed recommendations and fallback matrix


## Files to download
If you only want the installer package, download these files:
- `scripts/one_click_4090.sh`
- `config/models.4090.yaml`
- `docs/model_recommendations.md`

Or build one zip bundle from this repo:

```bash
bash scripts/build_download_bundle.sh
```

This creates:
- `dist/ai-studio-4090-bundle.zip`

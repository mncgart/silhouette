# Silhouette: Local Open-Source AI Video Agent (Updated Models)

Got it — you asked for newer model options like **Wan2.2 / LTX** plus better audio/music/image quality on your HP Omen RTX 4090 (16GB VRAM, 32GB RAM).

This update keeps everything local/open-source and adds:
- newer default image + voice presets
- optional AI background music generation
- explicit references to current dedicated video models (Wan2.2, LTX)

## What this pipeline does now

1. Writes scene script with an open-source LLM.
2. Generates scene visuals (high-quality image generation).
3. Generates narration (XTTS v2, optional voice-clone sample).
4. Optionally generates background music (MusicGen).
5. Composes a captioned MP4.

## Best setup: Windows vs WSL2 Linux

Short answer: **WSL2 Ubuntu is usually the best setup for this stack** on your laptop.

### Recommendation
- **Best overall**: **Windows 11 + WSL2 (Ubuntu 22.04/24.04)**
- **Why**:
  - Python AI ecosystem is smoother on Linux environments (fewer package issues).
  - Better compatibility with open-source tooling around diffusers/TTS/video pipelines.
  - Easier shell scripting and dependency management.

### When to use native Windows
Use native Windows only if you specifically need:
- direct integration with Windows-only apps/plugins
- a GUI-only workflow and no terminal comfort

### Practical setup checklist (recommended)
1. Install latest NVIDIA Game Ready/Studio driver on Windows host.
2. Install WSL2 + Ubuntu.
3. In Ubuntu, create venv and install requirements.
4. Install FFmpeg inside WSL2:
   ```bash
   sudo apt update && sudo apt install -y ffmpeg
   ```
5. Validate CUDA visibility from WSL2:
   ```bash
   nvidia-smi
   ```
6. Run with `--preset fast-4090` first, then upgrade to `quality-4090`.

## Default presets (for RTX 4090 laptop)

### `fast-4090` (default)
- Script: `Qwen/Qwen2.5-7B-Instruct`
- Image: `black-forest-labs/FLUX.1-schnell`
- Voice: `tts_models/multilingual/multi-dataset/xtts_v2`
- Music: `facebook/musicgen-small`

### `quality-4090`
- Script: `Qwen/Qwen2.5-7B-Instruct`
- Image: `stabilityai/stable-diffusion-xl-base-1.0`
- Voice: `tts_models/multilingual/multi-dataset/xtts_v2`
- Music: `facebook/musicgen-medium`

## Dedicated video model references (for next upgrade path)

- Wan2.2: `Wan-AI/Wan2.2-T2V-A14B`
- LTX: `Lightricks/LTX-Video`

> Note: this repo currently uses image+audio composition for stability on laptop hardware. You can plug Wan/LTX generation as a next module when you want full text-to-video generation directly.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```bash
python app.py "AI fitness app for busy professionals" --preset fast-4090
```

Quality mode:

```bash
python app.py "AI fitness app for busy professionals" --preset quality-4090
```

Disable background music:

```bash
python app.py "AI fitness app for busy professionals" --no-music
```

Use your own reference voice sample (XTTS voice clone):

```bash
python app.py "AI fitness app for busy professionals" --speaker-wav ./voice_ref.wav
```

Outputs:

```text
outputs/<topic-slug>/
  scenes.json
  images/
  audio/
  music/background.wav
  video/final.mp4
```

## VRAM tips for your laptop

If you get CUDA OOM:
- Lower resolution: `--width 1024 --height 576`
- Reduce scenes: `--scenes 3`
- Use `--preset fast-4090`
- Close Chrome/games/other GPU-heavy apps

## Why this is better for your request

- Uses stronger modern image generation defaults.
- Uses stronger modern voice model (XTTS v2).
- Adds music generation so final output feels closer to ad tools.
- Keeps explicit Wan2.2 / LTX model path for future true video-model rendering.

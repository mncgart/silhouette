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

Windows alternative:

```powershell
.\one_click_4090.ps1
```

Useful flags:

```bash
# Skip apt installs (if dependencies are already installed)
bash scripts/one_click_4090.sh --skip-system

# Skip optional ollama/piper install
bash scripts/one_click_4090.sh --skip-optional

# Dry run (shows planned commands)
bash scripts/one_click_4090.sh --dry-run
```

What it does:
1. Validates minimum requirements (`python3`, optional GPU check with `nvidia-smi`)
2. Installs OS packages (`python3-venv`, `ffmpeg`, `git`, `curl`, etc.) when supported
3. Creates virtual environment
4. Installs PyTorch + core inference libraries from requirements files
5. Optionally installs local services (`ollama`, `piper`)

## Files
- `scripts/one_click_4090.sh`: one-click local setup script
- `config/models.4090.yaml`: conservative model presets for 16 GB VRAM
- `docs/model_recommendations.md`: quality/speed recommendations and fallback matrix
- `docs/upgrade_blueprint.md`: practical roadmap to make your studio stronger
- `requirements/base.txt` and `requirements/cuda121.txt`: reproducible dependency lists

## Files to download
If you only want the installer package, download these files:
- `scripts/one_click_4090.sh`
- `scripts/one_click_4090.ps1`
- `scripts/build_download_bundle.ps1`
- `one_click_4090.ps1`
- `build_download_bundle.ps1`
- `one_click_4090.bat`
- `build_download_bundle.bat`
- `config/models.4090.yaml`
- `docs/model_recommendations.md`
- `requirements/base.txt`
- `requirements/cuda121.txt`

Or build one zip bundle from this repo:

```bash
bash scripts/build_download_bundle.sh
```

This creates:
- `dist/ai-studio-4090-bundle.zip`


## Windows PowerShell quick fix (for your errors)
If you are in `PS C:\...` and saw errors like:
- `Unexpected token ')'`
- `'✅' is not recognized as a cmdlet`
- `...one_click_4090.ps1 is not recognized...`

Use these exact commands in PowerShell (without emoji):

```powershell
# 1) confirm you are in the repo root
Get-Location

# 2) confirm files exist
Get-ChildItem .\scripts

# 3) run installer (script path inside scripts/)
.\scripts\one_click_4090.ps1

# optional flags
.\scripts\one_click_4090.ps1 -SkipSystem -SkipOptional
.\scripts\one_click_4090.ps1 -DryRun

# build downloadable zip
.\scripts\build_download_bundle.ps1
```

Alternative (new root launchers):

```powershell
.\one_click_4090.ps1
.\build_download_bundle.ps1
```

or double-click / run:

```powershell
.\one_click_4090.bat
.\build_download_bundle.bat
```

If `Get-ChildItem .\scripts` does not show `.ps1` files, you downloaded an older or incomplete copy. Re-download the full repo ZIP from GitHub **Code → Download ZIP**.

> Important: `✅` is only a status symbol in docs, not part of a shell command.

## Download on your laptop (step by step)

### Method A — Download ZIP from GitHub (easiest)
1. Open your repo page in browser.
2. Click **Code** → **Download ZIP**.
3. Move ZIP to your laptop (if needed).
4. Extract it.
5. Open terminal in extracted folder.
6. Run:

```bash
bash scripts/one_click_4090.sh
```

Windows alternative:

```powershell
.\one_click_4090.ps1
```

### Method B — Clone with Git (recommended)
1. Open terminal on your laptop.
2. Clone repo:

```bash
git clone <YOUR_REPO_URL>
```

3. Enter repo folder:

```bash
cd silhouette
```

4. Run one-click installer:

```bash
bash scripts/one_click_4090.sh
```

Windows alternative (from repo root):

```powershell
.\one_click_4090.ps1
```

### Method C — Download only the installer bundle file
If `dist/ai-studio-4090-bundle.zip` is already provided in your release/artifacts:
1. Download `ai-studio-4090-bundle.zip`.
2. Extract it.
3. Open terminal in extracted `ai-studio-4090-bundle` folder.
4. Run:

```bash
bash scripts/one_click_4090.sh
```

Windows alternative:

```powershell
.\one_click_4090.ps1
```

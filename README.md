# Silhouette Pro: Local AI Video Agent (RTX 4090 Laptop)

Yes — now it includes a **professional UI** and supports a **best-available model workflow**:
- Better image defaults (`FLUX.1-dev` quality preset)
- Optional image-to-video integration for **WAN 2.2** / **LTX** via command hooks
- XTTS v2 voice + optional MusicGen soundtrack

## What you get

- `app.py` — CLI pipeline
- `ui.py` — professional Gradio UI
- `setup_wsl.sh` — one-command WSL2 setup

## Best setup on your laptop

For HP Omen RTX 4090 16GB + 32GB RAM: use **Windows 11 + WSL2 Ubuntu**.

```bash
bash setup_wsl.sh
```

## Run Professional UI

```bash
source .venv/bin/activate
python ui.py
```

Open:
- `http://localhost:7860`

## Run CLI

```bash
python app.py "AI product ad for students" --preset quality-4090
```

## Model strategy (best now)

### Presets
- `fast-4090`
  - Image: `black-forest-labs/FLUX.1-schnell`
  - I2V: disabled (`none`)
- `quality-4090` (recommended)
  - Image: `black-forest-labs/FLUX.1-dev`
  - I2V backend default: `wan22`
  - I2V model default: `Wan-AI/Wan2.2-I2V-A14B`

### Latest I2V references
- WAN 2.2: `Wan-AI/Wan2.2-I2V-A14B`
- LTX: `Lightricks/LTX-Video`

## Important: WAN/LTX integration

WAN/LTX image-to-video is wired through an external command template so you can connect your preferred runner (ComfyUI, custom script, etc.).

`--i2v-command` supports placeholders:
- `{input}` scene image path
- `{output}` scene video output path
- `{prompt}` scene prompt
- `{model}` selected model id
- `{backend}` selected backend (`wan22` or `ltx`)

Example:

```bash
python app.py "Smart home ad" \
  --preset quality-4090 \
  --i2v-backend wan22 \
  --i2v-model Wan-AI/Wan2.2-I2V-A14B \
  --i2v-command 'python tools/run_i2v.py --backend {backend} --model {model} --input {input} --output {output} --prompt "{prompt}"'
```

## Download files to your laptop

### Option A (recommended): git clone
```bash
git clone <YOUR_REPO_URL>
cd silhouette
```

### Option B: Download ZIP
- GitHub → **Code** → **Download ZIP**
- Extract and open terminal in extracted folder

## VRAM tips

- Start with `--scenes 3`
- Use `1280x720` or `1024x576`
- Close heavy GPU apps before running

## Requirements

Install Python dependencies:

```bash
pip install -r requirements.txt
```

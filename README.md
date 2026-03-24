# silhouette

Deep footage analyzer app that inspects uploaded video and generates:
- **text-to-image prompts**
- **text-to-animation prompts**

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## What it does

1. Samples frames from your footage (configurable interval).
2. Extracts visual metrics per sampled shot:
   - brightness
   - contrast
   - motion level
   - dominant color palette
3. Builds reusable prompts for each shot.

## Notes

- Works with `mp4`, `mov`, `mkv`, `avi`, `webm`.
- It runs locally and does **not** upload your footage anywhere.

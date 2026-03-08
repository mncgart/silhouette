# AI Studio Upgrade Blueprint (No ComfyUI)

This blueprint is for making this project stronger than baseline open-source AI studio demos by focusing on:
- local-first reliability on RTX 4090 laptop (16 GB VRAM)
- better UX flow from idea to final render
- reproducible installs and predictable performance

## 1) Product upgrades to prioritize

1. **Project templates**
   - one-click presets for short ad, music video, cinematic trailer
2. **Shot consistency system**
   - persistent character/style cards used by image + video workers
3. **Timeline-first editing**
   - generated clips always land in timeline with metadata (prompt, seed, model)
4. **One-click regenerate variants**
   - regenerate only selected shot while preserving project context
5. **Thermal-aware generation profiles**
   - Eco / Balanced / Quality modes for laptop thermal and fan constraints

## 2) Architecture upgrades

- API layer: FastAPI orchestration service
- Worker pools by modality: llm, image, video, audio
- Queue: Redis with retries and idempotent job IDs
- Artifact store: local filesystem + metadata DB
- Unified run manifest:
  - input prompt
  - model + version
  - seed
  - inference params
  - output path

This enables deterministic reruns and easier debugging.

## 3) Performance guardrails (RTX 4090 laptop)

- keep default batch size = 1
- use 720p draft passes for video
- set max concurrent GPU jobs = 1 (default)
- schedule optional upscaling only on approved shots
- log VRAM peak per job to detect unstable settings

## 4) Suggested benchmark protocol

Track each release with the same test set (10 prompts):
- text->script latency
- image generation time (1024x1024)
- video generation time (720p, 3-5 sec)
- failure rate (OOM/timeouts)
- user-visible quality score (1-5)

Store results in `docs/benchmarks/YYYY-MM-DD.md`.

## 5) What “better” should mean

A better AI studio is not only model quality. It should improve:
- setup success rate on real laptops
- iteration speed per accepted shot
- reproducibility (same seed, same output family)
- user control (easy overrides without complex graph UI)

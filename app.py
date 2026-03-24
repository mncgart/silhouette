from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
import numpy as np
import streamlit as st


@dataclass
class ShotSummary:
    idx: int
    timestamp: float
    brightness: float
    contrast: float
    motion: float
    palette_hex: List[str]
    frame: np.ndarray


def to_hms(seconds: float) -> str:
    total = max(0, int(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def dominant_palette(frame: np.ndarray, k: int = 5) -> List[str]:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pixels = rgb.reshape((-1, 3)).astype(np.float32)

    # sample to keep app responsive on long videos
    if len(pixels) > 30_000:
        idx = np.random.choice(len(pixels), 30_000, replace=False)
        pixels = pixels[idx]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2)
    _, labels, centers = cv2.kmeans(
        pixels,
        k,
        None,
        criteria,
        8,
        cv2.KMEANS_PP_CENTERS,
    )
    counts = np.bincount(labels.flatten(), minlength=k)
    order = np.argsort(counts)[::-1]

    hex_colors = []
    for i in order:
        c = np.clip(centers[i], 0, 255).astype(int)
        hex_colors.append(f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}")
    return hex_colors


def analyze_video(video_path: Path, sample_every_sec: float, max_samples: int) -> List[ShotSummary]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError("Could not open video file")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    step_frames = max(1, int(sample_every_sec * fps))

    samples: List[ShotSummary] = []
    prev_gray = None
    frame_idx = 0

    while len(samples) < max_samples:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % step_frames != 0:
            frame_idx += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))

        if prev_gray is None:
            motion = 0.0
        else:
            diff = cv2.absdiff(gray, prev_gray)
            motion = float(np.mean(diff))

        prev_gray = gray
        timestamp = frame_idx / fps

        palette = dominant_palette(frame)
        samples.append(
            ShotSummary(
                idx=len(samples) + 1,
                timestamp=timestamp,
                brightness=brightness,
                contrast=contrast,
                motion=motion,
                palette_hex=palette,
                frame=frame,
            )
        )

        frame_idx += 1

    cap.release()
    return samples


def style_from_metrics(brightness: float, contrast: float, motion: float) -> str:
    mood = "moody" if brightness < 90 else "balanced" if brightness < 160 else "high-key"
    texture = "gritty" if contrast > 65 else "soft"
    movement = "dynamic movement" if motion > 22 else "steady composition"
    return f"{mood}, {texture}, {movement}"


def build_text_to_image_prompt(summary: ShotSummary, overall_theme: str, subject: str) -> str:
    style = style_from_metrics(summary.brightness, summary.contrast, summary.motion)
    palette_text = ", ".join(summary.palette_hex[:4])
    return (
        f"{subject}, cinematic still frame, {overall_theme}. "
        f"Visual style: {style}. "
        f"Color palette: {palette_text}. "
        f"Highly detailed, 35mm film look, volumetric lighting, composition focused on storytelling."
    )


def build_text_to_animation_prompt(summary: ShotSummary, overall_theme: str, subject: str) -> str:
    speed = "slow and emotional" if summary.motion < 12 else "medium pace" if summary.motion < 25 else "fast and energetic"
    palette_text = ", ".join(summary.palette_hex[:5])
    return (
        f"Create a {speed} animated sequence of {subject}. Theme: {overall_theme}. "
        f"Scene time marker from source footage: {to_hms(summary.timestamp)}. "
        f"Use this color script: {palette_text}. "
        "Include camera motion, foreground/background parallax, character micro-expressions, environmental particles, "
        "and smooth transitions between key poses. Output as high-detail stylized cinematic animation."
    )


def frame_to_rgb(frame: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def main() -> None:
    st.set_page_config(page_title="Silhouette Deep Footage Analyzer", layout="wide")
    st.title("🎬 Deep Footage Analyzer → Prompt Generator")
    st.write(
        "Upload video footage to auto-analyze visual style and generate **text-to-image** + "
        "**text-to-animation** prompts you can use in AI tools."
    )

    with st.sidebar:
        st.header("Settings")
        subject = st.text_input("Main subject", value="a lone traveler")
        theme = st.text_input("Theme", value="neo-noir city at dusk")
        sample_every = st.slider("Sample every N seconds", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
        max_samples = st.slider("Max sampled shots", min_value=3, max_value=30, value=10)

    uploaded = st.file_uploader("Upload footage", type=["mp4", "mov", "mkv", "avi", "webm"])
    if not uploaded:
        st.info("Upload a video file to start analysis.")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as temp:
        temp.write(uploaded.getbuffer())
        temp_path = Path(temp.name)

    with st.spinner("Analyzing footage…"):
        summaries = analyze_video(temp_path, sample_every_sec=sample_every, max_samples=max_samples)

    if not summaries:
        st.error("No frames could be analyzed from the uploaded file.")
        return

    avg_brightness = np.mean([s.brightness for s in summaries])
    avg_contrast = np.mean([s.contrast for s in summaries])
    avg_motion = np.mean([s.motion for s in summaries])

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Brightness", f"{avg_brightness:.1f}")
    c2.metric("Avg Contrast", f"{avg_contrast:.1f}")
    c3.metric("Avg Motion", f"{avg_motion:.1f}")

    st.subheader("Shot Breakdown & Prompts")
    for s in summaries:
        with st.expander(f"Shot {s.idx} — {to_hms(s.timestamp)}"):
            st.image(frame_to_rgb(s.frame), caption=f"Shot {s.idx}", use_container_width=True)
            st.write(
                f"Brightness: **{s.brightness:.1f}** · Contrast: **{s.contrast:.1f}** · Motion: **{s.motion:.1f}**"
            )
            st.write("Palette:", " ".join([f"`{color}`" for color in s.palette_hex[:5]]))

            image_prompt = build_text_to_image_prompt(s, overall_theme=theme, subject=subject)
            anim_prompt = build_text_to_animation_prompt(s, overall_theme=theme, subject=subject)

            st.markdown("**Text-to-Image Prompt**")
            st.code(image_prompt, language="text")
            st.markdown("**Text-to-Animation Prompt**")
            st.code(anim_prompt, language="text")


if __name__ == "__main__":
    main()

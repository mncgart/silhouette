from __future__ import annotations

import argparse
import json
import re
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import torch
from PIL import Image, ImageDraw, ImageFont
from rich import print


MODEL_PRESETS = {
    "fast-4090": {
        "script_model": "Qwen/Qwen2.5-7B-Instruct",
        "image_model": "black-forest-labs/FLUX.1-schnell",
        "tts_model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "music_model": "facebook/musicgen-small",
        "i2v_backend": "none",
        "i2v_model": "",
    },
    "quality-4090": {
        "script_model": "Qwen/Qwen2.5-7B-Instruct",
        "image_model": "black-forest-labs/FLUX.1-dev",
        "tts_model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "music_model": "facebook/musicgen-medium",
        "i2v_backend": "wan22",
        "i2v_model": "Wan-AI/Wan2.2-I2V-A14B",
    },
}

LATEST_VIDEO_REFERENCES = {
    "wan22_i2v": "Wan-AI/Wan2.2-I2V-A14B",
    "ltx_i2v": "Lightricks/LTX-Video",
}


@dataclass
class Scene:
    title: str
    visual_prompt: str
    voiceover: str


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "video"


def ensure_dirs(out_dir: Path) -> dict[str, Path]:
    paths = {
        "root": out_dir,
        "images": out_dir / "images",
        "scene_videos": out_dir / "scene_videos",
        "audio": out_dir / "audio",
        "music": out_dir / "music",
        "video": out_dir / "video",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def load_script_with_llm(topic: str, n_scenes: int, model_id: str) -> List[Scene]:
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")

    prompt = textwrap.dedent(
        f"""
        Create exactly {n_scenes} scenes for a short marketing video.
        Topic: {topic}
        Return valid JSON:
        {{"scenes":[{{"title":"...","visual_prompt":"...","voiceover":"..."}}]}}
        Keep each voiceover 15-25 words.
        """
    ).strip()

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    output_ids = model.generate(**inputs, max_new_tokens=650, temperature=0.7, do_sample=True, pad_token_id=tokenizer.eos_token_id)
    raw = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    json_start = raw.find("{")
    json_end = raw.rfind("}")
    if json_start == -1 or json_end == -1:
        raise ValueError("Could not parse JSON from model output")

    payload = json.loads(raw[json_start : json_end + 1])
    scenes = [Scene(**item) for item in payload.get("scenes", [])][:n_scenes]
    if len(scenes) != n_scenes:
        raise ValueError("LLM returned wrong number of scenes")
    return scenes


def generate_scene_images(scenes: List[Scene], out_dir: Path, image_model_id: str, width: int, height: int) -> List[Path]:
    from diffusers import AutoPipelineForText2Image

    pipe = AutoPipelineForText2Image.from_pretrained(image_model_id, torch_dtype=torch.float16, use_safetensors=True).to("cuda")
    image_paths: List[Path] = []

    for i, scene in enumerate(scenes, start=1):
        result = pipe(prompt=scene.visual_prompt, width=width, height=height, guidance_scale=4.0, num_inference_steps=22)
        img: Image.Image = result.images[0]
        img_path = out_dir / f"scene_{i:02d}.png"
        img.save(img_path)
        image_paths.append(img_path)
        print(f"[green]Generated image[/green] {img_path.name}")

    return image_paths


def generate_scene_videos(
    scenes: List[Scene],
    image_paths: List[Path],
    out_dir: Path,
    i2v_backend: str,
    i2v_model: str,
    i2v_command: Optional[str],
) -> List[Path]:
    """Generate short scene videos from images using external WAN/LTX command hooks."""
    if i2v_backend == "none":
        return []

    if not i2v_command:
        raise ValueError("i2v backend selected but --i2v-command is not provided")

    scene_videos: List[Path] = []
    for i, (scene, image_path) in enumerate(zip(scenes, image_paths), start=1):
        out_path = out_dir / f"scene_{i:02d}.mp4"
        cmd = i2v_command.format(
            input=image_path,
            output=out_path,
            prompt=scene.visual_prompt.replace('"', "'"),
            model=i2v_model,
            backend=i2v_backend,
        )
        print(f"[cyan]I2V command[/cyan]: {cmd}")
        completed = subprocess.run(cmd, shell=True)
        if completed.returncode != 0 or not out_path.exists():
            raise RuntimeError(f"I2V generation failed for scene {i}. Check command/output path.")
        scene_videos.append(out_path)

    return scene_videos


def synthesize_voiceovers(scenes: List[Scene], out_dir: Path, tts_model_id: str, speaker_wav: Optional[Path] = None) -> List[Path]:
    from TTS.api import TTS

    tts = TTS(model_name=tts_model_id, progress_bar=False)
    audio_paths: List[Path] = []

    for i, scene in enumerate(scenes, start=1):
        wav_path = out_dir / f"scene_{i:02d}.wav"
        kwargs = {"text": scene.voiceover, "file_path": str(wav_path)}
        if speaker_wav and speaker_wav.exists():
            kwargs["speaker_wav"] = str(speaker_wav)
            kwargs["language"] = "en"
        tts.tts_to_file(**kwargs)
        audio_paths.append(wav_path)

    return audio_paths


def synthesize_music(prompt: str, out_path: Path, model_id: str, duration_sec: int = 20) -> Optional[Path]:
    try:
        import scipy.io.wavfile as wavfile
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
    except Exception:
        print("[yellow]Music dependencies missing, skipping music track.[/yellow]")
        return None

    processor = AutoProcessor.from_pretrained(model_id)
    model = MusicgenForConditionalGeneration.from_pretrained(model_id).to("cuda")

    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(model.device)
    sampling_rate = model.config.audio_encoder.sampling_rate
    max_tokens = max(64, int(duration_sec * 50))
    audio_values = model.generate(**inputs, max_new_tokens=max_tokens)
    audio = (audio_values[0, 0].detach().cpu().numpy() * 32767).astype("int16")
    wavfile.write(out_path, rate=sampling_rate, data=audio)
    return out_path


def add_caption(image: Image.Image, caption: str) -> Image.Image:
    img = image.copy().convert("RGB")
    font = ImageFont.load_default()
    wrapped = textwrap.fill(caption, width=45)
    margin, box_height = 24, 100

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((margin, img.height - box_height - margin, img.width - margin, img.height - margin), fill=(0, 0, 0, 175))

    out = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(out)
    draw.multiline_text((margin + 12, img.height - box_height + 10), wrapped, fill="white", font=font)
    return out.convert("RGB")


def compose_video(
    image_paths: List[Path],
    audio_paths: List[Path],
    scenes: List[Scene],
    out_path: Path,
    music_path: Optional[Path],
    scene_video_paths: Optional[List[Path]] = None,
    fps: int = 24,
) -> Path:
    from moviepy.editor import AudioFileClip, CompositeAudioClip, ImageClip, VideoFileClip, concatenate_videoclips

    clips = []
    temp_frames = out_path.parent / "caption_frames"
    temp_frames.mkdir(parents=True, exist_ok=True)

    for i, (img_path, audio_path, scene) in enumerate(zip(image_paths, audio_paths, scenes), start=1):
        narration = AudioFileClip(str(audio_path))

        if scene_video_paths and len(scene_video_paths) >= i:
            clip = VideoFileClip(str(scene_video_paths[i - 1])).subclip(0, narration.duration)
        else:
            frame = add_caption(Image.open(img_path), scene.voiceover)
            captioned_path = temp_frames / f"scene_{i:02d}.png"
            frame.save(captioned_path)
            clip = ImageClip(str(captioned_path)).set_duration(narration.duration).fadein(0.2).fadeout(0.2)

        if music_path and music_path.exists():
            bg = AudioFileClip(str(music_path)).volumex(0.15).subclip(0, narration.duration)
            clip = clip.set_audio(CompositeAudioClip([bg, narration]))
        else:
            clip = clip.set_audio(narration)

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(str(out_path), fps=fps, codec="libx264", audio_codec="aac")
    return out_path


def build_video(args: argparse.Namespace) -> Path:
    project_dir = args.out / slugify(args.topic)
    paths = ensure_dirs(project_dir)

    scenes = load_script_with_llm(args.topic, n_scenes=args.scenes, model_id=args.script_model)
    with open(paths["root"] / "scenes.json", "w", encoding="utf-8") as f:
        json.dump([s.__dict__ for s in scenes], f, indent=2)

    images = generate_scene_images(scenes, paths["images"], image_model_id=args.image_model, width=args.width, height=args.height)
    scene_videos = generate_scene_videos(
        scenes,
        images,
        paths["scene_videos"],
        i2v_backend=args.i2v_backend,
        i2v_model=args.i2v_model,
        i2v_command=args.i2v_command,
    )
    voice = synthesize_voiceovers(scenes, paths["audio"], tts_model_id=args.tts_model, speaker_wav=args.speaker_wav)

    music = None
    if not args.no_music:
        music = synthesize_music(args.music_prompt, paths["music"] / "background.wav", model_id=args.music_model)

    return compose_video(images, voice, scenes, paths["video"] / "final.mp4", music_path=music, scene_video_paths=scene_videos)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local open-source AI video agent")
    parser.add_argument("topic", type=str)
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    parser.add_argument("--scenes", type=int, default=4)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--preset", choices=list(MODEL_PRESETS.keys()), default="quality-4090")

    parser.add_argument("--script-model", type=str, default=None)
    parser.add_argument("--image-model", type=str, default=None)
    parser.add_argument("--tts-model", type=str, default=None)
    parser.add_argument("--music-model", type=str, default=None)

    parser.add_argument("--i2v-backend", choices=["none", "wan22", "ltx"], default=None)
    parser.add_argument("--i2v-model", type=str, default=None)
    parser.add_argument("--i2v-command", type=str, default=None, help="Shell template with {input} {output} {prompt} {model} {backend}")

    parser.add_argument("--music-prompt", type=str, default="upbeat modern product ad music, clean electronic, no vocals")
    parser.add_argument("--speaker-wav", type=Path, default=None)
    parser.add_argument("--no-music", action="store_true")
    return parser.parse_args()


def resolve_models(args: argparse.Namespace) -> argparse.Namespace:
    preset = MODEL_PRESETS[args.preset]
    args.script_model = args.script_model or preset["script_model"]
    args.image_model = args.image_model or preset["image_model"]
    args.tts_model = args.tts_model or preset["tts_model"]
    args.music_model = args.music_model or preset["music_model"]
    args.i2v_backend = args.i2v_backend or preset["i2v_backend"]
    args.i2v_model = args.i2v_model or preset["i2v_model"]
    return args


def check_device() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required")
    props = torch.cuda.get_device_properties(0)
    print(f"[bold]GPU:[/bold] {props.name} | VRAM ~ {props.total_memory / (1024**3):.1f} GB")


def main() -> None:
    args = parse_args()
    check_device()
    args = resolve_models(args)

    print(f"[cyan]Preset:[/cyan] {args.preset}")
    print(f"[cyan]Models:[/cyan] script={args.script_model} image={args.image_model} tts={args.tts_model} music={args.music_model}")
    print(f"[cyan]I2V:[/cyan] backend={args.i2v_backend} model={args.i2v_model}")
    print(f"[cyan]Latest I2V refs:[/cyan] {LATEST_VIDEO_REFERENCES}")

    output = build_video(args)
    print(f"\n[bold green]Done.[/bold green] Video saved at: {output}")


if __name__ == "__main__":
    main()

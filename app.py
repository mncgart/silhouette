from __future__ import annotations

import argparse
import json
import re
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
    },
    "quality-4090": {
        "script_model": "Qwen/Qwen2.5-7B-Instruct",
        "image_model": "stabilityai/stable-diffusion-xl-base-1.0",
        "tts_model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "music_model": "facebook/musicgen-medium",
    },
}

LATEST_VIDEO_REFERENCES = {
    "wan22": "Wan-AI/Wan2.2-T2V-A14B",
    "ltx": "Lightricks/LTX-Video",
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
        result = pipe(prompt=scene.visual_prompt, width=width, height=height, guidance_scale=4.0, num_inference_steps=20)
        img: Image.Image = result.images[0]
        img_path = out_dir / f"scene_{i:02d}.png"
        img.save(img_path)
        image_paths.append(img_path)
        print(f"[green]Generated image[/green] {img_path.name}")

    return image_paths


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
        print(f"[green]Generated voiceover[/green] {wav_path.name}")

    return audio_paths


def synthesize_music(prompt: str, out_path: Path, model_id: str, duration_sec: int = 20) -> Optional[Path]:
    try:
        import scipy.io.wavfile as wavfile
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
    except Exception:
        print("[yellow]Music generation dependencies unavailable, skipping music track.[/yellow]")
        return None

    processor = AutoProcessor.from_pretrained(model_id)
    model = MusicgenForConditionalGeneration.from_pretrained(model_id).to("cuda")

    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(model.device)
    sampling_rate = model.config.audio_encoder.sampling_rate
    max_tokens = max(64, int(duration_sec * 50))
    audio_values = model.generate(**inputs, max_new_tokens=max_tokens)
    audio = audio_values[0, 0].detach().cpu().numpy()
    audio = (audio * 32767).astype("int16")
    wavfile.write(out_path, rate=sampling_rate, data=audio)
    print(f"[green]Generated music[/green] {out_path.name}")
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


def compose_video(image_paths: List[Path], audio_paths: List[Path], scenes: List[Scene], out_path: Path, music_path: Optional[Path], fps: int = 24) -> Path:
    from moviepy.editor import AudioFileClip, CompositeAudioClip, ImageClip, concatenate_videoclips

    clips = []
    temp_frames = out_path.parent / "caption_frames"
    temp_frames.mkdir(parents=True, exist_ok=True)

    for i, (img_path, audio_path, scene) in enumerate(zip(image_paths, audio_paths, scenes), start=1):
        narration = AudioFileClip(str(audio_path))
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


def build_video(topic: str, out_root: Path, n_scenes: int, width: int, height: int, script_model: str, image_model: str, tts_model: str, music_model: str, music_prompt: Optional[str], speaker_wav: Optional[Path]) -> Path:
    project_dir = out_root / slugify(topic)
    paths = ensure_dirs(project_dir)

    scenes = load_script_with_llm(topic, n_scenes=n_scenes, model_id=script_model)
    with open(paths["root"] / "scenes.json", "w", encoding="utf-8") as f:
        json.dump([s.__dict__ for s in scenes], f, indent=2)

    images = generate_scene_images(scenes, paths["images"], image_model_id=image_model, width=width, height=height)
    voice = synthesize_voiceovers(scenes, paths["audio"], tts_model_id=tts_model, speaker_wav=speaker_wav)
    music = None
    if music_prompt:
        music = synthesize_music(music_prompt, paths["music"] / "background.wav", model_id=music_model)

    return compose_video(images, voice, scenes, paths["video"] / "final.mp4", music_path=music)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local open-source AI video agent")
    parser.add_argument("topic", type=str)
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    parser.add_argument("--scenes", type=int, default=4)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--preset", choices=list(MODEL_PRESETS.keys()), default="fast-4090")
    parser.add_argument("--script-model", type=str, default=None)
    parser.add_argument("--image-model", type=str, default=None)
    parser.add_argument("--tts-model", type=str, default=None)
    parser.add_argument("--music-model", type=str, default=None)
    parser.add_argument("--music-prompt", type=str, default="upbeat modern product ad music, clean electronic, no vocals")
    parser.add_argument("--speaker-wav", type=Path, default=None, help="Optional voice clone sample for XTTS")
    parser.add_argument("--no-music", action="store_true")
    return parser.parse_args()


def resolve_models(args: argparse.Namespace) -> dict[str, str]:
    preset = MODEL_PRESETS[args.preset]
    return {
        "script_model": args.script_model or preset["script_model"],
        "image_model": args.image_model or preset["image_model"],
        "tts_model": args.tts_model or preset["tts_model"],
        "music_model": args.music_model or preset["music_model"],
    }


def check_device() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for this workflow")
    props = torch.cuda.get_device_properties(0)
    print(f"[bold]GPU:[/bold] {props.name} | VRAM ~ {props.total_memory / (1024**3):.1f} GB")


def main() -> None:
    args = parse_args()
    check_device()
    models = resolve_models(args)

    print(f"[cyan]Preset:[/cyan] {args.preset}")
    print(f"[cyan]Scene+Voice pipeline models:[/cyan] {models}")
    print(f"[cyan]Latest dedicated video model references:[/cyan] {LATEST_VIDEO_REFERENCES}")

    music_prompt = None if args.no_music else args.music_prompt
    out = build_video(
        topic=args.topic,
        out_root=args.out,
        n_scenes=args.scenes,
        width=args.width,
        height=args.height,
        script_model=models["script_model"],
        image_model=models["image_model"],
        tts_model=models["tts_model"],
        music_model=models["music_model"],
        music_prompt=music_prompt,
        speaker_wav=args.speaker_wav,
    )
    print(f"\n[bold green]Done.[/bold green] Video saved at: {out}")


if __name__ == "__main__":
    main()

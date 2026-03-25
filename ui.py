from __future__ import annotations

import traceback
from pathlib import Path

import gradio as gr

from app import MODEL_PRESETS, build_video, resolve_models, check_device


def run_generation(
    topic: str,
    preset: str,
    scenes: int,
    width: int,
    height: int,
    script_model: str,
    image_model: str,
    tts_model: str,
    music_model: str,
    i2v_backend: str,
    i2v_model: str,
    i2v_command: str,
    music_prompt: str,
    no_music: bool,
):
    try:
        check_device()

        class Args:
            pass

        args = Args()
        args.topic = topic
        args.out = Path("outputs")
        args.preset = preset
        args.scenes = scenes
        args.width = width
        args.height = height

        args.script_model = script_model.strip() or None
        args.image_model = image_model.strip() or None
        args.tts_model = tts_model.strip() or None
        args.music_model = music_model.strip() or None

        args.i2v_backend = i2v_backend
        args.i2v_model = i2v_model.strip() or None
        args.i2v_command = i2v_command.strip() or None

        args.music_prompt = music_prompt
        args.speaker_wav = None
        args.no_music = no_music

        args = resolve_models(args)
        output = build_video(args)
        return str(output), "✅ Completed"
    except Exception as exc:
        return "", f"❌ Failed: {exc}\n\n{traceback.format_exc()}"


def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(), title="Silhouette Pro UI") as demo:
        gr.Markdown("# 🎬 Silhouette Pro UI\nGenerate ad-style videos locally with open-source models.")

        with gr.Row():
            topic = gr.Textbox(label="Topic", value="AI fitness app for busy professionals")
            preset = gr.Dropdown(choices=list(MODEL_PRESETS.keys()), value="quality-4090", label="Preset")

        with gr.Row():
            scenes = gr.Slider(minimum=2, maximum=8, step=1, value=4, label="Scenes")
            width = gr.Dropdown(choices=[1024, 1280, 1366], value=1280, label="Width")
            height = gr.Dropdown(choices=[576, 720, 768], value=720, label="Height")

        gr.Markdown("## Models")
        with gr.Row():
            script_model = gr.Textbox(label="Script LLM", value="")
            image_model = gr.Textbox(label="Image Model (FLUX.1-dev recommended)", value="")

        with gr.Row():
            tts_model = gr.Textbox(label="Voice Model", value="")
            music_model = gr.Textbox(label="Music Model", value="")

        gr.Markdown("## Image-to-Video (WAN 2.2 / LTX via external runner)")
        with gr.Row():
            i2v_backend = gr.Dropdown(choices=["none", "wan22", "ltx"], value="wan22", label="I2V Backend")
            i2v_model = gr.Textbox(label="I2V Model", value="Wan-AI/Wan2.2-I2V-A14B")

        i2v_command = gr.Textbox(
            label="I2V Command Template",
            lines=3,
            value="",
            placeholder="example: python tools/run_i2v.py --backend {backend} --model {model} --input {input} --output {output} --prompt \"{prompt}\"",
        )

        with gr.Row():
            music_prompt = gr.Textbox(label="Music Prompt", value="upbeat modern product ad music, clean electronic, no vocals")
            no_music = gr.Checkbox(label="Disable Music", value=False)

        run_btn = gr.Button("Generate Video", variant="primary")
        output_video_path = gr.Textbox(label="Output Video Path")
        status = gr.Textbox(label="Status", lines=6)

        run_btn.click(
            fn=run_generation,
            inputs=[
                topic,
                preset,
                scenes,
                width,
                height,
                script_model,
                image_model,
                tts_model,
                music_model,
                i2v_backend,
                i2v_model,
                i2v_command,
                music_prompt,
                no_music,
            ],
            outputs=[output_video_path, status],
        )

    return demo


if __name__ == "__main__":
    build_ui().launch(server_name="0.0.0.0", server_port=7860)
